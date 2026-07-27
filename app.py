import os
import re
import tempfile
from pathlib import Path

import streamlit as st
import yt_dlp
from yt_dlp.utils import download_range_func


st.set_page_config(
    page_title="Descargador Pro",
    page_icon="📥",
    layout="centered",
)

st.title("📥 Descargador Pro")
st.caption(
    "Descarga videos completos o fragmentos en MP4 y MP3. "
    "Utiliza únicamente contenido propio o autorizado."
)


# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------

def segundos_a_tiempo(segundos: int | float | None) -> str:
    """Convierte segundos a HH:MM:SS o MM:SS."""
    if segundos is None:
        return "Desconocida"

    segundos = int(segundos)
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)

    if horas:
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    return f"{minutos:02d}:{segundos:02d}"


def tiempo_a_segundos(valor: str) -> int:
    """
    Convierte:
    90       -> 90 segundos
    01:30    -> 90 segundos
    1:02:30  -> 3750 segundos
    """
    valor = valor.strip()

    if not valor:
        raise ValueError("El tiempo está vacío.")

    if re.fullmatch(r"\d+", valor):
        return int(valor)

    partes = valor.split(":")

    if len(partes) == 2:
        minutos, segundos = partes

        if not minutos.isdigit() or not segundos.isdigit():
            raise ValueError("Usa el formato MM:SS.")

        minutos = int(minutos)
        segundos = int(segundos)

        if segundos >= 60:
            raise ValueError("Los segundos deben ser menores de 60.")

        return minutos * 60 + segundos

    if len(partes) == 3:
        horas, minutos, segundos = partes

        if not all(parte.isdigit() for parte in partes):
            raise ValueError("Usa el formato HH:MM:SS.")

        horas = int(horas)
        minutos = int(minutos)
        segundos = int(segundos)

        if minutos >= 60 or segundos >= 60:
            raise ValueError(
                "Los minutos y segundos deben ser menores de 60."
            )

        return horas * 3600 + minutos * 60 + segundos

    raise ValueError(
        "Formato incorrecto. Ejemplos válidos: 01:30 o 1:02:30."
    )


def nombre_seguro(nombre: str) -> str:
    """Limpia el nombre que recibirá el usuario."""
    nombre = re.sub(r'[<>:"/\\|?*]', "", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre[:150] or "archivo"


def opciones_comunes() -> dict:
    """Configuración común para analizar y descargar."""
    opciones = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "source_address": "0.0.0.0",
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 4,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    }

    cookie_path = Path("cookies.txt")

    if cookie_path.is_file():
        opciones["cookiefile"] = str(cookie_path)

    return opciones


def analizar_video(enlace: str) -> dict:
    """Obtiene información sin descargar el archivo."""
    opciones = opciones_comunes()
    opciones["skip_download"] = True

    with yt_dlp.YoutubeDL(opciones) as ydl:
        informacion = ydl.extract_info(enlace, download=False)
        return ydl.sanitize_info(informacion)


def selector_mp4(calidad: str) -> str:
    """Construye el selector de formatos para MP4."""
    alturas = {
        "Máxima disponible": None,
        "1080p": 1080,
        "720p": 720,
        "480p": 480,
        "360p": 360,
    }

    altura = alturas[calidad]

    if altura is None:
        return (
            "bv[ext=mp4]+ba[ext=m4a]/"
            "b[ext=mp4]/"
            "bv+ba/b"
        )

    return (
        f"bv[height<={altura}][ext=mp4]+ba[ext=m4a]/"
        f"b[height<={altura}][ext=mp4]/"
        f"bv[height<={altura}]+ba/"
        f"b[height<={altura}]/best"
    )


def encontrar_archivo(
    directorio: Path,
    extension: str,
) -> Path:
    """Encuentra el archivo final generado por yt-dlp y FFmpeg."""
    archivos = list(directorio.glob(f"*.{extension}"))

    if not archivos:
        archivos = [
            archivo
            for archivo in directorio.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower() not in {
                ".part",
                ".ytdl",
                ".temp",
                ".jpg",
                ".jpeg",
                ".png",
                ".webp",
            }
        ]

    if not archivos:
        raise FileNotFoundError(
            "La descarga terminó, pero no se encontró el archivo final."
        )

    return max(
        archivos,
        key=lambda archivo: archivo.stat().st_mtime,
    )


def descargar_archivo(
    enlace: str,
    formato_salida: str,
    calidad: str,
    bitrate: str,
    inicio: int | None,
    final: int | None,
    titulo: str,
) -> tuple[bytes, str, str]:
    """Descarga el contenido y devuelve bytes, nombre y MIME."""

    with tempfile.TemporaryDirectory() as carpeta_temporal:
        directorio = Path(carpeta_temporal)

        opciones = opciones_comunes()
        opciones.update(
            {
                "outtmpl": str(directorio / "descarga.%(ext)s"),
                "overwrites": True,
            }
        )

        if inicio is not None and final is not None:
            opciones["download_ranges"] = download_range_func(
                [],
                [(inicio, final)],
            )

            # Produce cortes más exactos, aunque consume más procesador.
            opciones["force_keyframes_at_cuts"] = True

        if formato_salida == "MP4":
            extension = "mp4"
            mime = "video/mp4"

            opciones.update(
                {
                    "format": selector_mp4(calidad),
                    "merge_output_format": "mp4",
                    "postprocessors": [
                        {
                            "key": "FFmpegVideoConvertor",
                            "preferedformat": "mp4",
                        }
                    ],
                }
            )

        else:
            extension = "mp3"
            mime = "audio/mpeg"

            bitrate_numero = bitrate.replace(" kbps", "")

            opciones.update(
                {
                    "format": "bestaudio/best",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": bitrate_numero,
                        }
                    ],
                }
            )

        barra = st.progress(0)
        estado = st.empty()

        def progreso(datos: dict) -> None:
            if datos.get("status") == "downloading":
                descargado = datos.get("downloaded_bytes", 0)
                total = (
                    datos.get("total_bytes")
                    or datos.get("total_bytes_estimate")
                )

                if total:
                    porcentaje = min(descargado / total, 1.0)
                    barra.progress(porcentaje)
                    estado.caption(
                        f"Descargando: {porcentaje * 100:.1f}%"
                    )
                else:
                    estado.caption("Descargando contenido...")

            elif datos.get("status") == "finished":
                barra.progress(1.0)
                estado.caption(
                    "Descarga terminada. Procesando archivo..."
                )

        opciones["progress_hooks"] = [progreso]

        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([enlace])

        archivo_final = encontrar_archivo(
            directorio,
            extension,
        )

        contenido = archivo_final.read_bytes()
        titulo_limpio = nombre_seguro(titulo)

        if inicio is not None and final is not None:
            nombre_final = (
                f"{titulo_limpio}_"
                f"{segundos_a_tiempo(inicio).replace(':', '-')}_"
                f"{segundos_a_tiempo(final).replace(':', '-')}"
                f".{extension}"
            )
        else:
            nombre_final = f"{titulo_limpio}.{extension}"

        estado.empty()
        barra.empty()

        return contenido, nombre_final, mime


# ---------------------------------------------------------
# ESTADO DE LA APLICACIÓN
# ---------------------------------------------------------

if "informacion_video" not in st.session_state:
    st.session_state.informacion_video = None

if "url_analizada" not in st.session_state:
    st.session_state.url_analizada = ""

if "archivo_preparado" not in st.session_state:
    st.session_state.archivo_preparado = None


# ---------------------------------------------------------
# INTERFAZ
# ---------------------------------------------------------

url = st.text_input(
    "Pega el enlace:",
    placeholder="https://...",
)

if st.button(
    "🔎 Analizar video",
    type="primary",
    use_container_width=True,
):
    if not url.strip():
        st.warning("Primero pega un enlace.")

    elif not url.startswith(("https://", "http://")):
        st.error("El enlace debe comenzar con http:// o https://.")

    else:
        try:
            with st.spinner("Analizando enlace..."):
                informacion = analizar_video(url.strip())

            st.session_state.informacion_video = informacion
            st.session_state.url_analizada = url.strip()
            st.session_state.archivo_preparado = None

        except yt_dlp.utils.DownloadError as error:
            st.error("No fue posible analizar el enlace.")
            st.code(str(error)[-1000:], language=None)

        except Exception as error:
            st.error(f"Error técnico: {error}")


informacion = st.session_state.informacion_video

if informacion and st.session_state.url_analizada == url.strip():
    titulo = informacion.get("title") or "Video"
    duracion = informacion.get("duration")
    thumbnail = informacion.get("thumbnail")
    autor = (
        informacion.get("uploader")
        or informacion.get("channel")
        or "Desconocido"
    )

    st.divider()
    st.subheader(titulo)

    if thumbnail:
        st.image(thumbnail, use_container_width=True)

    columna_1, columna_2 = st.columns(2)

    with columna_1:
        st.metric(
            "Duración",
            segundos_a_tiempo(duracion),
        )

    with columna_2:
        st.metric(
            "Autor o canal",
            str(autor)[:30],
        )

    formato_salida = st.radio(
        "Formato de descarga:",
        ["MP4", "MP3"],
        horizontal=True,
    )

    if formato_salida == "MP4":
        calidad = st.selectbox(
            "Calidad del video:",
            [
                "Máxima disponible",
                "1080p",
                "720p",
                "480p",
                "360p",
            ],
            index=2,
        )

        bitrate = "192 kbps"

    else:
        bitrate = st.selectbox(
            "Calidad del audio:",
            [
                "320 kbps",
                "256 kbps",
                "192 kbps",
                "128 kbps",
            ],
            index=2,
        )

        calidad = "Solo audio"

    tipo_descarga = st.radio(
        "¿Qué parte deseas descargar?",
        [
            "Video completo",
            "Seleccionar fragmento",
        ],
    )

    inicio_segundos = None
    final_segundos = None
    tiempos_validos = True

    if tipo_descarga == "Seleccionar fragmento":
        st.info(
            "Indica el punto inicial y final. "
            "Ejemplo: 01:30 hasta 03:45."
        )

        columna_inicio, columna_final = st.columns(2)

        with columna_inicio:
            tiempo_inicio = st.text_input(
                "Comenzar en:",
                value="00:00",
                placeholder="MM:SS",
            )

        with columna_final:
            tiempo_final = st.text_input(
                "Terminar en:",
                value=segundos_a_tiempo(duracion)
                if duracion
                else "01:00",
                placeholder="MM:SS",
            )

        try:
            inicio_segundos = tiempo_a_segundos(tiempo_inicio)
            final_segundos = tiempo_a_segundos(tiempo_final)

            if final_segundos <= inicio_segundos:
                st.error(
                    "El tiempo final debe ser mayor que el inicial."
                )
                tiempos_validos = False

            elif duracion and final_segundos > duracion:
                st.error(
                    "El tiempo final supera la duración del video."
                )
                tiempos_validos = False

            else:
                duracion_fragmento = final_segundos - inicio_segundos

                st.success(
                    "Fragmento seleccionado: "
                    f"{segundos_a_tiempo(duracion_fragmento)}"
                )

        except ValueError as error:
            st.error(str(error))
            tiempos_validos = False

    preparar = st.button(
        f"⚙️ Preparar descarga en {formato_salida}",
        type="primary",
        use_container_width=True,
        disabled=not tiempos_validos,
    )

    if preparar:
        try:
            st.session_state.archivo_preparado = None

            with st.spinner(
                "Descargando y procesando el archivo..."
            ):
                datos, nombre, mime = descargar_archivo(
                    enlace=url.strip(),
                    formato_salida=formato_salida,
                    calidad=calidad,
                    bitrate=bitrate,
                    inicio=inicio_segundos,
                    final=final_segundos,
                    titulo=titulo,
                )

            st.session_state.archivo_preparado = {
                "datos": datos,
                "nombre": nombre,
                "mime": mime,
                "formato": formato_salida,
            }

        except yt_dlp.utils.DownloadError as error:
            st.error("No fue posible descargar el contenido.")
            st.code(str(error)[-1200:], language=None)

            st.info(
                "Revisa que el enlace sea público, que FFmpeg esté "
                "instalado y que cookies.txt siga siendo válido."
            )

        except Exception as error:
            st.error(f"Error técnico: {error}")

    archivo = st.session_state.archivo_preparado

    if archivo:
        st.success(
            f"✅ Archivo {archivo['formato']} preparado correctamente."
        )

        tamaño_mb = len(archivo["datos"]) / (1024 * 1024)
        st.caption(f"Tamaño aproximado: {tamaño_mb:.2f} MB")

        if archivo["formato"] == "MP4":
            st.video(archivo["datos"])
        else:
            st.audio(archivo["datos"])

        st.download_button(
            label=f"⬇️ DESCARGAR {archivo['formato']}",
            data=archivo["datos"],
            file_name=archivo["nombre"],
            mime=archivo["mime"],
            type="primary",
            use_container_width=True,
            on_click="ignore",
        )

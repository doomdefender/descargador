import os
import re
import tempfile
from pathlib import Path

import streamlit as st
import yt_dlp
from yt_dlp.utils import download_range_func


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Offsave — Descargador",
    page_icon="⏻",
    layout="centered",
)

MAX_FILE_SIZE_MB = 450


# =========================================================
# ESTILO RETRO INSPIRADO EN WEBS DE DESCARGA DE 2011
# =========================================================

st.markdown(
    """
    <style>
    :root {
        --retro-black: #050505;
        --retro-paper: #dbe3e3;
        --retro-light: #f1f4f3;
        --retro-yellow: #f1ff00;
        --retro-muted: #667171;
    }

    html,
    body,
    [class*="css"] {
        font-family: Arial, Helvetica, sans-serif;
    }

    .stApp {
        color: var(--retro-black);
        background-color: var(--retro-paper);
        background-image:
            radial-gradient(
                circle at 15% 20%,
                rgba(255, 255, 255, 0.45),
                transparent 30%
            ),
            radial-gradient(
                circle at 85% 70%,
                rgba(0, 0, 0, 0.045),
                transparent 28%
            ),
            repeating-linear-gradient(
                0deg,
                rgba(255, 255, 255, 0.04) 0,
                rgba(255, 255, 255, 0.04) 1px,
                transparent 1px,
                transparent 4px
            );
    }

    header[data-testid="stHeader"],
    #MainMenu,
    footer {
        display: none;
    }

    .block-container {
        width: 100%;
        max-width: 800px;
        padding-top: 54px;
        padding-bottom: 80px;
    }

    .retro-brand {
        margin: 0 auto 34px;
        text-align: center;
        user-select: none;
    }

    .retro-wordmark {
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--retro-black);
        font-family: "Trebuchet MS", Arial, sans-serif;
        font-size: clamp(54px, 10vw, 88px);
        font-weight: 700;
        line-height: 0.95;
        letter-spacing: -7px;
    }

    .retro-power {
        display: inline-flex;
        width: 0.93em;
        height: 0.93em;
        margin-right: 5px;
        align-items: center;
        justify-content: center;
        color: var(--retro-paper);
        background: var(--retro-black);
        border-radius: 50%;
        font-size: 0.72em;
        letter-spacing: 0;
    }

    .retro-tagline {
        margin-top: 12px;
        padding-left: 18px;
        color: var(--retro-black);
        font-size: clamp(11px, 2.4vw, 17px);
        font-weight: 700;
        letter-spacing: 7px;
        text-transform: lowercase;
    }

    .retro-intro {
        max-width: 620px;
        margin: -8px auto 28px;
        color: #222;
        font-size: 14px;
        line-height: 1.55;
        text-align: center;
    }

    .retro-section-title {
        margin: 34px 0 5px;
        color: var(--retro-black);
        font-size: 27px;
        font-weight: 900;
        text-align: center;
    }

    .retro-subtitle {
        margin: 4px 0 22px;
        color: #344041;
        font-size: 13px;
        text-align: center;
    }

    .video-title {
        margin: 18px 0 7px;
        color: var(--retro-black);
        font-size: 24px;
        font-weight: 900;
        line-height: 1.2;
        text-align: center;
    }

    .video-author {
        margin-bottom: 20px;
        color: var(--retro-muted);
        font-size: 13px;
        text-align: center;
    }

    div[data-testid="stForm"] {
        padding: 0;
        background: transparent;
        border: none;
    }

    div[data-testid="stTextInput"] label {
        color: var(--retro-black) !important;
        font-weight: 800 !important;
    }

    div[data-testid="stTextInput"] input {
        min-height: 64px;
        padding: 0 18px;
        color: var(--retro-black) !important;
        background: var(--retro-light) !important;
        border: 4px solid var(--retro-black) !important;
        border-radius: 10px !important;
        box-shadow:
            inset 0 2px 4px rgba(0, 0, 0, 0.18),
            0 2px 0 rgba(255, 255, 255, 0.55);
        font-size: 16px;
        font-weight: 700;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: var(--retro-black) !important;
        box-shadow:
            inset 0 2px 4px rgba(0, 0, 0, 0.18),
            0 0 0 2px var(--retro-yellow) !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #7e8889;
        font-weight: 400;
    }

    div[data-testid="stFormSubmitButton"] button {
        width: 100%;
        min-height: 64px;
        padding: 0;
        color: white !important;
        background: var(--retro-black) !important;
        border: 4px solid var(--retro-black) !important;
        border-radius: 11px !important;
        box-shadow: 0 3px 0 rgba(255, 255, 255, 0.5);
        font-size: 19px;
        font-weight: 900;
        letter-spacing: 1px;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        color: var(--retro-yellow) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stFormSubmitButton"] button:active {
        transform: translateY(2px);
    }

    div[data-testid="stRadio"],
    div[data-testid="stSelectbox"] {
        padding: 13px 16px;
        margin-bottom: 10px;
        background: rgba(241, 244, 243, 0.78);
        border: 2px solid var(--retro-black);
        border-radius: 8px;
    }

    div[data-testid="stRadio"] label,
    div[data-testid="stSelectbox"] label {
        color: var(--retro-black) !important;
        font-weight: 800 !important;
    }

    div[data-testid="stMetric"] {
        min-height: 96px;
        padding: 14px;
        background: rgba(241, 244, 243, 0.84);
        border: 3px solid var(--retro-black);
        border-radius: 9px;
        text-align: center;
    }

    div[data-testid="stButton"] button {
        width: 100%;
        min-height: 54px;
        color: white !important;
        background: var(--retro-black) !important;
        border: 3px solid var(--retro-black) !important;
        border-radius: 9px !important;
        font-size: 16px;
        font-weight: 900;
    }

    div[data-testid="stButton"] button:hover {
        color: var(--retro-yellow) !important;
    }

    div[data-testid="stDownloadButton"] button {
        width: 100%;
        min-height: 72px;
        color: var(--retro-black) !important;
        background: var(--retro-yellow) !important;
        border: 4px solid var(--retro-black) !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 0 rgba(0, 0, 0, 0.2);
        font-size: 19px;
        font-weight: 900;
    }

    div[data-testid="stDownloadButton"] button:hover {
        color: var(--retro-black) !important;
        background: #fbff4d !important;
        transform: translateY(-2px);
    }

    div[data-testid="stAlert"] {
        color: var(--retro-black);
        background: rgba(241, 244, 243, 0.95);
        border: 3px solid var(--retro-black);
        border-radius: 9px;
    }

    div[data-testid="stProgress"] > div > div {
        background: var(--retro-yellow);
    }

    div[data-testid="stImage"] img,
    video,
    audio {
        border: 4px solid var(--retro-black);
        border-radius: 9px;
        background: black;
    }

    hr {
        margin: 35px 0;
        border: none;
        border-top: 4px solid var(--retro-black);
    }

    .retro-footer {
        margin-top: 55px;
        padding-top: 20px;
        border-top: 2px solid rgba(0, 0, 0, 0.35);
        color: #354041;
        font-size: 12px;
        line-height: 1.6;
        text-align: center;
    }

    @media (max-width: 600px) {
        .block-container {
            padding: 30px 14px 55px;
        }

        .retro-wordmark {
            letter-spacing: -4px;
        }

        .retro-tagline {
            padding-left: 6px;
            letter-spacing: 4px;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stFormSubmitButton"] button {
            min-height: 58px;
        }
    }
    </style>

    <div class="retro-brand">
        <div class="retro-wordmark">
            <span class="retro-power">⏻</span>ffsave
        </div>
        <div class="retro-tagline">evidence of offline life</div>
    </div>

    <div class="retro-intro">
        Guarda contenido para verlo o escucharlo sin conexión.
        Elige MP4, MP3, calidad y el fragmento exacto que necesitas.
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def segundos_a_tiempo(segundos: int | float | None) -> str:
    """Convierte segundos a HH:MM:SS o MM:SS."""
    if segundos is None:
        return "Desconocida"

    segundos = max(0, int(segundos))
    horas, resto = divmod(segundos, 3600)
    minutos, segundos = divmod(resto, 60)

    if horas:
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    return f"{minutos:02d}:{segundos:02d}"


def tiempo_a_segundos(valor: str) -> int:
    """Acepta segundos, MM:SS o HH:MM:SS."""
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
    """Limpia el nombre para la descarga."""
    nombre = re.sub(r'[<>:"/\\|?*]', "", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre[:150] or "archivo"


def opciones_comunes() -> dict:
    """Configuración común de yt-dlp."""
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
    """Obtiene información sin descargar."""
    opciones = opciones_comunes()
    opciones["skip_download"] = True

    with yt_dlp.YoutubeDL(opciones) as ydl:
        informacion = ydl.extract_info(enlace, download=False)
        return ydl.sanitize_info(informacion)


def selector_mp4(calidad: str) -> str:
    """Construye un selector de calidad para MP4."""
    alturas = {
        "Máxima disponible": None,
        "2160p (4K)": 2160,
        "1440p": 1440,
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


def encontrar_archivo(directorio: Path, extension: str) -> Path:
    """Localiza el archivo final creado por yt-dlp/FFmpeg."""
    archivos = list(directorio.glob(f"*.{extension}"))

    if not archivos:
        archivos = [
            archivo
            for archivo in directorio.iterdir()
            if archivo.is_file()
            and archivo.suffix.lower()
            not in {
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

    return max(archivos, key=lambda archivo: archivo.stat().st_mtime)


def descargar_archivo(
    enlace: str,
    formato_salida: str,
    calidad: str,
    bitrate: str,
    inicio: int | None,
    final: int | None,
    titulo: str,
) -> tuple[bytes, str, str]:
    """Descarga y devuelve bytes, nombre y tipo MIME."""

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
                        },
                        {
                            "key": "FFmpegMetadata",
                            "add_metadata": True,
                        },
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
                    "Descarga terminada. Procesando con FFmpeg..."
                )

        opciones["progress_hooks"] = [progreso]

        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([enlace])

        archivo_final = encontrar_archivo(directorio, extension)
        tamaño_mb = archivo_final.stat().st_size / (1024 * 1024)

        if tamaño_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"El archivo pesa {tamaño_mb:.1f} MB y supera el límite "
                f"de {MAX_FILE_SIZE_MB} MB configurado para esta aplicación."
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


# =========================================================
# ESTADO DE STREAMLIT
# =========================================================

if "informacion_video" not in st.session_state:
    st.session_state.informacion_video = None

if "url_analizada" not in st.session_state:
    st.session_state.url_analizada = ""

if "archivo_preparado" not in st.session_state:
    st.session_state.archivo_preparado = None


# =========================================================
# FORMULARIO PRINCIPAL
# =========================================================

with st.form("formulario_principal", clear_on_submit=False):
    columna_url, columna_off = st.columns(
        [5.2, 1],
        vertical_alignment="bottom",
    )

    with columna_url:
        url = st.text_input(
            "Dirección del contenido",
            placeholder="Paste the direct URL to online content...",
            label_visibility="collapsed",
        )

    with columna_off:
        analizar = st.form_submit_button(
            "OFF",
            use_container_width=True,
        )


if analizar:
    if not url.strip():
        st.warning("Pega primero el enlace del contenido.")

    elif not url.startswith(("https://", "http://")):
        st.error("El enlace debe comenzar con http:// o https://.")

    else:
        try:
            with st.spinner("Offliberando el enlace..."):
                informacion = analizar_video(url.strip())

            st.session_state.informacion_video = informacion
            st.session_state.url_analizada = url.strip()
            st.session_state.archivo_preparado = None

        except yt_dlp.utils.DownloadError as error:
            st.error("No fue posible analizar el enlace.")
            st.code(str(error)[-1000:], language=None)

        except Exception as error:
            st.error(f"Error técnico: {error}")


# =========================================================
# OPCIONES DE DESCARGA
# =========================================================

informacion = st.session_state.informacion_video

if informacion and st.session_state.url_analizada == url.strip():
    titulo = informacion.get("title") or "Video"
    duracion = informacion.get("duration")
    thumbnail = informacion.get("thumbnail")
    autor = (
        informacion.get("uploader")
        or informacion.get("channel")
        or "Autor desconocido"
    )

    st.divider()

    if thumbnail:
        st.image(thumbnail, use_container_width=True)

    st.markdown(
        f"""
        <div class="video-title">{titulo}</div>
        <div class="video-author">{autor}</div>
        """,
        unsafe_allow_html=True,
    )

    columna_1, columna_2 = st.columns(2)

    with columna_1:
        st.metric(
            "Duración",
            segundos_a_tiempo(duracion),
        )

    with columna_2:
        st.metric(
            "Tipo",
            informacion.get("extractor_key") or "Contenido web",
        )

    st.markdown(
        """
        <div class="retro-section-title">Elige tu descarga</div>
        <div class="retro-subtitle">
            Selecciona formato, calidad y duración.
        </div>
        """,
        unsafe_allow_html=True,
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
                "2160p (4K)",
                "1440p",
                "1080p",
                "720p",
                "480p",
                "360p",
            ],
            index=4,
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
            "Contenido completo",
            "Seleccionar fragmento",
        ],
    )

    inicio_segundos = None
    final_segundos = None
    tiempos_validos = True

    if tipo_descarga == "Seleccionar fragmento":
        st.info(
            "Escribe el punto inicial y final. "
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
                value=(
                    segundos_a_tiempo(duracion)
                    if duracion
                    else "01:00"
                ),
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

            elif duracion and final_segundos > int(duracion):
                st.error(
                    "El tiempo final supera la duración del contenido."
                )
                tiempos_validos = False

            else:
                duracion_fragmento = (
                    final_segundos - inicio_segundos
                )

                st.success(
                    "Fragmento seleccionado: "
                    f"{segundos_a_tiempo(duracion_fragmento)}"
                )

        except ValueError as error:
            st.error(str(error))
            tiempos_validos = False

    preparar = st.button(
        f"PREPARAR DESCARGA {formato_salida}",
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
            f"Archivo {archivo['formato']} preparado correctamente."
        )

        tamaño_mb = len(archivo["datos"]) / (1024 * 1024)
        st.caption(f"Tamaño aproximado: {tamaño_mb:.2f} MB")

        if archivo["formato"] == "MP4":
            st.video(archivo["datos"])
            etiqueta = "DESCARGAR ARCHIVO DE VIDEO"
        else:
            st.audio(archivo["datos"])
            etiqueta = "DESCARGAR ARCHIVO DE AUDIO"

        st.download_button(
            label=etiqueta,
            data=archivo["datos"],
            file_name=archivo["nombre"],
            mime=archivo["mime"],
            type="primary",
            use_container_width=True,
            on_click="ignore",
        )


st.markdown(
    """
    <div class="retro-footer">
        Descarga únicamente contenido propio, de dominio público
        o para el que tengas autorización.<br>
        OFFSAVE procesa los archivos de forma temporal.
    </div>
    """,
    unsafe_allow_html=True,
)

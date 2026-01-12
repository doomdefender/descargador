import streamlit as st
import yt_dlp
import os

st.set_page_config(page_title="Video Downloader", page_icon="📥")

st.title("📥 Descargador de Videos")
st.subheader("Fácil, rápido y sin errores")

url = st.text_input("Pega el enlace de YouTube aquí:", placeholder="https://www.youtube.com/watch?v=...")

if url:
    try:
        with st.spinner("Buscando video..."):
            ydl_opts = {'format': 'best'}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'video')
                video_url = info.get('url')
                thumbnail = info.get('thumbnail')

        st.image(thumbnail, width=300)
        st.write(f"**Título:** {video_title}")

        # Botón mágico de descarga
        st.video(video_url)
        st.link_button("⬇️ DESCARGAR AHORA", video_url)
        
    except Exception as e:
        st.error("No se pudo cargar el video. Revisa el link.")

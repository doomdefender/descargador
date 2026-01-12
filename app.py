import streamlit as st
import yt_dlp

st.set_page_config(page_title="Descargador Pro", page_icon="📥")
st.title("📥 Mi Descargador Web")

url = st.text_input("Pega el enlace aquí:", placeholder="https://...")

if url:
    try:
        # Configuración más robusta para evitar bloqueos
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'source_address': '0.0.0.0', # Ayuda con problemas de red
        }
        
        with st.spinner("Analizando enlace..."):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_url = info.get('url')
                title = info.get('title')
                
        st.success(f"✅ Video encontrado: {title}")
        st.video(video_url)
        st.link_button("⬇️ CLIC PARA DESCARGAR", video_url)

    except Exception as e:
        st.error(f"Error técnico: {str(e)[:100]}") # Nos dirá una pista del error
        st.info("Prueba con un video diferente o revisa que el link sea de un video público.")

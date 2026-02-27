import streamlit as st
import feedparser
import urllib.parse
from google import genai
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Kedah Infodemic Firewatch",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD CSS ---
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'keyword' not in st.session_state:
    st.session_state.keyword = "vape kedah"
if 'last_results' not in st.session_state:
    st.session_state.last_results = []

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e0/Coat_of_arms_of_Kedah.svg", width=100)
    st.title("KIF CONTROL")
    st.markdown("---")
    
    st.session_state.api_key = st.text_input(
        "GEMINI API KEY", 
        value=st.session_state.api_key, 
        type="password",
        help="Dapatkan kunci API anda dari Google AI Studio."
    )
    
    st.session_state.keyword = st.text_input(
        "KATA KUNCI SURVEILANS", 
        value=st.session_state.keyword,
        placeholder="cth: bunuh diri kedah"
    )
    
    st.markdown("---")
    run_btn = st.button("🚀 LANCARKAN FIREWATCH")
    
    st.info("KIF v3.0 (Standalone Mode)")

# --- MAIN CONTENT ---
st.title("🛡️ Kedah Infodemic Firewatch")
st.markdown("### Command Center Pemantauan Isu Kesihatan Awam")

if run_btn:
    if not st.session_state.api_key:
        st.error("Ralat: Sila masukkan API Key Gemini di bar sisi.")
    else:
        with st.spinner("⏳ Menghubungi satelit data... Sedang mencari isu terkini."):
            # 1. RSS FETCHING
            encoded_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(st.session_state.keyword)}&hl=ms&gl=MY&ceid=MY:ms"
            feed = feedparser.parse(encoded_url)
            
            if feed.entries:
                st.session_state.last_results = feed.entries[:5]  # Ambil 5 berita teratas
                
                # Sediakan input untuk AI (Batching)
                news_context = ""
                for i, entry in enumerate(st.session_state.last_results):
                    news_context += f"ISU {i+1}: {entry.title}\n"

                # 2. DISPLAY DETECTED ISSUES FIRST
                st.subheader(f"🔍 {len(st.session_state.last_results)} ISU DIKESAN")
                
                # Show a preview of the news items found
                for i, entry in enumerate(st.session_state.last_results):
                    with st.expander(f"📌 {entry.title}", expanded=(i==0)):
                        st.write(f"**Sumber:** {entry.get('source', {}).get('title', 'Google News')}")
                        st.write(f"**Pautan:** [Baca Berita Penuh]({entry.link})")
                
                st.markdown("---")

                # 3. AI ANALYSIS
                try:
                    client = genai.Client(api_key=st.session_state.api_key)
                    
                    with st.spinner("🧠 Pakar AI sedang menganalisa keseluruhan senarai isu..."):
                        response = client.models.generate_content(
                            model="gemini-2.0-flash", 
                            contents=f"""
                            Berlakon sebagai Pakar Kesihatan Awam dan Komunikasi Risiko di JKN Kedah.
                            Analisis senarai berita berikut secara berasingan:
                            
                            {news_context}
                            
                            Sila berikan output dalam format Markdown yang kemas. 
                            Bagi SETIAP isu, berikan:
                            1. **Isu**: (Tajuk Isu)
                            2. **Sentiment**: (Positif/Negatif/Neutral)
                            3. **Tahap Risiko**: (Skor 1-10 &sebab)
                            4. **Cadangan**: (Tindakan JKN Kedah)
                            5. **Status Fakta**: (Sahih/Rumor/Clickbait)
                            
                            Gunakan format 'card' atau pembahagi yang jelas antara isu.
                            """
                        )
                    
                    st.success("✅ ANALISIS BERKELOMPOK SIAP")
                    st.markdown(response.text)
                            
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg:
                        st.error("🚨 KUOTA AI TAMAT (RESOURCE EXHAUSTED)")
                        st.warning("""
                        Punca: Anda menggunakan pelan percuma Gemini. 
                        Tindakan: Sila tunggu 1 minit sebelum mencuba lagi.
                        Tips: Batching telah diaktifkan untuk mengurangkan penggunaan kuota.
                        """)
                    elif "API_KEY_INVALID" in error_msg or "400" in error_msg:
                        st.error("❌ API KEY TIDAK SAH")
                        st.error("""
                        Sila pastikan API Key yang anda masukkan di bar sisi adalah betul. 
                        Anda boleh mendapatkan kunci baru dari [Google AI Studio](https://aistudio.google.com/app/apikey).
                        """)
                        st.info("Nota: Anda masih boleh melihat senarai berita yang ditemui di atas.")
                    else:
                        st.error(f"⚠️ Ralat Teknikal: {error_msg}")
                        st.info("Menjalankan mod simulasi untuk demonstrasi...")
                        st.write("**Sentimen:** Resah | **Risiko:** 7/10 | **Tindakan:** Pantau media sosial.")
            else:
                st.warning("Tiada berita baru ditemui untuk kata kunci tersebut.")

else:
    # Initial State / Welcome
    st.write("Sila masukkan kata kunci di bar sisi dan klik 'Lancarkan Firewatch' untuk memulakan analisa.")
    
    # Placeholder layout
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status Sistem", "ONLINE", "ACTIVE")
    with col2:
        st.metric("Unit", "Surveilans Digital", "JKN KEDAH")
    with col3:
        st.metric("AI Engine", "Gemini 2.0 Flash", "LLM")

    st.markdown("""
    ### Panduan Penggunaan:
    1. **Masukkan API Key**: Gunakan kunci API anda dari Google AI Studio.
    2. **Tentukan Kata Kunci**: Fokus kepada isu spesifik (cth: "vape sekolah", "bulu babi", "keracunan makanan kedah").
    3. **Analisa**: Sistem akan mengambil data berita terkini dan menggunakan AI untuk menilai impak infodemik.
    4. **Bertindak**: Gunakan cadangan AI untuk merangka pelan komunikasi risiko.
    """)

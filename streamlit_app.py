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
if 'ai_analysis' not in st.session_state:
    st.session_state.ai_analysis = ""
if 'news_context' not in st.session_state:
    st.session_state.news_context = ""

# --- FUNCTIONS ---
def run_ai_analysis():
    if not st.session_state.api_key:
        st.error("Ralat: Sila masukkan API Key Gemini di bar sisi.")
        return

    try:
        client = genai.Client(api_key=st.session_state.api_key)
        with st.spinner("🧠 Pakar AI sedang menganalisa keseluruhan senarai isu..."):
            response = client.models.generate_content(
                model="gemini-2.0-flash", 
                contents=f"""
                Berlakon sebagai Pakar Kesihatan Awam dan Komunikasi Risiko di JKN Kedah.
                Analisis senarai berita berikut secara berasingan:
                
                {st.session_state.news_context}
                
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
        
        if response.text:
            st.session_state.ai_analysis = response.text
            st.success("✅ ANALISIS BERKELOMPOK SIAP")
        else:
            st.info("Tiada isu yang signifikan dijumpai dalam laporan berita ini.")
                
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg:
            st.warning("🚨 KUOTA AI TAMAT (RESOURCE EXHAUSTED)")
            st.error("Sila tunggu 1 minit sebelum menekan butang 'Cuba Analisa Semula' di bawah.")
        elif "API_KEY_INVALID" in error_msg or "400" in error_msg:
            st.error("❌ API KEY TIDAK SAH")
            st.info("Sila masukkan API Key Gemini yang sah.")
        else:
            st.error(f"⚠️ Ralat Teknikal AI: {error_msg}")

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

    timeframe = st.selectbox(
        "TEMPOH MASA",
        options=["1 hari", "3 hari", "7 hari", "30 hari"],
        index=1  # Default 3 hari
    )

    sources = st.multiselect(
        "SUMBER SURVEILANS",
        options=["Portal Berita", "TikTok", "Facebook", "X (Twitter)"],
        default=["Portal Berita"]
    )
    
    # Map timeframe to Google News 'when' operator
    tf_map = {"1 hari": "1d", "3 hari": "3d", "7 hari": "7d", "30 hari": "30d"}
    tf_code = tf_map[timeframe]
    
    st.markdown("---")
    run_btn = st.button("🚀 LANCARKAN FIREWATCH")
    
    st.info("KIF v3.0 (Standalone Mode)")

# --- MAIN CONTENT ---
st.title("🛡️ Kedah Infodemic Firewatch")
st.markdown("### Command Center Pemantauan Isu Kesihatan Awam")

if run_btn:
    st.session_state.ai_analysis = "" # Reset analysis on new run
    if not st.session_state.api_key:
        st.error("Ralat: Sila masukkan API Key Gemini di bar sisi.")
    elif not sources:
        st.error("Ralat: Sila pilih sekurang-kurangnya satu sumber surveilans.")
    else:
        with st.spinner(f"⏳ Menghubungi satelit data... Mencari di {', '.join(sources)}."):
            # 1. RSS FETCHING - Construct Advanced Query
            base_query = st.session_state.keyword
            
            # Platform filters
            site_filters = []
            if "TikTok" in sources: site_filters.append("site:tiktok.com")
            if "Facebook" in sources: site_filters.append("site:facebook.com")
            if "X (Twitter)" in sources: site_filters.append("site:x.com OR site:twitter.com")
            
            if site_filters:
                # If searching social media, add viral keywords to catch discourse
                platform_query = f"({ ' OR '.join(site_filters) })"
                if "Portal Berita" in sources:
                    search_query = f"{base_query} (viral OR isu OR {platform_query}) when:{tf_code}"
                else:
                    search_query = f"{base_query} {platform_query} when:{tf_code}"
            else:
                search_query = f"{base_query} when:{tf_code}"

            encoded_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_query)}&hl=ms&gl=MY&ceid=MY:ms"
            feed = feedparser.parse(encoded_url)
            
            if feed.entries:
                st.session_state.last_results = feed.entries[:5]
                
                # Sediakan input untuk AI
                st.session_state.news_context = ""
                for i, entry in enumerate(st.session_state.last_results):
                    st.session_state.news_context += f"ISU {i+1}: {entry.title}\n"
                
                # Jalankan analisa kali pertama
                run_ai_analysis()
            else:
                st.session_state.last_results = []
                st.warning(f"Tiada isu yang signifikan dijumpai untuk '{st.session_state.keyword}' di platform yang dipilih bagi tempoh {timeframe}.")

# --- DISPLAY SECTION ---
if st.session_state.last_results:
    st.subheader(f"🔍 {len(st.session_state.last_results)} ISU REAL-TIME DIKESAN")
    st.caption("Data daripada Google News RSS")
    
    for i, entry in enumerate(st.session_state.last_results):
        with st.expander(f"📌 {entry.title}", expanded=(i==0)):
            st.write(f"**Sumber Berita:** {entry.get('source', {}).get('title', 'Berita Tempatan')}")
            st.markdown(f"**Pautan Terus:** [KLIK SINI UNTUK BACA BERITA PENUH]({entry.link})")
    
    st.markdown("---")
    st.subheader("🧠 ANALISA PAKAR AI (JKN KEDAH)")
    
    if st.session_state.ai_analysis:
        st.markdown(st.session_state.ai_analysis)
    else:
        # Jika berita ada tapi analisa tiada (mungkin sebab ralat tadi), tunjuk butang retry
        st.info("Analisa AI tidak tersedia buat masa ini.")
        if st.button("🔄 CUBA ANALISA SEMULA"):
            run_ai_analysis()
            st.rerun()

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

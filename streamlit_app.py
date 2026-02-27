import streamlit as st
import feedparser
import urllib.parse
from google import genai
from openai import OpenAI
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
if 'ai_engine' not in st.session_state:
    st.session_state.ai_engine = "Gemini (Google)"
if 'retry_active' not in st.session_state:
    st.session_state.retry_active = False

# --- FUNCTIONS ---
def run_ai_analysis(retry_count=0):
    if not st.session_state.api_key:
        st.error(f"Ralat: Sila masukkan API Key untuk {st.session_state.ai_engine} di bar sisi.")
        return

    try:
        prompt = f"""
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

        with st.spinner(f"🧠 {st.session_state.ai_engine} sedang menganalisa isu..."):
            if st.session_state.ai_engine == "Gemini (Google)":
                client = genai.Client(api_key=st.session_state.api_key)
                response = client.models.generate_content(model=gemini_model, contents=prompt)
                st.session_state.ai_analysis = response.text
            
            elif st.session_state.ai_engine == "ChatGPT (OpenAI)":
                client = OpenAI(api_key=st.session_state.api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.session_state.ai_analysis = response.choices[0].message.content
            
            elif st.session_state.ai_engine == "DeepSeek":
                client = OpenAI(api_key=st.session_state.api_key, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.session_state.ai_analysis = response.choices[0].message.content

        if st.session_state.ai_analysis:
            st.success(f"✅ ANALISIS {st.session_state.ai_engine.upper()} SIAP")
        else:
            st.warning("⚠️ AI memulangkan respons kosong.")
                
    except Exception as e:
        error_msg = str(e)
        st.session_state.ai_analysis = ""
        
        # Kes Khas OpenAI (Insufficient Balance)
        if "insufficient_quota" in error_msg.lower():
            st.error("💳 BAKI AKAUN TIADA (OpenAI/ChatGPT)")
            st.info("Nota: Akaun ChatGPT API anda perlu diisi prabayar (min $5). Sila semak status di platform.openai.com.")
            st.session_state.retry_active = False
            return

        if "429" in error_msg and retry_count < 1:
            st.warning("🚨 HAD KUOTA DICAPAI. Menunggu 30 saat untuk cuba semula secara automatik...")
            st.session_state.retry_active = True
            progress_bar = st.progress(0)
            for i in range(30):
                time.sleep(1)
                progress_bar.progress((i + 1) / 30)
            st.rerun() 
        else:
            st.error(f"❌ RALAT TEKNIKAL: {st.session_state.ai_engine}")
            st.code(error_msg)
            st.session_state.retry_active = False
            if "api_key" in error_msg.lower() or "invalid" in error_msg.lower():
                st.error("🔑 Masalah Kunci API: Sila pastikan kunci adalah sah untuk enjin ini.")
            else:
                st.info("Sila pastikan anda mempunyai sambungan internet yang stabil dan API Key yang aktif.")

# --- SIDEBAR ---
with st.sidebar:
    # Menggunakan PNG link yang lebih stabil untuk logo Kedah
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Coat_of_arms_of_Kedah.svg/150px-Coat_of_arms_of_Kedah.svg.png", width=100)
    st.title("KIF CONTROL")
    st.markdown("---")
    
    st.session_state.ai_engine = st.selectbox(
        "PILIH ENJIN AI",
        options=["Gemini (Google)", "ChatGPT (OpenAI)", "DeepSeek"],
        index=0
    )

    # Sub-options for Gemini models if selected
    gemini_model = "gemini-2.0-flash"
    if st.session_state.ai_engine == "Gemini (Google)":
        gemini_model = st.selectbox(
            "VERSI GEMINI",
            options=["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"],
            index=0,
            help="Jika keluar ralat 404, cuba tukar ke versi lain."
        )

    st.session_state.api_key = st.text_input(
        f"KUNCI API {st.session_state.ai_engine.upper()}", 
        value=st.session_state.api_key, 
        type="password",
        help=f"Pastikan kunci anda sah untuk {st.session_state.ai_engine}."
    )
    
    with st.expander("🛠️ DEBUG (TEKNIKAL)"):
        if st.button("SENARAI MODEL TERSEDIA"):
            if not st.session_state.api_key:
                st.error("Masukkan API Key dahulu.")
            else:
                try:
                    if st.session_state.ai_engine == "Gemini (Google)":
                        client = genai.Client(api_key=st.session_state.api_key)
                        models = client.models.list()
                        st.write("Model yang kunci anda boleh akses:")
                        for m in models:
                            st.code(m.name)
                    else:
                        st.info("Ciri ini hanya untuk Gemini buat masa ini.")
                except Exception as e:
                    st.error(f"Gagal senaraikan model: {str(e)}")
    
    st.session_state.keyword = st.text_input(
        "KATA KUNCI SURVEILANS", 
        value=st.session_state.keyword,
        placeholder="cth: bunuh diri kedah"
    )

    timeframe = st.selectbox(
        "TEMPOH MASA",
        options=["1 hari", "3 hari", "7 hari", "30 hari"],
        index=1
    )

    sources = st.multiselect(
        "SUMBER SURVEILANS",
        options=["Semua Platform", "Portal Berita", "TikTok", "Facebook", "X (Twitter)"],
        default=["Semua Platform"]
    )
    
    tf_map = {"1 hari": "1d", "3 hari": "3d", "7 hari": "7d", "30 hari": "30d"}
    tf_code = tf_map[timeframe]
    
    st.markdown("---")
    run_btn = st.button("🚀 LANCARKAN FIREWATCH")
    
    st.info("KIF v3.0 (Standalone Mode)")

# --- AUTO-RETRY LOGIC ---
if st.session_state.retry_active:
    st.session_state.retry_active = False
    run_ai_analysis()

# --- MAIN CONTENT ---
st.title("🛡️ Kedah Infodemic Firewatch")
st.markdown("### Sistem Pemantauan Isu Kesihatan Awam")

if run_btn:
    st.session_state.ai_analysis = ""
    if not st.session_state.api_key:
        st.error(f"Ralat: Sila masukkan API Key {st.session_state.ai_engine} di bar sisi.")
    elif not sources:
        st.error("Ralat: Sila pilih sekurang-kurangnya satu sumber surveilans.")
    else:
        with st.spinner(f"⏳ Mencari data di {', '.join(sources)}..."):
            # Gunakan quotes untuk ketepatan kata kunci (Exact Match)
            base_query = f'"{st.session_state.keyword}"'
            
            # Platform filters
            site_filters = []
            if "TikTok" in sources: site_filters.append("site:tiktok.com")
            if "Facebook" in sources: site_filters.append("site:facebook.com")
            if "X (Twitter)" in sources: site_filters.append("site:x.com OR site:twitter.com")
            
            if "Semua Platform" in sources:
                # Cari merentasi semua, tapi pastikan kata kunci wujud
                search_query = f"{base_query} when:{tf_code}"
            elif site_filters:
                # Filter platform secara spesifik
                platform_query = f"({ ' OR '.join(site_filters) })"
                # Gabungkan kata kunci DENGAN platform (Gunakan AND logic)
                search_query = f"{base_query} {platform_query} when:{tf_code}"
            else:
                # Portal Berita sahaja
                search_query = f"{base_query} when:{tf_code}"

            encoded_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_query)}&hl=ms&gl=MY&ceid=MY:ms"
            feed = feedparser.parse(encoded_url)
            
            # Jika carian spesifik tiada hasil, cuba longgarkan sedikit (tanpa quotes)
            if not feed.entries:
                search_query_relaxed = f"{st.session_state.keyword} {' '.join(site_filters)} when:{tf_code}"
                encoded_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_query_relaxed)}&hl=ms&gl=MY&ceid=MY:ms"
                feed = feedparser.parse(encoded_url)

            if feed.entries:
                # Filter tambahan secara manual untuk pastikan kata kunci wujud dalam tajuk
                # (Google RSS kadangkala bagi 'related' content yang tidak tepat)
                relevant_entries = []
                kw_lower = st.session_state.keyword.lower()
                for entry in feed.entries:
                    if kw_lower in entry.title.lower():
                        relevant_entries.append(entry)
                
                # Jika filter manual terlalu ketat (0 hasil), ambil saja apa yang Google bagi
                if not relevant_entries:
                    relevant_entries = feed.entries[:5]
                else:
                    relevant_entries = relevant_entries[:5]

                st.session_state.last_results = relevant_entries
                st.session_state.news_context = ""
                for i, entry in enumerate(st.session_state.last_results):
                    st.session_state.news_context += f"ISU {i+1}: {entry.title}\n"
                run_ai_analysis()
            else:
                st.session_state.last_results = []
                st.warning(f"Tiada isu ditemui untuk '{st.session_state.keyword}' bagi platform tempoh {timeframe}.")

# --- DISPLAY SECTION ---
if st.session_state.last_results:
    st.subheader(f"🔍 {len(st.session_state.last_results)} ISU REAL-TIME DIKESAN")
    for i, entry in enumerate(st.session_state.last_results):
        with st.expander(f"📌 {entry.title}", expanded=(i==0)):
            st.write(f"**Sumber Berita:** {entry.get('source', {}).get('title', 'Berita Tempatan')}")
            st.markdown(f"**Pautan Terus:** [KLIK SINI UNTUK BACA BERITA PENUH]({entry.link})")
    
    st.markdown("---")
    st.subheader(f"🧠 ANALISA {st.session_state.ai_engine.upper()}")
    
    if st.session_state.ai_analysis:
        st.markdown(st.session_state.ai_analysis)
    else:
        st.info("Analisa AI tidak tersedia buat masa ini.")
        if st.button("🔄 CUBA ANALISA SEMULA"):
            run_ai_analysis()
            st.rerun()

else:
    st.write("Sila masukkan kata kunci di bar sisi dan klik 'Lancarkan Firewatch' untuk memulakan analisa.")
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Status Sistem", "ONLINE", "ACTIVE")
    with col2: st.metric("Unit", "NCD", "JKN KEDAH")
    with col3: st.metric("Multi-AI Mode", "READY", "Gemini/GPT/DeepSeek")
    st.markdown("""
    ### Jadikan Surveilans Lebih Fleksibel:
    1. **Pilih Enjin AI**: Gunakan Gemini secara percuma, atau masukkan kunci ChatGPT/DeepSeek jika mahu alternatif.
    2. **Pilih Sumber**: Pantau portal berita atau terus ke media sosial (TikTok/FB).
    3. **Tapis Masa**: Fokus kepada isu yang paling baru (24 jam hingga 30 hari).
    """)

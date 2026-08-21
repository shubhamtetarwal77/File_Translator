"""
Universal File Translator - Main Streamlit Application
Upload any file → Translate → Download in same format
"""

import streamlit as st
import os
import tempfile
from pathlib import Path
import time

from core.translator import TranslationEngine
from core.handlers import get_handler

# ─── Page Configuration (Must be the first st command) ─────────────
st.set_page_config(
    page_title="Universal File Translator",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Language Mapping ──────────────────────────────────────────────
LANGUAGES = {
    'Auto Detect': 'auto',
    'Afrikaans': 'af', 'Albanian': 'sq', 'Arabic': 'ar', 'Armenian': 'hy',
    'Azerbaijani': 'az', 'Basque': 'eu', 'Belarusian': 'be', 'Bengali': 'bn',
    'Bosnian': 'bs', 'Bulgarian': 'bg', 'Catalan': 'ca', 'Cebuano': 'ceb',
    'Chinese (Simplified)': 'zh-CN', 'Chinese (Traditional)': 'zh-TW',
    'Croatian': 'hr', 'Czech': 'cs', 'Danish': 'da', 'Dutch': 'nl',
    'English': 'en', 'Esperanto': 'eo', 'Estonian': 'et', 'Filipino': 'tl',
    'Finnish': 'fi', 'French': 'fr', 'Galician': 'gl', 'Georgian': 'ka',
    'German': 'de', 'Greek': 'el', 'Gujarati': 'gu', 'Haitian Creole': 'ht',
    'Hausa': 'ha', 'Hebrew': 'iw', 'Hindi': 'hi', 'Hmong': 'hmn',
    'Hungarian': 'hu', 'Icelandic': 'is', 'Igbo': 'ig', 'Indonesian': 'id',
    'Irish': 'ga', 'Italian': 'it', 'Japanese': 'ja', 'Javanese': 'jw',
    'Kannada': 'kn', 'Kazakh': 'kk', 'Khmer': 'km', 'Korean': 'ko',
    'Kurdish': 'ku', 'Kyrgyz': 'ky', 'Lao': 'lo', 'Latin': 'la',
    'Latvian': 'lv', 'Lithuanian': 'lt', 'Luxembourgish': 'lb',
    'Macedonian': 'mk', 'Malagasy': 'mg', 'Malay': 'ms', 'Malayalam': 'ml',
    'Maltese': 'mt', 'Maori': 'mi', 'Marathi': 'mr', 'Mongolian': 'mn',
    'Myanmar (Burmese)': 'my', 'Nepali': 'ne', 'Norwegian': 'no',
    'Persian': 'fa', 'Polish': 'pl', 'Portuguese': 'pt', 'Punjabi': 'pa',
    'Romanian': 'ro', 'Russian': 'ru', 'Serbian': 'sr', 'Sesotho': 'st',
    'Sinhala': 'si', 'Slovak': 'sk', 'Slovenian': 'sl', 'Somali': 'so',
    'Spanish': 'es', 'Sundanese': 'su', 'Swahili': 'sw', 'Swedish': 'sv',
    'Tajik': 'tg', 'Tamil': 'ta', 'Telugu': 'te', 'Thai': 'th',
    'Turkish': 'tr', 'Ukrainian': 'uk', 'Urdu': 'ur', 'Uzbek': 'uz',
    'Vietnamese': 'vi', 'Welsh': 'cy', 'Yiddish': 'yi', 'Yoruba': 'yo',
    'Zulu': 'zu'
}

SUPPORTED_EXTENSIONS = [
    '.docx', '.pdf', '.xlsx', '.xls', '.csv', '.pptx',
    '.txt', '.rtf', '.md',
    '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp',
    '.srt', '.vtt',
    '.json', '.xml', '.html', '.htm',
]

FILE_TYPE_ICONS = {
    '.docx': '📄', '.pdf': '📕', '.xlsx': '📊', '.xls': '📊',
    '.csv': '📊', '.pptx': '📑', '.txt': '📝', '.rtf': '📝',
    '.md': '📝', '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️',
    '.bmp': '🖼️', '.tiff': '🖼️', '.tif': '🖼️', '.webp': '🖼️',
    '.srt': '🎬', '.vtt': '🎬', '.json': '🔧', '.xml': '🔧',
    '.html': '🌐', '.htm': '🌐',
}


def format_file_size(size_bytes):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def load_global_css():
    """Inject global CSS that applies to both Landing Page and Main App."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Poppins:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Animated background */
    .stApp {
        background: linear-gradient(-45deg, #050510, #1a1a3a, #0f0f24, #050510);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Primary buttons */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #7b2ff7, #00d4ff);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(123, 47, 247, 0.4);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.6);
    }

    /* App Title */
    h1.app-title {
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle {
        text-align: center;
        color: #b0b0d0;
        font-size: 1.2rem;
        margin-bottom: 1rem;
    }
    
    /* Hide top bar */
    header { display: none !important; }
    </style>
    """, unsafe_allow_html=True)


def show_landing_page():
    """Displays the animated welcome screen."""
    
    # Custom CSS for the landing page visuals
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    
    .map-container {
        position: relative;
        width: 100%;
        height: 500px;
        background: url('https://upload.wikimedia.org/wikipedia/commons/8/80/World_map_-_low_resolution.svg') no-repeat center center;
        background-size: contain;
        opacity: 0.85;
        margin-top: 30px;
        margin-bottom: 50px;
        filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.2));
    }

    .floating-lang {
        position: absolute;
        font-weight: 700;
        font-size: 1.5rem;
        padding: 8px 16px;
        border-radius: 20px;
        background: rgba(15, 12, 41, 0.8);
        backdrop-filter: blur(5px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        color: white;
    }

    /* Coordinates and animations for floating languages */
    .lang-en { top: 25%; left: 15%; color: #00d4ff; animation: float 4s ease-in-out infinite; } /* North America */
    .lang-es { top: 60%; left: 25%; color: #ff2fd0; animation: float 5s ease-in-out infinite 0.5s; } /* South America */
    .lang-fr { top: 30%; left: 45%; color: #7b2ff7; animation: float 6s ease-in-out infinite 1s; } /* Europe */
    .lang-ar { top: 45%; left: 55%; color: #00ffcc; animation: float 4.5s ease-in-out infinite 1.5s; } /* Middle East */
    .lang-hi { top: 45%; left: 68%; color: #ffaa00; animation: float 5.5s ease-in-out infinite 0.2s; } /* India */
    .lang-ja { top: 35%; left: 82%; color: #ff5555; animation: float 4s ease-in-out infinite 0.8s; } /* Japan */
    .lang-sw { top: 65%; left: 52%; color: #aaff00; animation: float 5s ease-in-out infinite 1.2s; } /* Africa */

    @keyframes float {
        0% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-20px) scale(1.05); }
        100% { transform: translateY(0px) scale(1); }
    }

    .feature-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(123, 47, 247, 0.3);
        border-radius: 15px;
        padding: 25px;
        height: 100%;
        text-align: center;
        transition: transform 0.3s;
    }
    .feature-card:hover {
        transform: translateY(-10px);
        background: rgba(255,255,255,0.06);
        border-color: #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Main Hero Header
    st.markdown("<h1 class='app-title' style='font-size: 4.5rem !important; margin-top:20px;'>Break Language Barriers</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>The world is connected. Your files should be too. Translate entire documents, spreadsheets, and presentations while keeping the exact same layout.</p>", unsafe_allow_html=True)

    # Big Call to Action Button
    col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1, 1.5])
    with col_btn2:
        st.write("") # spacing
        if st.button("Open Translator", use_container_width=True):
            st.session_state.app_started = True
            st.rerun()

    # 2. Interactive Animated World Map
    st.markdown("""
    <div class="map-container">
        <div class="floating-lang lang-en">Hello 👋</div>
        <div class="floating-lang lang-es">Hola 💃</div>
        <div class="floating-lang lang-fr">Bonjour 🥐</div>
        <div class="floating-lang lang-ar">مرحباً 🕌</div>
        <div class="floating-lang lang-hi">नमस्ते 🪷</div>
        <div class="floating-lang lang-ja">こんにちは 🌸</div>
        <div class="floating-lang lang-sw">Jambo 🌍</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 3. Why Translation Matters
    st.markdown("<h2 style='text-align:center; margin-bottom: 30px; color: #fff;'>The Power of Understanding</h2>", unsafe_allow_html=True)
    
    col_feat1, col_feat2, col_feat3 = st.columns(3)
    
    with col_feat1:
        st.markdown("""
        <div class="feature-card">
            <h1 style="font-size: 3rem; margin:0;">🌍</h1>
            <h3 style="color:#00d4ff;">Global Business</h3>
            <p style="color:#b0b0d0;">Seamlessly translate contracts, pitch decks, and financial spreadsheets. Expand your company's reach to international markets without breaking your document layouts.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_feat2:
        st.markdown("""
        <div class="feature-card">
            <h1 style="font-size: 3rem; margin:0;">🤝</h1>
            <h3 style="color:#ff2fd0;">Deep Connections</h3>
            <p style="color:#b0b0d0;">Translate letters, subtitle files (SRT/VTT), and images. Share stories, movies, and culture with people around the world, making the planet feel a little bit smaller.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_feat3:
        st.markdown("""
        <div class="feature-card">
            <h1 style="font-size: 3rem; margin:0;">🎓</h1>
            <h3 style="color:#7b2ff7;">Limitless Learning</h3>
            <p style="color:#b0b0d0;">Access research papers, academic PDFs, and historical texts originally written in foreign languages. Turn any PDF into a readable, localized Word document instantly.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("<br><br>", unsafe_allow_html=True)

    # 4. Images with updated use_container_width
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        st.image("https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", caption="Collaborate across borders.", use_container_width=True)
    with col_img2:
        st.image("https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", caption="A connected world.", use_container_width=True)

    st.write("<br><br>", unsafe_allow_html=True)


def show_main_app():
    """Displays the main translation tool."""
    
    st.markdown("<h1 class='app-title'>🌐 Universal File Translator</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>Upload any document, spreadsheet, presentation, image, or subtitle file — "
        "translate it into your preferred language and download it "
        "(<i>Note: PDFs will be converted to DOCX</i>).</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # ─── Sidebar Settings ──────────────────────────────────────────
    with st.sidebar:
        if st.button("🏠 Back to Home Screen"):
            st.session_state.app_started = False
            st.rerun()
            
        st.markdown("## ⚙️ Translation Settings")

        target_lang_name = st.selectbox(
            "🎯 Target Language",
            [k for k in LANGUAGES.keys() if k != 'Auto Detect'],
            index=0
        )
        target_lang = LANGUAGES[target_lang_name]

        source_lang_name = st.selectbox(
            "🔍 Source Language",
            list(LANGUAGES.keys()),
            index=0
        )
        source_lang = LANGUAGES[source_lang_name]

        st.markdown("---")
        engine_choice = st.selectbox(
            "🤖 Translation Engine",
            ['Google Translate (Free)', 'MyMemory (Free)']
        )
        
        st.markdown("---")
        st.markdown("### 📂 Supported Formats")
        format_groups = {
            "📄 Documents": [".docx", ".pdf", ".txt", ".rtf", ".md"],
            "📊 Spreadsheets": [".xlsx", ".xls", ".csv"],
            "📑 Presentations": [".pptx"],
            "🖼️ Images (OCR)": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
            "🎬 Subtitles": [".srt", ".vtt"],
            "🔧 Data / Web": [".json", ".xml", ".html"],
        }
        for group, exts in format_groups.items():
            st.markdown(f"**{group}**  \n<small style='color:#9090b0;'>{', '.join(exts)}</small>", unsafe_allow_html=True)

    # ─── File Upload ───────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "📁 Choose a file to translate",
        type=None,
        help=f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
    )

    if uploaded_file is not None:
        file_ext = Path(uploaded_file.name).suffix.lower()

        if file_ext not in SUPPORTED_EXTENSIONS:
            st.error(f"❌ Unsupported file format: `{file_ext}`")
            return

        if 'uploaded_filename' not in st.session_state or st.session_state.uploaded_filename != uploaded_file.name:
            st.session_state.uploaded_filename = uploaded_file.name
            st.session_state.translation_done = False
            st.session_state.translated_bytes = None

        # ─── File Info Display ─────────────────────────────────────
        icon = FILE_TYPE_ICONS.get(file_ext, '📁')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"{icon} **File**: `{uploaded_file.name}`")
        with col2:
            st.info(f"📏 **Size**: {format_file_size(uploaded_file.size)}")
        with col3:
            st.info(f"🔧 **Format**: {file_ext.upper()}")

        # ─── Translate Button ──────────────────────────────────────
        if st.button("🚀 Translate Now", type="primary", use_container_width=True):
            engine_type = 'google' if 'Google' in engine_choice else 'mymemory'

            try:
                translator = TranslationEngine(
                    engine=engine_type,
                    source_lang=source_lang,
                    target_lang=target_lang
                )
            except Exception as e:
                st.error(f"Failed to initialize translator: {e}")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_input:
                tmp_input.write(uploaded_file.getvalue())
                input_path = tmp_input.name

            target_ext = ".docx" if file_ext == ".pdf" else file_ext
            output_path = input_path.replace(file_ext, f"_translated{target_ext}")

            try:
                handler = get_handler(file_ext)
                if handler is None:
                    st.error(f"No handler available for `{file_ext}` files.")
                    return

                progress_bar = st.progress(0, text="Starting translation...")
                status_text = st.empty()

                def update_progress(progress, message):
                    progress_bar.progress(int(progress * 100))
                    status_text.text(message)

                start_time = time.time()

                with st.spinner("🔄 Translating your file... please wait"):
                    handler.translate(
                        input_path=input_path,
                        output_path=output_path,
                        translator=translator,
                        progress_callback=update_progress
                    )

                elapsed = time.time() - start_time
                progress_bar.progress(100)
                status_text.text(f"✅ Translation completed in {elapsed:.1f}s!")

                with open(output_path, 'rb') as f:
                    st.session_state.translated_bytes = f.read()

                st.session_state.target_ext = target_ext
                st.session_state.default_name = f"{Path(uploaded_file.name).stem}_{target_lang}{target_ext}"
                st.session_state.elapsed = elapsed
                st.session_state.engine_choice = engine_choice
                st.session_state.target_lang_name = target_lang_name
                st.session_state.translation_done = True
                st.balloons()

            except Exception as e:
                st.error(f"❌ Translation failed: {str(e)}")
            finally:
                for path in [input_path, output_path]:
                    try:
                        if os.path.exists(path):
                            os.unlink(path)
                    except OSError:
                        pass

        # ─── Display Download UI ───────────────────────────────────
        if st.session_state.get('translation_done', False):
            st.markdown("---")
            st.markdown("### 🎉 Translation Complete!")

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.metric("Original Size", format_file_size(uploaded_file.size))
            with col_dl2:
                st.metric("Translated Size", format_file_size(len(st.session_state.translated_bytes)))

            st.markdown("#### 💾 Specify Download Filename")
            
            custom_filename = st.text_input(
                "Type the filename you want to save as:",
                value=st.session_state.default_name,
                key="custom_name_input",
                help="You can change this filename before clicking download."
            )

            custom_filename = (custom_filename or st.session_state.default_name).strip()
            for ch in r'\/:*?"<>|':
                custom_filename = custom_filename.replace(ch, "_")

            target_ext = st.session_state.target_ext
            if not custom_filename.lower().endswith(target_ext.lower()):
                custom_filename = str(Path(custom_filename).stem) + target_ext

            st.download_button(
                label=f"📥 Download File as: {custom_filename}",
                data=st.session_state.translated_bytes,
                file_name=custom_filename,
                mime="application/octet-stream",
                use_container_width=True
            )

            st.caption(
                f"⏱️ Time: {st.session_state.elapsed:.1f}s | "
                f"Engine: {st.session_state.engine_choice} | "
                f"Target: {st.session_state.target_lang_name}"
            )

def main():
    load_global_css()

    if 'app_started' not in st.session_state:
        st.session_state.app_started = False

    if not st.session_state.app_started:
        show_landing_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main()

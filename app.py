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
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Animated background */
    .stApp {
        background: linear-gradient(-45deg, #0f0c29, #302b63, #24243e, #1a1a2e);
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

    /* Other standard stylings */
    h1.app-title {
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 3rem !important;
        text-align: center;
    }
    .subtitle {
        text-align: center;
        color: #b0b0d0;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }
    div[data-testid="stAlert"] {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(123, 47, 247, 0.3) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px);
        color: #e0e0f0 !important;
    }
    .stDownloadButton > button {
        background: linear-gradient(90deg, #11998e, #38ef7d) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.5rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4) !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 25px rgba(56, 239, 125, 0.6) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.04);
        border: 2px dashed #7b2ff7;
        border-radius: 18px;
        padding: 25px;
        transition: all 0.3s ease;
    }
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.6);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(123, 47, 247, 0.2);
    }
    p, li, label, .stMarkdown {
        color: #d0d0e8;
    }
    </style>
    """, unsafe_allow_html=True)


def show_landing_page():
    """Displays the animated welcome screen."""
    
    # CSS specifically to hide the sidebar and top header on the landing page
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none; }
    [data-testid="collapsedControl"] { display: none; }
    header { display: none; }
    
    .landing-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 75vh;
        text-align: center;
        animation: fadeIn 2s ease-in-out;
    }
    
    .landing-title {
        font-size: 5.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
        line-height: 1.2;
        animation: float 4s ease-in-out infinite;
    }
    
    .landing-subtitle {
        font-size: 1.5rem;
        color: #d0d0e8;
        margin-top: 15px;
        margin-bottom: 50px;
        font-weight: 300;
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
        100% { transform: translateY(0px); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    </style>
    
    <div class="landing-container">
        <h1 class="landing-title">🌐 Universal File Translator</h1>
        <p class="landing-subtitle">Break language barriers instantly. Fast, accurate, and preserves your formatting.</p>
    </div>
    """, unsafe_allow_html=True)

    # Center the Let's Go button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🚀 Let's Go", use_container_width=True):
            st.session_state.app_started = True
            st.rerun()


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
        # Back to Home Button
        if st.button("🏠 Back to Home"):
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

        # Reset session state if a new file is uploaded
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

                # Store translated file and metadata in Session State
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

        # ─── Display Download UI (Persists across user typing) ─────
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

            # Clean and sanitize the filename
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
    # Load the basic styling for the app
    load_global_css()

    # Initialize the app state
    if 'app_started' not in st.session_state:
        st.session_state.app_started = False

    # Route to the correct screen based on the state
    if not st.session_state.app_started:
        show_landing_page()
    else:
        show_main_app()

if __name__ == "__main__":
    main()

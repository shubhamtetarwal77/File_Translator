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

# ─── Page Configuration ────────────────────────────────────────────
st.set_page_config(
    page_title="Universal File Translator",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'About': "Universal File Translator v2.0"}
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


def main():
    # ====================== MODERN COOL CSS ======================
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            color: #e0e0ff;
        }
        .main-header {
            font-size: 3.5rem;
            font-weight: 800;
            background: linear-gradient(90deg, #00ffea, #7b68ff, #ff00cc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.3rem;
            text-shadow: 0 0 30px rgba(123, 104, 255, 0.5);
        }
        .sub-header {
            text-align: center;
            color: #b0b0ff;
            font-size: 1.35rem;
            margin-bottom: 2rem;
            opacity: 0.85;
        }
        .stFileUploader > div {
            border: 3px dashed #00ffea;
            border-radius: 20px;
            padding: 35px 20px;
            background: rgba(0, 255, 234, 0.06);
            transition: all 0.4s ease;
        }
        .stFileUploader > div:hover {
            border-color: #7b68ff;
            background: rgba(123, 104, 255, 0.1);
            transform: translateY(-5px);
        }
        div.stButton > button {
            background: linear-gradient(90deg, #00ffea, #7b68ff);
            color: black;
            font-weight: 700;
            border-radius: 16px;
            height: 3.2em;
            font-size: 1.1rem;
            box-shadow: 0 8px 20px rgba(0, 255, 234, 0.3);
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            transform: scale(1.05);
            box-shadow: 0 12px 25px rgba(123, 104, 255, 0.4);
        }
        .success-box {
            background: linear-gradient(90deg, #00ffea20, #7b68ff20);
            border-left: 6px solid #00ffea;
            padding: 20px;
            border-radius: 12px;
            margin: 15px 0;
        }
        .metric-card {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(123, 104, 255, 0.2);
        }
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #00ffea, #7b68ff);
        }
        .sidebar .css-1d391kg {
            background: rgba(26, 26, 46, 0.95);
        }
    </style>
    """, unsafe_allow_html=True)

    # ====================== COOL HEADER ======================
    st.markdown('<h1 class="main-header">🌐 Universal File Translator</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Translate documents, images, subtitles &amp; more — instantly, in the same format</p>', unsafe_allow_html=True)
    st.divider()

    # ─── Sidebar Settings ──────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ Translation Settings")
        target_lang_name = st.selectbox(
            "🎯 Target Language",
            [k for k in LANGUAGES.keys() if k != 'Auto Detect'],
            index=0,
            help="Choose the language you want to translate INTO"
        )
        target_lang = LANGUAGES[target_lang_name]

        source_lang_name = st.selectbox(
            "🔍 Source Language",
            list(LANGUAGES.keys()),
            index=0,
            help="Choose 'Auto Detect' if you're not sure"
        )
        source_lang = LANGUAGES[source_lang_name]

        st.markdown("---")
        engine_choice = st.selectbox(
            "🤖 Translation Engine",
            ['Google Translate (Free)', 'MyMemory (Free)'],
            help="Google: up to 5K chars/request. MyMemory: up to 5K chars/request, 5K/day anon."
        )

        st.markdown("---")
        st.markdown("### 📂 Supported Formats")
        format_groups = {
            "Documents": [".docx", ".pdf", ".txt", ".rtf", ".md"],
            "Spreadsheets": [".xlsx", ".xls", ".csv"],
            "Presentations": [".pptx"],
            "Images (OCR)": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
            "Subtitles": [".srt", ".vtt"],
            "Data / Web": [".json", ".xml", ".html"],
        }
        for group, exts in format_groups.items():
            st.markdown(f"**{group}**: {', '.join(exts)}")

        st.markdown("---")
        st.markdown(
            "<small>⚡ Powered by deep-translator, PyMuPDF, python-docx & more</small>",
            unsafe_allow_html=True
        )

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
            st.info(f"✅ Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
            return

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

            output_path = input_path.replace(file_ext, f"_translated{file_ext}")

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
                    translated_data = f.read()

                output_filename = f"{Path(uploaded_file.name).stem}_{target_lang}{file_ext}"

                st.markdown("---")
                st.markdown('<div class="success-box"><h3>🎉 Translation Complete!</h3></div>', unsafe_allow_html=True)

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.metric("Original Size", format_file_size(uploaded_file.size))
                with col_dl2:
                    st.metric("Translated Size", format_file_size(len(translated_data)))

                st.download_button(
                    label=f"📥 Download Translated — {output_filename}",
                    data=translated_data,
                    file_name=output_filename,
                    mime="application/octet-stream",
                    use_container_width=True
                )

                st.caption(f"⏱️ Took {elapsed:.1f} seconds • Engine: {engine_choice} • Target: {target_lang_name}")

            except Exception as e:
                st.error(f"❌ Translation failed: {str(e)}")
                with st.expander("🔍 Error Details"):
                    st.exception(e)

            finally:
                for path in [input_path, output_path]:
                    try:
                        if os.path.exists(path):
                            os.unlink(path)
                    except OSError:
                        pass


if __name__ == "__main__":
    main()

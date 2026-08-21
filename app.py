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


def load_css():
    """Inject custom CSS for a modern, polished look."""
    st.markdown("""
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* Animated gradient background */
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

    /* Main title gradient text */
    h1 {
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 3rem !important;
        text-align: center;
    }

    /* Subtitle text */
    .subtitle {
        text-align: center;
        color: #b0b0d0;
        font-size: 1.1rem;
        margin-bottom: 1rem;
    }

    /* Glassmorphism cards for st.info */
    div[data-testid="stAlert"] {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(123, 47, 247, 0.3) !important;
        border-radius: 16px !important;
        backdrop-filter: blur(10px);
        color: #e0e0f0 !important;
    }

    /* Primary buttons */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #7b2ff7, #00d4ff);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.7rem 1.5rem;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(123, 47, 247, 0.4);
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.6);
    }

    /* Download button */
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

    /* File uploader dropzone */
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.04);
        border: 2px dashed #7b2ff7;
        border-radius: 18px;
        padding: 25px;
        transition: all 0.3s ease;
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #00d4ff;
        background: rgba(123, 47, 247, 0.08);
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.6);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(123, 47, 247, 0.2);
    }

    /* Selectboxes */
    div[data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        border: 1px solid rgba(123, 47, 247, 0.3);
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.3);
        border-radius: 16px;
        padding: 16px;
        backdrop-filter: blur(8px);
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #7b2ff7, #00d4ff);
    }

    /* Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #7b2ff7, transparent);
    }

    /* Text color fix */
    p, li, label, .stMarkdown {
        color: #d0d0e8;
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    # ─── Load Custom Styling ───────────────────────────────────────
    load_css()

    # ─── Header ────────────────────────────────────────────────────
    st.markdown("<h1>🌐 Universal File Translator</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='subtitle'>Upload any document, spreadsheet, presentation, image, or subtitle file — "
        "translate it into your preferred language and download it <b>in the exact same format</b> "
         "(<i>Note: PDFs will be converted to DOCX</i>).</p>",
         unsafe_allow_html=True
    )
    st.divider()

    # ─── Sidebar Settings ──────────────────────────────────────────
    with st.sidebar:
        st.markdown("## ⚙️ Translation Settings")

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
            "📄 Documents": [".docx", ".pdf", ".txt", ".rtf", ".md"],
            "📊 Spreadsheets": [".xlsx", ".xls", ".csv"],
            "📑 Presentations": [".pptx"],
            "🖼️ Images (OCR)": [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"],
            "🎬 Subtitles": [".srt", ".vtt"],
            "🔧 Data / Web": [".json", ".xml", ".html"],
        }
        for group, exts in format_groups.items():
            st.markdown(f"**{group}**  \n<small style='color:#9090b0;'>{', '.join(exts)}</small>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            "<small>⚡ Powered by <a href='https://github.com/nidhaloff/deep-translator'>deep-translator</a>, "
            "<a href='https://pymupdf.readthedocs.io/'>PyMuPDF</a>, "
            "<a href='https://python-docx.readthedocs.io/'>python-docx</a>, and more.</small>",
            unsafe_allow_html=True
        )
        st.markdown("<br><center><small>Made with ❤️ using Streamlit</small></center>", unsafe_allow_html=True)

    # ─── File Upload ───────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "📁 Choose a file to translate",
        type=None,
        help=f"Supported: {', '.join(SUPPORTED_EXTENSIONS)}"
    )

    if uploaded_file is not None:
        file_ext = Path(uploaded_file.name).suffix.lower()

        # Validate extension
        if file_ext not in SUPPORTED_EXTENSIONS:
            st.error(f"❌ Unsupported file format: `{file_ext}`")
            st.info(f"✅ Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}")
            return

        st.toast(f"'{uploaded_file.name}' uploaded successfully! 🎉")

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
            # Initialize translator
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

            # Save uploaded file to temp location
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_input:
                tmp_input.write(uploaded_file.getvalue())
                input_path = tmp_input.name

            # Force output extension to .docx if the input was a PDF
            target_ext = ".docx" if file_ext == ".pdf" else file_ext
            output_path = input_path.replace(file_ext, f"_translated{target_ext}")

            try:
                # Get handler
                handler = get_handler(file_ext)
                if handler is None:
                    st.error(f"No handler available for `{file_ext}` files.")
                    return

                # Progress tracking
                progress_bar = st.progress(0, text="Starting translation...")
                status_text = st.empty()

                def update_progress(progress, message):
                    progress_bar.progress(int(progress * 100))
                    status_text.text(message)

                start_time = time.time()

                with st.spinner("🔄 Translating your file... please wait"):
                    # Perform translation
                    handler.translate(
                        input_path=input_path,
                        output_path=output_path,
                        translator=translator,
                        progress_callback=update_progress
                    )

                elapsed = time.time() - start_time

                progress_bar.progress(100)
                status_text.text(f"✅ Translation completed in {elapsed:.1f}s!")

                # Read translated file
                with open(output_path, 'rb') as f:
                    translated_data = f.read()

                # Default name (PDF → .docx already handled via target_ext)
                default_name = f"{Path(uploaded_file.name).stem}_{target_lang}{target_ext}"

                st.balloons()
                st.markdown("---")
                st.markdown("### 🎉 Translation Complete!")

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.metric("Original Size", format_file_size(uploaded_file.size))
                with col_dl2:
                    st.metric("Translated Size", format_file_size(len(translated_data)))

                # ─── Custom download filename ─────────────────────────
                st.markdown("#### 💾 Choose download name")
                custom_name = st.text_input(
                    "File name (without worrying about path)",
                    value=default_name,
                    help="Change the name if you want. Extension is added automatically if missing.",
                    key="download_filename_input",
                )

                # Clean name + ensure correct extension
                custom_name = (custom_name or default_name).strip()
                # Remove illegal path characters
                for ch in r'\/:*?"<>|':
                    custom_name = custom_name.replace(ch, "_")

                if not custom_name.lower().endswith(target_ext.lower()):
                    # If user typed another extension, strip it and force correct one
                    custom_name = str(Path(custom_name).stem) + target_ext

                output_filename = custom_name

                st.download_button(
                    label=f"📥 Download — {output_filename}",
                    data=translated_data,
                    file_name=output_filename,
                    mime="application/octet-stream",
                    use_container_width=True,
                    key="download_translated_btn",
                )

                st.caption(
                    f"⏱️ Time: {elapsed:.1f}s | "
                    f"Engine: {engine_choice} | "
                    f"Target: {target_lang_name}"
                )

            except Exception as e:
                st.error(f"❌ Translation failed: {str(e)}")
                with st.expander("🔍 Error Details"):
                    st.exception(e)

            finally:
                # Cleanup temp files
                for path in [input_path, output_path]:
                    try:
                        if os.path.exists(path):
                            os.unlink(path)
                    except OSError:
                        pass


if __name__ == "__main__":
    main()

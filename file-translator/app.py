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


def main():
    # ─── Custom CSS ────────────────────────────────────────────────
    st.markdown("""
    <style>
    .stFileUploader label { font-size: 1.1rem; }
    div.stButton > button:first-child { 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; border: none; font-weight: 600;
    }
    .success-box {
        background: #d4edda; border: 1px solid #c3e6cb;
        border-radius: 8px; padding: 16px; margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # ─── Header ────────────────────────────────────────────────────
    st.title("🌐 Universal File Translator")
    st.markdown(
        "Upload any document, spreadsheet, presentation, image, or subtitle file — "
        "translate it into your preferred language and download it **in the exact same format**."
    )
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
            "<small>⚡ Powered by [deep-translator](https://github.com/nidhaloff/deep-translator), "
            "[PyMuPDF](https://pymupdf.readthedocs.io/), [python-docx](https://python-docx.readthedocs.io/), "
            "and more.</small>",
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

        # Validate extension
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

            output_path = input_path.replace(file_ext, f"_translated{file_ext}")

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

                output_filename = f"{Path(uploaded_file.name).stem}_{target_lang}{file_ext}"

                st.markdown("---")
                st.markdown("### 🎉 Translation Complete!")

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.metric("Original Size", format_file_size(uploaded_file.size))
                with col_dl2:
                    st.metric("Translated Size", format_file_size(len(translated_data)))

                st.download_button(
                    label=f"📥 Download Translated File — `{output_filename}`",
                    data=translated_data,
                    file_name=output_filename,
                    mime="application/octet-stream",
                    use_container_width=True
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
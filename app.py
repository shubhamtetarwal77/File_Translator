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

# ── Language Mapping ──────────────────────────────────────────────
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
    '.docx': '📄', '.pdf': '', '.xlsx': '📊', '.xls': '📊',
    '.csv': '📊', '.pptx': '', '.txt': '📝', '.rtf': '📝',
    '.md': '📝', '.png': '️', '.jpg': '🖼️', '.jpeg': '🖼️',
    '.bmp': '🖼️', '.tiff': '🖼️', '.tif': '️', '.webp': '🖼️',
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
    """Inject global CSS with enhanced animations."""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Poppins:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* ════════════════════════════════════════════════════════════
       ANIMATED BACKGROUND WITH PARTICLES
       ════════════════════════════════════════════════════════════ */
    .stApp {
        background: linear-gradient(-45deg, #050510, #1a1a3a, #0f0f24, #050510);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        position: relative;
        overflow: hidden;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Floating particles in background */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(123, 47, 247, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(0, 212, 255, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(255, 47, 208, 0.1) 0%, transparent 50%);
        animation: particleFloat 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }

    @keyframes particleFloat {
        0%, 100% { transform: translate(0, 0) scale(1); }
        25% { transform: translate(30px, -30px) scale(1.1); }
        50% { transform: translate(-20px, 20px) scale(0.9); }
        75% { transform: translate(20px, 30px) scale(1.05); }
    }

    /* ════════════════════════════════════════════════════════════
       BUTTONS WITH GLOW EFFECTS
       ════════════════════════════════════════════════════════════ */
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
        position: relative;
        overflow: hidden;
    }

    div.stButton > button:first-child::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s ease;
    }

    div.stButton > button:first-child:hover::before {
        left: 100%;
    }

    div.stButton > button:first-child:hover {
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.6), 0 0 20px rgba(123, 47, 247, 0.8);
    }

    /* ════════════════════════════════════════════════════════════
       TITLE WITH TYPING EFFECT
       ════════════════════════════════════════════════════════════ */
    h1.app-title {
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 3.5rem !important;
        text-align: center;
        margin-bottom: 0px;
        animation: titleGlow 3s ease-in-out infinite;
    }

    @keyframes titleGlow {
        0%, 100% { filter: drop-shadow(0 0 10px rgba(123, 47, 247, 0.5)); }
        50% { filter: drop-shadow(0 0 25px rgba(0, 212, 255, 0.8)); }
    }

    .subtitle {
        text-align: center;
        color: #b0b0d0;
        font-size: 1.2rem;
        margin-bottom: 1rem;
        animation: fadeInUp 1s ease-out;
    }

    /* ════════════════════════════════════════════════════════════
       FADE IN ANIMATIONS
       ════════════════════════════════════════════════════════════ */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes fadeInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }

    /* ════════════════════════════════════════════════════════════
       SIDEBAR STYLING
       ════════════════════════════════════════════════════════════ */
    header { display: none !important; }

    [data-testid="collapsedControl"] {
        display: none !important;
    }
    
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.6);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(123, 47, 247, 0.2);
    }

    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    /* ════════════════════════════════════════════════════════════
       DOWNLOAD BUTTON
       ════════════════════════════════════════════════════════════ */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #11998e, #38ef7d) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.5rem !important;
        box-shadow: 0 4px 15px rgba(56, 239, 125, 0.4) !important;
        transition: all 0.3s ease !important;
    }

    .stDownloadButton > button:hover {
        transform: translateY(-3px) scale(1.03);
        box-shadow: 0 8px 25px rgba(56, 239, 125, 0.6) !important;
    }

    /* ════════════════════════════════════════════════════════════
       FILE UPLOADER
       ════════════════════════════════════════════════════════════ */
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
        box-shadow: 0 0 20px rgba(123, 47, 247, 0.3);
    }

    /* ════════════════════════════════════════════════════════════
       TEXT COLORS
       ════════════════════════════════════════════════════════════ */
    p, li, label, .stMarkdown {
        color: #d0d0e8;
    }
    </style>
    """, unsafe_allow_html=True)


def show_landing_page():
    """Displays the enhanced animated landing screen."""
    
    st.markdown("""
    <style>
    /* Hide sidebar on landing page */
    [data-testid="stSidebar"] { 
        display: none !important; 
    }

    /* ════════════════════════════════════════════════════════════
       MAP WITH ENHANCED ANIMATIONS
       ════════════════════════════════════════════════════════════ */
    .map-container {
        position: relative;
        width: 100%;
        height: 550px;
        background: url('https://upload.wikimedia.org/wikipedia/commons/8/80/World_map_-_low_resolution.svg') no-repeat center center;
        background-size: contain;
        opacity: 0.9;
        margin-top: 40px;
        margin-bottom: 60px;
        filter: drop-shadow(0 0 30px rgba(0, 212, 255, 0.3));
        animation: mapPulse 8s ease-in-out infinite;
    }

    @keyframes mapPulse {
        0%, 100% { filter: drop-shadow(0 0 30px rgba(0, 212, 255, 0.3)) brightness(1); }
        50% { filter: drop-shadow(0 0 50px rgba(123, 47, 247, 0.5)) brightness(1.1); }
    }

    .floating-lang {
        position: absolute;
        font-weight: 700;
        font-size: 1.6rem;
        padding: 10px 20px;
        border-radius: 25px;
        background: rgba(15, 12, 41, 0.85);
        backdrop-filter: blur(8px);
        border: 2px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.5), inset 0 0 20px rgba(255,255,255,0.1);
        color: white;
        animation: float 6s ease-in-out infinite;
        transition: all 0.3s ease;
        cursor: default;
    }

    .floating-lang:hover {
        transform: scale(1.2) !important;
        box-shadow: 0 15px 40px 0 rgba(31, 38, 135, 0.8);
        z-index: 100;
    }

    /* Different float animations for variety */
    .lang-en { top: 25%; left: 15%; color: #00d4ff; animation: float 4s ease-in-out infinite; }
    .lang-es { top: 60%; left: 25%; color: #ff2fd0; animation: float 5s ease-in-out infinite 0.5s; }
    .lang-fr { top: 30%; left: 45%; color: #7b2ff7; animation: float 6s ease-in-out infinite 1s; }
    .lang-ar { top: 45%; left: 55%; color: #00ffcc; animation: float 4.5s ease-in-out infinite 1.5s; }
    .lang-hi { top: 45%; left: 68%; color: #ffaa00; animation: float 5.5s ease-in-out infinite 0.2s; }
    .lang-ja { top: 35%; left: 82%; color: #ff5555; animation: float 4s ease-in-out infinite 0.8s; }
    .lang-sw { top: 65%; left: 52%; color: #aaff00; animation: float 5s ease-in-out infinite 1.2s; }
    .lang-zh { top: 38%; left: 75%; color: #ff4444; animation: float 5.5s ease-in-out infinite 0.3s; }
    .lang-de { top: 28%; left: 48%; color: #ffcc00; animation: float 4.5s ease-in-out infinite 0.7s; }
    .lang-pt { top: 65%; left: 28%; color: #00ff88; animation: float 6s ease-in-out infinite 1.3s; }

    @keyframes float {
        0%, 100% { 
            transform: translateY(0px) scale(1) rotate(0deg);
            opacity: 0.95;
        }
        25% {
            transform: translateY(-25px) scale(1.08) rotate(2deg);
            opacity: 1;
        }
        50% { 
            transform: translateY(-15px) scale(1.05) rotate(-1deg);
            opacity: 0.98;
        }
        75% {
            transform: translateY(-30px) scale(1.1) rotate(1deg);
            opacity: 1;
        }
    }

    /* ════════════════════════════════════════════════════════════
       FEATURE CARDS WITH HOVER GLOW
       ════════════════════════════════════════════════════════════ */
    .feature-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(123, 47, 247, 0.3);
        border-radius: 20px;
        padding: 30px;
        height: 100%;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        position: relative;
        overflow: hidden;
        animation: fadeInUp 1s ease-out backwards;
    }

    .feature-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(123, 47, 247, 0.1), transparent);
        opacity: 0;
        transition: opacity 0.4s ease;
    }

    .feature-card:hover::before {
        opacity: 1;
    }

    .feature-card:hover {
        transform: translateY(-15px) scale(1.02);
        background: rgba(255,255,255,0.08);
        border-color: #00d4ff;
        box-shadow: 0 20px 40px rgba(0, 212, 255, 0.3), 0 0 30px rgba(123, 47, 247, 0.4);
    }

    .feature-card:nth-child(1) { animation-delay: 0.2s; }
    .feature-card:nth-child(2) { animation-delay: 0.4s; }
    .feature-card:nth-child(3) { animation-delay: 0.6s; }

    /* Icon bounce animation */
    .feature-card h1 {
        animation: iconBounce 2s ease-in-out infinite;
        display: inline-block;
    }

    .feature-card:nth-child(1) h1 { animation-delay: 0s; }
    .feature-card:nth-child(2) h1 { animation-delay: 0.3s; }
    .feature-card:nth-child(3) h1 { animation-delay: 0.6s; }

    @keyframes iconBounce {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        25% { transform: translateY(-10px) rotate(-5deg); }
        75% { transform: translateY(-5px) rotate(5deg); }
    }

    /* ════════════════════════════════════════════════════════════
       IMAGES WITH ZOOM EFFECT
       ════════════════════════════════════════════════════════════ */
    .image-container {
        border-radius: 20px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: all 0.4s ease;
        animation: scaleIn 1s ease-out backwards;
    }

    .image-container:nth-child(1) { animation-delay: 0.3s; }
    .image-container:nth-child(2) { animation-delay: 0.5s; }

    .image-container:hover {
        transform: scale(1.03);
        box-shadow: 0 20px 50px rgba(123, 47, 247, 0.4);
    }

    /* ════════════════════════════════════════════════════════════
       CALL TO ACTION BUTTON WITH PULSE
       ═══════════════════════════════════════════════════════════ */
    .cta-button {
        animation: buttonPulse 2s ease-in-out infinite;
    }

    @keyframes buttonPulse {
        0%, 100% { 
            box-shadow: 0 4px 15px rgba(123, 47, 247, 0.4);
        }
        50% { 
            box-shadow: 0 4px 25px rgba(0, 212, 255, 0.7), 0 0 30px rgba(123, 47, 247, 0.6);
        }
    }

    /* ════════════════════════════════════════════════════════════
       SECTION HEADERS
       ════════════════════════════════════════════════════════════ */
    .section-header {
        text-align: center;
        margin-bottom: 40px;
        animation: fadeInUp 1s ease-out;
        position: relative;
    }

    .section-header::after {
        content: '';
        display: block;
        width: 100px;
        height: 4px;
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0);
        margin: 20px auto 0;
        border-radius: 2px;
        animation: expandLine 1.5s ease-out;
    }

    @keyframes expandLine {
        from { width: 0; }
        to { width: 100px; }
    }

    /* ════════════════════════════════════════════════════════════
       SCROLL INDICATOR
       ════════════════════════════════════════════════════════════ */
    .scroll-indicator {
        text-align: center;
        margin: 30px 0;
        animation: bounce 2s infinite;
        opacity: 0.7;
    }

    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-15px); }
        60% { transform: translateY(-8px); }
    }

    /* ════════════════════════════════════════════════════════════
       STATS COUNTER ANIMATION
       ═══════════════════════════════════════════════════════════ */
    .stats-container {
        display: flex;
        justify-content: center;
        gap: 50px;
        margin: 40px 0;
        flex-wrap: wrap;
    }

    .stat-item {
        text-align: center;
        padding: 20px;
        background: rgba(255,255,255,0.03);
        border-radius: 15px;
        border: 1px solid rgba(123, 47, 247, 0.2);
        min-width: 150px;
        animation: fadeInUp 1s ease-out backwards;
    }

    .stat-item:nth-child(1) { animation-delay: 0.8s; }
    .stat-item:nth-child(2) { animation-delay: 1s; }
    .stat-item:nth-child(3) { animation-delay: 1.2s; }

    .stat-number {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d4ff, #7b2ff7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: block;
    }

    .stat-label {
        color: #b0b0d0;
        font-size: 1rem;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Main Hero Header with typing effect simulation
    st.markdown("""
    <div style="animation: fadeInUp 1.5s ease-out;">
        <h1 class='app-title' style='font-size: 4.5rem !important; margin-top:20px;'>
            🌐 Break Language Barriers
        </h1>
        <p class='subtitle' style='font-size: 1.3rem; max-width: 800px; margin: 20px auto;'>
            The world is connected. Your files should be too. 
            <span style="color: #00d4ff;">Translate entire documents</span>, 
            <span style="color: #7b2ff7;">spreadsheets</span>, and 
            <span style="color: #ff2fd0;">presentations</span> 
            while keeping the exact same layout.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Big Call to Action Button with pulse animation
    col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1, 1.5])
    with col_btn2:
        st.write("")
        st.markdown("""
        <style>
        .stButton > button {
            animation: buttonPulse 2s ease-in-out infinite !important;
        }
        </style>
        """, unsafe_allow_html=True)
        if st.button(" Open Translator", use_container_width=True, key="landing_cta"):
            st.session_state.app_started = True
            st.rerun()

    # Scroll indicator
    st.markdown("""
    <div class="scroll-indicator">
        <p style="color: #7b2ff7; font-size: 0.9rem;">↓ Scroll to explore ↓</p>
    </div>
    """, unsafe_allow_html=True)

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
        <div class="floating-lang lang-zh">你好 🐼</div>
        <div class="floating-lang lang-de">Hallo 🍺</div>
        <div class="floating-lang lang-pt">Olá ⚽</div>
    </div>
    """, unsafe_allow_html=True)

    # Stats Section
    st.markdown("""
    <div class="stats-container">
        <div class="stat-item">
            <span class="stat-number">100+</span>
            <span class="stat-label">Languages</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">15+</span>
            <span class="stat-label">File Formats</span>
        </div>
        <div class="stat-item">
            <span class="stat-number">100%</span>
            <span class="stat-label">Format Preserved</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # 3. Why Translation Matters
    st.markdown("""
    <h2 class="section-header" style="color: #fff; font-size: 2.5rem;">
        ✨ The Power of Understanding
    </h2>
    """, unsafe_allow_html=True)
    
    col_feat1, col_feat2, col_feat3 = st.columns(3)
    
    with col_feat1:
        st.markdown("""
        <div class="feature-card">
            <h1 style="font-size: 3.5rem; margin:0;">🌍</h1>
            <h3 style="color:#00d4ff; margin: 15px 0;">Global Business</h3>
            <p style="color:#b0b0d0; line-height: 1.6;">Seamlessly translate contracts, pitch decks, and financial spreadsheets. Expand your company's reach to international markets without breaking your document layouts.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_feat2:
        st.markdown("""
        <div class="feature-card">
            <h1 style="font-size: 3.5rem; margin:0;">🤝</h1>
            <h3 style="color:#ff2fd0; margin: 15px 0;">Deep Connections</h3>
            <p style="color:#b0b0d0; line-height: 1.6;">Translate letters, subtitle files (SRT/VTT), and images. Share stories, movies, and culture with people around the world, making the planet feel a little bit smaller.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_feat3:
        st.markdown("""
        <div class="feature-card">
            <h1 style="font-size: 3.5rem; margin:0;">🎓</h1>
            <h3 style="color:#7b2ff7; margin: 15px 0;">Limitless Learning</h3>
            <p style="color:#b0b0d0; line-height: 1.6;">Access research papers, academic PDFs, and historical texts originally written in foreign languages. Turn any PDF into a readable, localized Word document instantly.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("<br><br>", unsafe_allow_html=True)

    # 4. Images with enhanced containers
    st.markdown("<h2 class='section-header' style='color: #fff; font-size: 2.5rem;'> Connected Worldwide</h2>", unsafe_allow_html=True)
    
    col_img1, col_img2 = st.columns(2)
    with col_img1:
        st.markdown('<div class="image-container">', unsafe_allow_html=True)
        st.image(
            "https://images.unsplash.com/photo-1522071820081-009f0129c71c?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", 
            caption="Collaborate across borders.", 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
    with col_img2:
        st.markdown('<div class="image-container">', unsafe_allow_html=True)
        st.image(
            "https://images.unsplash.com/photo-1451187580459-43490279c0fa?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80", 
            caption="A connected world.", 
            use_container_width=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("<br><br>", unsafe_allow_html=True)

    # Final CTA
    st.markdown("""
    <div style="text-align: center; padding: 40px; background: rgba(255,255,255,0.03); border-radius: 20px; border: 1px solid rgba(123, 47, 247, 0.3); animation: fadeInUp 1s ease-out;">
        <h3 style="color: #fff; font-size: 2rem; margin-bottom: 20px;">Ready to Break Barriers?</h3>
        <p style="color: #b0b0d0; margin-bottom: 30px;">Join thousands of users translating documents every day</p>
    </div>
    """, unsafe_allow_html=True)


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
        if st.button("🏠 Back to Home Screen", use_container_width=True):
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
        if st.button(" Translate Now", type="primary", use_container_width=True):
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
                label=f" Download File as: {custom_filename}",
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

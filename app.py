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
    initial_sidebar_state="expanded"  # Forces sidebar to start expanded
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
    
    /* Hide top header bar */
    header { display: none !important; }

    /* ════════════════════════════════════════════════════════════
       LOCK SIDEBAR — Hide minimize button completely globally
       ════════════════════════════════════════════════════════════ */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebarCollapseButton"] { display: none !important; }
    
    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.6);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(123, 47, 247, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)


def show_landing_page():
    """Displays an advanced animated landing screen."""
    st.markdown("""
    <style>
    /* Hide sidebar ONLY on landing page */
    [data-testid="stSidebar"] { display: none !important; }

    /* Landing page full width */
    .main .block-container {
        max-width: 100% !important;
        padding-top: 2rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }

    /* Floating animated background particles */
    .landing-bg {
        position: fixed;
        inset: 0;
        overflow: hidden;
        pointer-events: none;
        z-index: 0;
    }

    .particle {
        position: absolute;
        width: 8px;
        height: 8px;
        background: rgba(0, 212, 255, 0.7);
        border-radius: 50%;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.9);
        animation: floatParticle 12s linear infinite;
    }

    .particle:nth-child(1) { left: 10%; animation-delay: 0s; animation-duration: 13s; }
    .particle:nth-child(2) { left: 20%; animation-delay: 2s; animation-duration: 16s; }
    .particle:nth-child(3) { left: 30%; animation-delay: 4s; animation-duration: 11s; }
    .particle:nth-child(4) { left: 45%; animation-delay: 1s; animation-duration: 15s; }
    .particle:nth-child(5) { left: 60%; animation-delay: 3s; animation-duration: 12s; }
    .particle:nth-child(6) { left: 72%; animation-delay: 5s; animation-duration: 17s; }
    .particle:nth-child(7) { left: 85%; animation-delay: 2.5s; animation-duration: 14s; }

    @keyframes floatParticle {
        0% { top: 110%; opacity: 0; transform: translateX(0) scale(0.8); }
        15% { opacity: 1; }
        50% { transform: translateX(60px) scale(1.2); }
        100% { top: -10%; opacity: 0; transform: translateX(-60px) scale(0.6); }
    }

    /* Hero Section */
    .hero-section {
        position: relative;
        z-index: 2;
        min-height: 78vh;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 3rem 1rem 1rem 1rem;
    }

    .hero-glow {
        position: absolute;
        width: 420px;
        height: 420px;
        background: radial-gradient(circle, rgba(123,47,247,0.45), transparent 65%);
        filter: blur(20px);
        animation: pulseGlow 5s ease-in-out infinite;
        z-index: -1;
    }

    @keyframes pulseGlow {
        0%, 100% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.2); opacity: 1; }
    }

    .hero-kicker {
        display: inline-block;
        padding: 10px 22px;
        border-radius: 999px;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(0,212,255,0.35);
        color: #00d4ff;
        font-weight: 700;
        letter-spacing: 1px;
        margin-bottom: 18px;
        animation: fadeSlideDown 1s ease forwards;
    }

    .hero-title {
        font-size: clamp(3rem, 8vw, 6.5rem);
        line-height: 1.05;
        margin: 0;
        font-weight: 900;
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0, #00d4ff);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientMove 5s ease infinite, fadeSlideUp 1.2s ease forwards;
    }

    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .hero-subtitle {
        max-width: 900px;
        margin: 24px auto 18px auto;
        font-size: 1.35rem;
        color: #d4d4f5;
        line-height: 1.7;
        animation: fadeIn 1.8s ease forwards;
    }

    .hero-highlight { color: #00d4ff; font-weight: 700; }

    @keyframes fadeSlideUp {
        from { opacity: 0; transform: translateY(35px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeSlideDown {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    /* Scroll cue */
    .scroll-cue {
        margin-top: 30px;
        color: #9090b0;
        font-size: 0.95rem;
        animation: bounce 2s infinite;
    }

    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(10px); }
    }

    /* Language marquee */
    .language-ribbon {
        position: relative;
        z-index: 2;
        overflow: hidden;
        white-space: nowrap;
        margin: 20px 0 50px 0;
        padding: 16px 0;
        border-top: 1px solid rgba(255,255,255,0.08);
        border-bottom: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
    }

    .ribbon-track {
        display: inline-block;
        animation: marquee 28s linear infinite;
    }

    .ribbon-track span {
        display: inline-block;
        margin: 0 30px;
        font-size: 1.25rem;
        font-weight: 700;
        color: #ffffff;
        opacity: 0.9;
    }

    @keyframes marquee {
        from { transform: translateX(0); }
        to { transform: translateX(-50%); }
    }

    /* Map Section */
    .map-section {
        position: relative;
        z-index: 2;
        margin-top: 20px;
        padding: 20px 0 60px 0;
    }

    .section-title {
        text-align: center;
        font-size: 2.7rem;
        color: #ffffff;
        margin-bottom: 10px;
    }

    .section-subtitle {
        text-align: center;
        color: #b0b0d0;
        font-size: 1.1rem;
        max-width: 850px;
        margin: 0 auto 35px auto;
        line-height: 1.7;
    }

    .map-container {
        position: relative;
        width: 100%;
        height: 560px;
        background: url('https://upload.wikimedia.org/wikipedia/commons/8/80/World_map_-_low_resolution.svg') no-repeat center center;
        background-size: contain;
        opacity: 0.95;
        margin-top: 20px;
        margin-bottom: 30px;
        filter: drop-shadow(0 0 35px rgba(0, 212, 255, 0.25));
    }

    .map-container::before {
        content: "";
        position: absolute;
        inset: 8%;
        border: 1px solid rgba(0, 212, 255, 0.25);
        border-radius: 50%;
        animation: rotateRing 18s linear infinite;
    }

    .map-container::after {
        content: "";
        position: absolute;
        inset: 14%;
        border: 1px dashed rgba(255, 47, 208, 0.25);
        border-radius: 50%;
        animation: rotateRingReverse 26s linear infinite;
    }

    @keyframes rotateRing { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes rotateRingReverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }

    .floating-lang {
        position: absolute;
        font-weight: 800;
        font-size: 1.35rem;
        padding: 9px 18px;
        border-radius: 22px;
        background: rgba(15, 12, 41, 0.82);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.22);
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.38);
        color: white;
        z-index: 5;
    }

    .floating-lang::after {
        content: "";
        position: absolute;
        left: 50%;
        bottom: -12px;
        width: 10px;
        height: 10px;
        background: currentColor;
        border-radius: 50%;
        box-shadow: 0 0 18px currentColor;
    }

    .lang-en { top: 24%; left: 15%; color: #00d4ff; animation: float 4s ease-in-out infinite; }
    .lang-es { top: 61%; left: 25%; color: #ff2fd0; animation: float 5s ease-in-out infinite 0.5s; }
    .lang-fr { top: 30%; left: 45%; color: #7b2ff7; animation: float 6s ease-in-out infinite 1s; }
    .lang-ar { top: 46%; left: 55%; color: #00ffcc; animation: float 4.5s ease-in-out infinite 1.5s; }
    .lang-hi { top: 47%; left: 68%; color: #ffaa00; animation: float 5.5s ease-in-out infinite 0.2s; }
    .lang-ja { top: 35%; left: 82%; color: #ff5555; animation: float 4s ease-in-out infinite 0.8s; }
    .lang-sw { top: 66%; left: 52%; color: #aaff00; animation: float 5s ease-in-out infinite 1.2s; }

    @keyframes float {
        0% { transform: translateY(0px) scale(1); }
        50% { transform: translateY(-20px) scale(1.06); }
        100% { transform: translateY(0px) scale(1); }
    }

    /* Animated connection lines */
    .route {
        position: absolute;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, #ff2fd0, transparent);
        opacity: 0.6;
        transform-origin: left center;
        animation: routePulse 3s ease-in-out infinite;
        z-index: 3;
    }

    .route-1 { width: 260px; top: 34%; left: 25%; transform: rotate(8deg); }
    .route-2 { width: 320px; top: 43%; left: 48%; transform: rotate(18deg); animation-delay: 0.7s; }
    .route-3 { width: 230px; top: 58%; left: 42%; transform: rotate(-22deg); animation-delay: 1.2s; }
    .route-4 { width: 270px; top: 48%; left: 18%; transform: rotate(32deg); animation-delay: 1.8s; }

    @keyframes routePulse {
        0%, 100% { opacity: 0.2; filter: blur(0); }
        50% { opacity: 1; filter: blur(1px); }
    }

    /* Cards */
    .impact-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 24px;
        margin: 50px 0;
        position: relative;
        z-index: 2;
    }

    .impact-card {
        background: rgba(255,255,255,0.045);
        border: 1px solid rgba(123, 47, 247, 0.35);
        border-radius: 22px;
        padding: 32px;
        text-align: center;
        min-height: 250px;
        transition: all 0.35s ease;
        position: relative;
        overflow: hidden;
    }

    .impact-card::before {
        content: "";
        position: absolute;
        top: -80px;
        left: -80px;
        width: 160px;
        height: 160px;
        background: radial-gradient(circle, rgba(0,212,255,0.25), transparent 65%);
        transition: 0.4s;
    }

    .impact-card:hover {
        transform: translateY(-12px) scale(1.02);
        border-color: #00d4ff;
        box-shadow: 0 18px 50px rgba(0,212,255,0.18);
        background: rgba(255,255,255,0.075);
    }

    .impact-card:hover::before { transform: scale(1.8); }

    .impact-icon {
        font-size: 3.3rem;
        margin-bottom: 12px;
        animation: iconFloat 3s ease-in-out infinite;
    }

    @keyframes iconFloat {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-8px); }
    }

    .impact-card h3 { margin: 8px 0 12px 0; font-size: 1.45rem; }
    .impact-card p { color: #b0b0d0; line-height: 1.65; font-size: 1rem; }

    /* Timeline */
    .journey {
        margin: 60px 0;
        position: relative;
        z-index: 2;
    }

    .journey-steps {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 18px;
        margin-top: 30px;
    }

    .step-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 20px;
        padding: 24px;
        text-align: center;
        transition: 0.3s ease;
    }

    .step-card:hover {
        transform: translateY(-8px);
        border-color: #ff2fd0;
        box-shadow: 0 15px 40px rgba(255,47,208,0.14);
    }

    .step-number {
        width: 42px;
        height: 42px;
        margin: 0 auto 14px auto;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, #7b2ff7, #00d4ff);
        color: white;
        font-weight: 800;
    }

    .step-card h4 { color: white; margin-bottom: 8px; }
    .step-card p { color: #b0b0d0; font-size: 0.95rem; line-height: 1.55; }

    /* Photo storytelling */
    .photo-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 26px;
        margin: 50px 0;
        position: relative;
        z-index: 2;
    }

    .photo-card {
        position: relative;
        min-height: 330px;
        border-radius: 26px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.15);
        background-size: cover;
        background-position: center;
        transition: 0.45s ease;
    }

    .photo-card:hover {
        transform: scale(1.025);
        box-shadow: 0 22px 60px rgba(0,0,0,0.45);
    }

    .photo-card::before {
        content: "";
        position: absolute;
        inset: 0;
        background: linear-gradient(180deg, transparent, rgba(0,0,0,0.78));
    }

    .photo-content { position: absolute; left: 28px; right: 28px; bottom: 28px; }
    .photo-content h3 { color: white; font-size: 1.7rem; margin-bottom: 8px; }
    .photo-content p { color: #d6d6ec; line-height: 1.55; }

    .photo-1 { background-image: url('https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80'); }
    .photo-2 { background-image: url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80'); }

    /* Final CTA */
    .final-cta {
        text-align: center;
        padding: 60px 20px 25px 20px;
        position: relative;
        z-index: 2;
    }

    .final-cta h2 { color: white; font-size: 2.7rem; margin-bottom: 12px; }
    .final-cta p {
        color: #b0b0d0;
        font-size: 1.15rem;
        max-width: 750px;
        margin: 0 auto 25px auto;
        line-height: 1.7;
    }

    /* Responsive */
    @media (max-width: 900px) {
        .impact-grid, .journey-steps, .photo-grid { grid-template-columns: 1fr; }
        .map-container { height: 420px; }
        .floating-lang { font-size: 0.95rem; padding: 7px 12px; }
        .route { display: none; }
        .hero-subtitle { font-size: 1.05rem; }
    }
    </style>
    """, unsafe_allow_html=True)

    # Animated particles
    st.markdown("""
    <div class="landing-bg">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>
    """, unsafe_allow_html=True)

    # Hero
    st.markdown("""
    <section class="hero-section">
        <div class="hero-glow"></div>
        <div>
            <div class="hero-kicker">🌐 AI-Powered Universal File Translation</div>
            <h1 class="hero-title">Every Language<br>Every File<br>One World</h1>
            <p class="hero-subtitle">
                Translation is not just changing words. It helps people do business, learn, travel,
                share culture, understand research, and connect across borders.
                Upload your files and turn them into a language your audience understands —
                while keeping the <span class="hero-highlight">formatting, structure, and meaning</span>.
            </p>
            <div class="scroll-cue">Scroll to explore ↓</div>
        </div>
    </section>
    """, unsafe_allow_html=True)

    # Top CTA button
    col_btn1, col_btn2, col_btn3 = st.columns([1.5, 1, 1.5])
    with col_btn2:
        if st.button("🚀 Start Translating", use_container_width=True, key="landing_start_top"):
            st.session_state.app_started = True
            st.rerun()

    # Language ribbon
    st.markdown("""
    <div class="language-ribbon">
        <div class="ribbon-track">
            <span>Hello</span><span>Hola</span><span>Bonjour</span><span>नमस्ते</span><span>مرحبا</span>
            <span>こんにちは</span><span>안녕하세요</span><span>Ciao</span><span>Hallo</span><span>Olá</span>
            <span>Привет</span><span>你好</span><span>Jambo</span><span>Merhaba</span><span>שלום</span>
            <span>Hello</span><span>Hola</span><span>Bonjour</span><span>नमस्ते</span><span>مرحبا</span>
            <span>こんにちは</span><span>안녕하세요</span><span>Ciao</span><span>Hallo</span><span>Olá</span>
            <span>Привет</span><span>你好</span><span>Jambo</span><span>Merhaba</span><span>שלום</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Map section
    st.markdown("""
    <section class="map-section">
        <h2 class="section-title">Languages Move the World</h2>
        <p class="section-subtitle">
            From a student reading foreign research, to a company sending proposals overseas,
            to subtitles making stories accessible — translation connects people who would otherwise stay apart.
        </p>

        <div class="map-container">
            <div class="route route-1"></div>
            <div class="route route-2"></div>
            <div class="route route-3"></div>
            <div class="route route-4"></div>

            <div class="floating-lang lang-en">Hello 👋</div>
            <div class="floating-lang lang-es">Hola 💃</div>
            <div class="floating-lang lang-fr">Bonjour 🥐</div>
            <div class="floating-lang lang-ar">مرحباً 🕌</div>
            <div class="floating-lang lang-hi">नमस्ते 🪷</div>
            <div class="floating-lang lang-ja">こんにちは 🌸</div>
            <div class="floating-lang lang-sw">Jambo 🌍</div>
        </div>
    </section>
    """, unsafe_allow_html=True)

    # Impact cards
    st.markdown("""
    <div class="impact-grid">
        <div class="impact-card">
            <div class="impact-icon">🌍</div>
            <h3 style="color:#00d4ff;">Global Business</h3>
            <p>
                Translate contracts, reports, spreadsheets, and pitch decks.
                Reach new markets without recreating your documents from scratch.
            </p>
        </div>

        <div class="impact-card">
            <div class="impact-icon">🤝</div>
            <h3 style="color:#ff2fd0;">Human Connection</h3>
            <p>
                Letters, images, subtitles, and documents become accessible to people
                who speak different languages but share the same ideas.
            </p>
        </div>

        <div class="impact-card">
            <div class="impact-icon">🎓</div>
            <h3 style="color:#7b2ff7;">Limitless Learning</h3>
            <p>
                Research papers, PDFs, notes, and academic material can be understood
                by students and professionals around the world.
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Journey / process
    st.markdown("""
    <section class="journey">
        <h2 class="section-title">From File to Understanding</h2>
        <p class="section-subtitle">
            Your document goes through a simple journey — upload, detect, translate, and download.
        </p>

        <div class="journey-steps">
            <div class="step-card">
                <div class="step-number">1</div>
                <h4>Upload</h4>
                <p>Choose DOCX, PDF, PPTX, Excel, CSV, images, subtitles, JSON, XML, HTML, or text files.</p>
            </div>

            <div class="step-card">
                <div class="step-number">2</div>
                <h4>Understand</h4>
                <p>The app reads your file content while preserving the original document structure.</p>
            </div>

            <div class="step-card">
                <div class="step-number">3</div>
                <h4>Translate</h4>
                <p>Your content is translated into the selected target language using your chosen engine.</p>
            </div>

            <div class="step-card">
                <div class="step-number">4</div>
                <h4>Download</h4>
                <p>Download the translated file with your desired filename. PDFs are converted to DOCX.</p>
            </div>
        </div>
    </section>
    """, unsafe_allow_html=True)

    # Photo story cards
    st.markdown("""
    <div class="photo-grid">
        <div class="photo-card photo-1">
            <div class="photo-content">
                <h3>Teams Without Borders</h3>
                <p>
                    Translate proposals, presentations, and reports so global teams can work together clearly.
                </p>
            </div>
        </div>

        <div class="photo-card photo-2">
            <div class="photo-content">
                <h3>A Connected Planet</h3>
                <p>
                    Knowledge should not stop at language barriers. Make every document readable to more people.
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Final CTA
    st.markdown("""
    <div class="final-cta">
        <h2>Ready to Translate Your World?</h2>
        <p>
            Start with one file. Translate it into another language. Share it with someone new.
            That is how communication becomes connection.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_bottom1, col_bottom2, col_bottom3 = st.columns([1.5, 1, 1.5])
    with col_bottom2:
        if st.button("🌐 Open File Translator", use_container_width=True, key="landing_start_bottom"):
            st.session_state.app_started = True
            st.rerun()

    st.write("<br><br>", unsafe_allow_html=True)


def show_main_app():
    """Displays the main translation tool."""
    
    # Force sidebar open on this page
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: block !important;
        visibility: visible !important;
        min-width: 21rem !important;
        max-width: 21rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
                    # Fixed crash bug here with min()
                    progress_bar.progress(min(int(progress * 100), 100))
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

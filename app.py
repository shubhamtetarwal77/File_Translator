"""
Universal File Translator - Main Streamlit Application
Upload any file → Translate → Download in same format
"""

import streamlit as st
import streamlit.components.v1 as components
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
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def load_global_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

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

    div.stButton > button:first-child {
        background: linear-gradient(90deg, #7b2ff7, #00d4ff) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        box-shadow: 0 4px 15px rgba(123, 47, 247, 0.4) !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.55) !important;
    }

    h1.app-title {
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800 !important;
        font-size: 3.2rem !important;
        text-align: center;
    }
    .subtitle {
        text-align: center;
        color: #b0b0d0;
        font-size: 1.1rem;
    }

    header { display: none !important; }

    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }

    section[data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.75);
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(123, 47, 247, 0.25);
    }

    .stDownloadButton > button {
        background: linear-gradient(90deg, #11998e, #38ef7d) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255,255,255,0.04);
        border: 2px dashed #7b2ff7;
        border-radius: 18px;
    }

    iframe {
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)


def show_landing_page():
    """Landing page rendered via components.html so animations actually display."""

    # Hide sidebar on landing only
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }
    .main .block-container {
        max-width: 100% !important;
        padding-top: 1rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    landing_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8" />
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800;900&display=swap" rel="stylesheet">
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: 'Poppins', sans-serif;
        background: transparent;
        color: #fff;
        overflow-x: hidden;
      }

      .wrap { width: 100%; padding: 10px 8px 30px 8px; }

      /* particles */
      .particles { position: relative; height: 0; }
      .particle {
        position: fixed;
        width: 7px; height: 7px;
        border-radius: 50%;
        background: rgba(0,212,255,0.75);
        box-shadow: 0 0 16px rgba(0,212,255,0.9);
        animation: rise 14s linear infinite;
        z-index: 0;
      }
      .p1 { left: 8%; animation-delay: 0s; }
      .p2 { left: 22%; animation-delay: 2s; animation-duration: 16s; }
      .p3 { left: 38%; animation-delay: 4s; animation-duration: 12s; }
      .p4 { left: 55%; animation-delay: 1s; animation-duration: 15s; }
      .p5 { left: 70%; animation-delay: 3s; animation-duration: 13s; }
      .p6 { left: 85%; animation-delay: 5s; animation-duration: 17s; }
      @keyframes rise {
        0% { top: 105%; opacity: 0; transform: translateX(0); }
        20% { opacity: 1; }
        100% { top: -10%; opacity: 0; transform: translateX(40px); }
      }

      /* hero */
      .hero {
        position: relative;
        z-index: 2;
        text-align: center;
        padding: 40px 16px 20px 16px;
        min-height: 420px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }
      .glow {
        position: absolute;
        width: 380px; height: 380px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(123,47,247,0.45), transparent 70%);
        filter: blur(18px);
        animation: pulse 5s ease-in-out infinite;
        z-index: -1;
      }
      @keyframes pulse {
        0%,100% { transform: scale(1); opacity: 0.7; }
        50% { transform: scale(1.18); opacity: 1; }
      }
      .kicker {
        display: inline-block;
        padding: 10px 18px;
        border-radius: 999px;
        border: 1px solid rgba(0,212,255,0.4);
        background: rgba(255,255,255,0.06);
        color: #00d4ff;
        font-weight: 700;
        margin-bottom: 18px;
        animation: fadeDown 1s ease both;
      }
      .title {
        margin: 0;
        font-size: clamp(2.6rem, 7vw, 5.6rem);
        line-height: 1.05;
        font-weight: 900;
        background: linear-gradient(90deg, #00d4ff, #7b2ff7, #ff2fd0, #00d4ff);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: grad 5s ease infinite, fadeUp 1.1s ease both;
      }
      @keyframes grad {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
      }
      .subtitle {
        max-width: 880px;
        margin: 20px auto 0 auto;
        color: #d4d4f5;
        font-size: 1.15rem;
        line-height: 1.7;
        animation: fadeIn 1.5s ease both;
      }
      .highlight { color: #00d4ff; font-weight: 700; }
      .scroll {
        margin-top: 22px;
        color: #9090b0;
        animation: bounce 2s infinite;
      }
      @keyframes bounce {
        0%,100% { transform: translateY(0); }
        50% { transform: translateY(8px); }
      }
      @keyframes fadeUp {
        from { opacity: 0; transform: translateY(28px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes fadeDown {
        from { opacity: 0; transform: translateY(-18px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

      /* ribbon */
      .ribbon {
        margin: 24px 0 36px 0;
        padding: 14px 0;
        overflow: hidden;
        white-space: nowrap;
        border-top: 1px solid rgba(255,255,255,0.08);
        border-bottom: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        position: relative;
        z-index: 2;
      }
      .track {
        display: inline-block;
        animation: marquee 28s linear infinite;
      }
      .track span {
        display: inline-block;
        margin: 0 28px;
        font-weight: 700;
        font-size: 1.15rem;
      }
      @keyframes marquee {
        from { transform: translateX(0); }
        to { transform: translateX(-50%); }
      }

      /* sections */
      .section {
        position: relative;
        z-index: 2;
        padding: 18px 8px 34px 8px;
        text-align: center;
      }
      .section h2 {
        margin: 0 0 10px 0;
        font-size: 2.3rem;
      }
      .section p.lead {
        max-width: 820px;
        margin: 0 auto 28px auto;
        color: #b0b0d0;
        line-height: 1.7;
        font-size: 1.05rem;
      }

      /* map */
      .map-box {
        position: relative;
        width: 100%;
        height: 520px;
        margin: 0 auto;
        background: url('https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/World_map_-_low_resolution.svg/1280px-World_map_-_low_resolution.svg.png') no-repeat center center;
        background-size: contain;
        filter: drop-shadow(0 0 28px rgba(0,212,255,0.25));
      }
      .map-box:before, .map-box:after {
        content: "";
        position: absolute;
        border-radius: 50%;
        pointer-events: none;
      }
      .map-box:before {
        inset: 8%;
        border: 1px solid rgba(0,212,255,0.28);
        animation: spin 18s linear infinite;
      }
      .map-box:after {
        inset: 14%;
        border: 1px dashed rgba(255,47,208,0.28);
        animation: spinrev 26s linear infinite;
      }
      @keyframes spin { from { transform: rotate(0deg);} to { transform: rotate(360deg);} }
      @keyframes spinrev { from { transform: rotate(360deg);} to { transform: rotate(0deg);} }

      .bubble {
        position: absolute;
        z-index: 5;
        font-weight: 800;
        font-size: 1.15rem;
        padding: 8px 14px;
        border-radius: 18px;
        background: rgba(15,12,41,0.88);
        border: 1px solid rgba(255,255,255,0.22);
        box-shadow: 0 8px 24px rgba(0,0,0,0.35);
        animation: float 4.5s ease-in-out infinite;
      }
      .bubble:after {
        content: "";
        position: absolute;
        left: 50%;
        bottom: -10px;
        width: 8px; height: 8px;
        border-radius: 50%;
        background: currentColor;
        box-shadow: 0 0 12px currentColor;
        transform: translateX(-50%);
      }
      .b-en { top: 22%; left: 14%; color: #00d4ff; }
      .b-es { top: 60%; left: 24%; color: #ff2fd0; animation-delay: .4s; }
      .b-fr { top: 28%; left: 44%; color: #b07bff; animation-delay: .8s; }
      .b-ar { top: 44%; left: 54%; color: #00ffcc; animation-delay: 1.1s; }
      .b-hi { top: 46%; left: 67%; color: #ffaa00; animation-delay: .2s; }
      .b-ja { top: 33%; left: 80%; color: #ff6b6b; animation-delay: .6s; }
      .b-sw { top: 64%; left: 51%; color: #b6ff3b; animation-delay: 1.3s; }
      @keyframes float {
        0%,100% { transform: translateY(0); }
        50% { transform: translateY(-14px); }
      }

      .route {
        position: absolute;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00d4ff, #ff2fd0, transparent);
        opacity: .55;
        animation: routePulse 3s ease-in-out infinite;
        z-index: 3;
      }
      .r1 { width: 240px; top: 34%; left: 24%; transform: rotate(8deg); }
      .r2 { width: 300px; top: 42%; left: 47%; transform: rotate(16deg); animation-delay: .7s; }
      .r3 { width: 220px; top: 57%; left: 41%; transform: rotate(-20deg); animation-delay: 1.2s; }
      @keyframes routePulse {
        0%,100% { opacity: .15; }
        50% { opacity: .9; }
      }

      /* cards */
      .grid3 {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 18px;
        margin-top: 10px;
        text-align: left;
      }
      .card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(123,47,247,0.35);
        border-radius: 20px;
        padding: 24px;
        min-height: 220px;
        transition: .3s ease;
      }
      .card:hover {
        transform: translateY(-8px);
        border-color: #00d4ff;
        box-shadow: 0 16px 40px rgba(0,212,255,0.15);
      }
      .card .icon { font-size: 2.6rem; margin-bottom: 8px; }
      .card h3 { margin: 6px 0 10px 0; font-size: 1.3rem; }
      .card p { margin: 0; color: #b0b0d0; line-height: 1.6; }

      .grid4 {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        margin-top: 8px;
      }
      .step {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 18px;
        padding: 18px;
        text-align: center;
        transition: .3s ease;
      }
      .step:hover {
        transform: translateY(-6px);
        border-color: #ff2fd0;
      }
      .num {
        width: 40px; height: 40px;
        margin: 0 auto 10px auto;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(135deg, #7b2ff7, #00d4ff);
        font-weight: 800;
      }
      .step h4 { margin: 0 0 8px 0; }
      .step p { margin: 0; color: #b0b0d0; font-size: 0.92rem; line-height: 1.5; }

      .photos {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 18px;
        margin-top: 10px;
      }
      .photo {
        position: relative;
        min-height: 280px;
        border-radius: 22px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.14);
        background-size: cover;
        background-position: center;
        transition: .35s ease;
      }
      .photo:hover { transform: scale(1.02); }
      .photo:before {
        content: "";
        position: absolute; inset: 0;
        background: linear-gradient(180deg, transparent, rgba(0,0,0,0.8));
      }
      .photo .txt {
        position: absolute; left: 22px; right: 22px; bottom: 22px;
        text-align: left;
      }
      .photo h3 { margin: 0 0 8px 0; font-size: 1.45rem; }
      .photo p { margin: 0; color: #d6d6ec; line-height: 1.5; }
      .ph1 { background-image: url('https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1200&q=80'); }
      .ph2 { background-image: url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=1200&q=80'); }

      .cta {
        text-align: center;
        padding: 40px 10px 10px 10px;
      }
      .cta h2 { margin: 0 0 10px 0; font-size: 2.3rem; }
      .cta p {
        max-width: 720px;
        margin: 0 auto;
        color: #b0b0d0;
        line-height: 1.7;
      }

      @media (max-width: 900px) {
        .grid3, .grid4, .photos { grid-template-columns: 1fr; }
        .map-box { height: 360px; }
        .bubble { font-size: 0.9rem; padding: 6px 10px; }
        .route { display: none; }
      }
    </style>
    </head>
    <body>
      <div class="particles">
        <div class="particle p1"></div>
        <div class="particle p2"></div>
        <div class="particle p3"></div>
        <div class="particle p4"></div>
        <div class="particle p5"></div>
        <div class="particle p6"></div>
      </div>

      <div class="wrap">
        <div class="hero">
          <div class="glow"></div>
          <div class="kicker">AI-Powered Universal File Translation</div>
          <h1 class="title">Every Language<br>Every File<br>One World</h1>
          <p class="subtitle">
            Translation is not just changing words. It helps people do business, learn, travel,
            share culture, understand research, and connect across borders.
            Upload your files and turn them into a language your audience understands —
            while keeping the <span class="highlight">formatting, structure, and meaning</span>.
          </p>
          <div class="scroll">Scroll to explore ↓</div>
        </div>

        <div class="ribbon">
          <div class="track">
            <span>Hello</span><span>Hola</span><span>Bonjour</span><span>नमस्ते</span><span>مرحبا</span>
            <span>こんにちは</span><span>안녕하세요</span><span>Ciao</span><span>Hallo</span><span>Olá</span>
            <span>Привет</span><span>你好</span><span>Jambo</span><span>Merhaba</span><span>שלום</span>
            <span>Hello</span><span>Hola</span><span>Bonjour</span><span>नमस्ते</span><span>مرحبا</span>
            <span>こんにちは</span><span>안녕하세요</span><span>Ciao</span><span>Hallo</span><span>Olá</span>
            <span>Привет</span><span>你好</span><span>Jambo</span><span>Merhaba</span><span>שלום</span>
          </div>
        </div>

        <div class="section">
          <h2>Languages Move the World</h2>
          <p class="lead">
            From a student reading foreign research, to a company sending proposals overseas,
            to subtitles making stories accessible — translation connects people who would otherwise stay apart.
          </p>

          <div class="map-box">
            <div class="route r1"></div>
            <div class="route r2"></div>
            <div class="route r3"></div>

            <div class="bubble b-en">Hello</div>
            <div class="bubble b-es">Hola</div>
            <div class="bubble b-fr">Bonjour</div>
            <div class="bubble b-ar">مرحباً</div>
            <div class="bubble b-hi">नमस्ते</div>
            <div class="bubble b-ja">こんにちは</div>
            <div class="bubble b-sw">Jambo</div>
          </div>
        </div>

        <div class="section">
          <div class="grid3">
            <div class="card">
              <div class="icon">🌍</div>
              <h3 style="color:#00d4ff;">Global Business</h3>
              <p>Translate contracts, reports, spreadsheets, and pitch decks. Reach new markets without recreating your documents from scratch.</p>
            </div>
            <div class="card">
              <div class="icon">🤝</div>
              <h3 style="color:#ff2fd0;">Human Connection</h3>
              <p>Letters, images, subtitles, and documents become accessible to people who speak different languages but share the same ideas.</p>
            </div>
            <div class="card">
              <div class="icon">🎓</div>
              <h3 style="color:#b07bff;">Limitless Learning</h3>
              <p>Research papers, PDFs, notes, and academic material can be understood by students and professionals around the world.</p>
            </div>
          </div>
        </div>

        <div class="section">
          <h2>From File to Understanding</h2>
          <p class="lead">Your document goes through a simple journey — upload, understand, translate, and download.</p>
          <div class="grid4">
            <div class="step">
              <div class="num">1</div>
              <h4>Upload</h4>
              <p>DOCX, PDF, PPTX, Excel, CSV, images, subtitles, JSON, XML, HTML, or text.</p>
            </div>
            <div class="step">
              <div class="num">2</div>
              <h4>Understand</h4>
              <p>The app reads content while preserving original document structure.</p>
            </div>
            <div class="step">
              <div class="num">3</div>
              <h4>Translate</h4>
              <p>Content is translated into your selected target language.</p>
            </div>
            <div class="step">
              <div class="num">4</div>
              <h4>Download</h4>
              <p>Save with your custom filename. PDFs become DOCX.</p>
            </div>
          </div>
        </div>

        <div class="section">
          <div class="photos">
            <div class="photo ph1">
              <div class="txt">
                <h3>Teams Without Borders</h3>
                <p>Translate proposals, presentations, and reports so global teams can work together clearly.</p>
              </div>
            </div>
            <div class="photo ph2">
              <div class="txt">
                <h3>A Connected Planet</h3>
                <p>Knowledge should not stop at language barriers. Make every document readable to more people.</p>
              </div>
            </div>
          </div>
        </div>

        <div class="cta">
          <h2>Ready to Translate Your World?</h2>
          <p>Start with one file. Translate it into another language. Share it with someone new. That is how communication becomes connection.</p>
        </div>
      </div>
    </body>
    </html>
    """

    # IMPORTANT: use components.html (not st.markdown) so HTML/CSS actually renders
    components.html(landing_html, height=3200, scrolling=True)

    # Streamlit buttons must stay outside the HTML component
    c1, c2, c3 = st.columns([1.4, 1.2, 1.4])
    with c2:
        if st.button("🚀 Start Translating", use_container_width=True, key="start_translate_btn"):
            st.session_state.app_started = True
            st.rerun()


def show_main_app():
    # Force sidebar visible on translator page
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
            st.markdown(
                f"**{group}**  \n<small style='color:#9090b0;'>{', '.join(exts)}</small>",
                unsafe_allow_html=True
            )

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

        icon = FILE_TYPE_ICONS.get(file_ext, '📁')
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"{icon} **File**: `{uploaded_file.name}`")
        with col2:
            st.info(f"📏 **Size**: {format_file_size(uploaded_file.size)}")
        with col3:
            st.info(f"🔧 **Format**: {file_ext.upper()}")

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

        if st.session_state.get('translation_done', False) and st.session_state.get('translated_bytes'):
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
                key="custom_name_input"
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

"""A quiet lab notebook palette with readable text and visible keyboard focus."""

CSS = """
<style>
.block-container {max-width: 1240px; padding-top: 2.5rem; padding-bottom: 3rem;}
[data-testid="stSidebar"] {border-right: 1px solid #34474b;}
h1 {font-size: 3.7rem !important; letter-spacing: -0.065em; line-height: 1.05 !important;}
[data-testid="stSidebar"] h1 {font-size:1.7rem !important; letter-spacing:-.04em;}
h2 {letter-spacing: -0.035em;}
h3 {letter-spacing: -0.02em;}
p, label, li {line-height: 1.65;}
.eyebrow {color: #a6f4c5; font: 600 .75rem monospace; letter-spacing: .16em; margin-bottom: 1rem;}
.hero-copy {color: #c5d2ce; max-width: 620px; font-size: 1.1rem; margin-bottom: 1.8rem;}
.lab-mark {display:inline-block; padding:8px 12px; border:1px solid #719b86;
 border-radius:6px; font:600 14px monospace; color:#a6f4c5; margin-bottom:16px;}
.note {border-left: 3px solid #e4bf79; padding: 12px 18px; background:#242a28;
 color:#f1dfbc; border-radius:0 8px 8px 0; margin:12px 0 20px;}
.run-label {color:#bfcec8; font:12px monospace; letter-spacing:.05em;}
[data-testid="stMetric"] {background:#1b272b; border:1px solid #3c5054;
 padding:18px; border-radius:12px; min-height:110px;}
[data-testid="stMetricLabel"] {color:#c5d2ce;}
[data-testid="stMetricValue"] {font-family:monospace; color:#f2f6f3;}
button, input, textarea {transition: border-color .15s;}
button[kind="primary"], button[kind="primary"] p {color:#101719 !important; font-weight:650;}
textarea:disabled {-webkit-text-fill-color:#d9e5df !important; color:#d9e5df !important;}
button:focus-visible, input:focus-visible, textarea:focus-visible {
 outline: 3px solid #e4bf79 !important; outline-offset: 3px;}
[data-testid="stCaptionContainer"] {color:#c5d2ce; opacity:1 !important;}
[data-testid="stCaptionContainer"] p {color:#c5d2ce !important;}
[data-testid="stWidgetLabel"] p {color:#d9e5df !important;}
@media(max-width:700px) {h1 {font-size:2.8rem !important;} .block-container {padding-top:1.5rem;}}
</style>
"""

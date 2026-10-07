#!/usr/bin/env python3
"""
Gera assets/ascii-portrait.svg: a foto de perfil do GitHub convertida em
caracteres ASCII dentro de uma janela de terminal, com as linhas surgindo
uma a uma.

Uso: python scripts/make_ascii_svg.py [foto.png]
Sem argumento, baixa o avatar atual de github.com/Jeda-Ismael.
Funciona melhor com um PNG de fundo transparente (ex.: `rembg i foto.jpg foto.png`).
Dependências: Pillow, numpy.
"""
import io
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image, ImageFilter, ImageOps

USER = "Jeda-Ismael"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "ascii-portrait.svg")

# recorte (fração da imagem): rosto e ombros
CROP = (0.30, 0.04, 0.90, 0.62)
COLS = 130
CHAR_ASPECT = 0.55          # largura/altura de um caractere monoespaçado
RAMP = " .,:;i1tfLCG08@"    # do escuro (fundo) ao claro
LEVELS = [                  # (limite de brilho, cor)
    (0.32, "#4b2a6b"),
    (0.55, "#8a4fd0"),
    (0.78, "#c9a6f5"),
    (1.01, "#f5efff"),
]

FONT = 6.4
LINE = 7.0
CHAR_W = FONT * 0.6
PAD = 22
BAR = 30
FOOT = 34


def load(path):
    if path:
        return Image.open(path)
    url = f"https://avatars.githubusercontent.com/{USER}?s=600"
    with urllib.request.urlopen(url, timeout=30) as r:
        return Image.open(io.BytesIO(r.read()))


def to_ascii(img):
    w, h = img.size
    box = (int(CROP[0] * w), int(CROP[1] * h), int(CROP[2] * w), int(CROP[3] * h))
    img = img.convert("RGBA").crop(box)
    rows = int(COLS * img.height / img.width * CHAR_ASPECT)

    # canal alfa = recorte da pessoa (foto com fundo removido); sem ele, tudo conta
    mask = np.asarray(img.getchannel("A").resize((COLS, rows), Image.LANCZOS), dtype=float) / 255
    gray = ImageOps.autocontrast(img.convert("L"), cutoff=1).filter(ImageFilter.UnsharpMask(2, 140))
    a = np.asarray(gray.resize((COLS, rows), Image.LANCZOS), dtype=float) / 255
    # piso dentro do recorte para que cabelo e partes escuras ainda apareçam
    return np.clip(mask * (0.2 + 0.8 * a ** 0.9), 0, 1)


def svg(a):
    rows, cols = a.shape
    width = PAD * 2 + cols * CHAR_W
    height = BAR + PAD + rows * LINE + PAD + FOOT
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">',
        "<style>"
        "text{font-family:'DejaVu Sans Mono',Menlo,Consolas,monospace;white-space:pre}"
        ".r{font-size:%.1fpx;opacity:0;animation:in .4s ease-out forwards}" % FONT
        + "@keyframes in{to{opacity:1}}"
        ".cur{animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}"
        "</style>",
        f'<rect width="{width:.0f}" height="{height:.0f}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<path d="M0 {BAR}H{width:.0f}" stroke="#30363d"/>',
        '<circle cx="18" cy="15" r="5" fill="#ff5f56"/>'
        '<circle cx="34" cy="15" r="5" fill="#ffbd2e"/>'
        '<circle cx="50" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{width / 2:.0f}" y="19" text-anchor="middle" font-size="11" fill="#8b949e">'
        "jedaias@github: ~ $ ./retrato.sh</text>",
    ]
    for i, row in enumerate(a):
        yy = BAR + PAD + (i + 1) * LINE
        parts, cur, buf = [], None, ""
        for v in row:
            ch = RAMP[min(int(v * len(RAMP)), len(RAMP) - 1)]
            color = next(c for t, c in LEVELS if v < t)
            if ch == " ":
                color = cur  # espaço não muda de cor
            if color != cur and buf:
                parts.append(f'<tspan fill="{cur}">{escape(buf)}</tspan>')
                buf = ""
            cur = color
            buf += ch
        if buf.strip():
            parts.append(f'<tspan fill="{cur}">{escape(buf)}</tspan>')
        if parts:
            out.append(f'<text class="r" x="{PAD}" y="{yy:.1f}" xml:space="preserve" '
                       f'style="animation-delay:{i * 0.035:.3f}s">{"".join(parts)}</text>')
    fy = height - FOOT / 2 + 4
    out.append(f'<path d="M0 {height - FOOT:.0f}H{width:.0f}" stroke="#30363d"/>')
    out.append(f'<text x="{PAD}" y="{fy:.0f}" font-size="12" fill="#8b949e">jedaias@github:~$ '
               '<tspan fill="#c9d1d9">whoami</tspan> <tspan fill="#A020F0" font-weight="bold">'
               'Jedaías Ismael</tspan> <tspan class="cur" fill="#c9d1d9">█</tspan></text>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    art = to_ascii(load(sys.argv[1] if len(sys.argv) > 1 else None))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg(art))
    print(f"ok: {OUT} ({art.shape[1]}x{art.shape[0]})")

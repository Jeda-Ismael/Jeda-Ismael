#!/usr/bin/env python3
"""
Gera assets/banner.svg: banner do topo do README com o retrato ASCII,
o nome em mandarim (杰达亚斯) e uma linha que digita e apaga frases.

Os textos viram contornos (paths), então o banner fica igual em qualquer
sistema, sem depender das fontes de quem visita o perfil.

Uso: python scripts/make_banner_svg.py foto-sem-fundo.png
Dependências: Pillow, numpy, fonttools (+ fontes DejaVu Sans Mono e WenQuanYi Zen Hei).
"""
import os
import sys
from xml.sax.saxutils import escape

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
import make_ascii_svg as ascii_art  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "banner.svg")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
CJK = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"

W, H = 1584, 396
BG, FG, ORANGE, MUTED = "#111111", "#f4f1ec", "#ff7a18", "#6b6b6b"
NAME = "杰达亚斯"
PHRASES = [
    "Olá! Eu sou o Jedaías Ismael",
    "Analista de Soluções e Dados @ NBS TELECOM",
    "Estudante de Ciência da Computação",
    "Seja bem-vindo(a)!",
]
TYPE, ERASE, HOLD, GAP = 0.07, 0.025, 2.2, 0.5   # segundos


def text_path(font, text, size, x, y):
    """Desenha `text` como um único path; devolve (d, largura)."""
    gs, cmap = font.getGlyphSet(), font.getBestCmap()
    scale = size / font["head"].unitsPerEm
    pen = SVGPathPen(gs)
    cx = 0
    for ch in text:
        g = cmap.get(ord(ch))
        if g is None:
            continue
        gs[g].draw(TransformPen(pen, (scale, 0, 0, -scale, x + cx, y)))
        cx += gs[g].width * scale
    return pen.getCommands(), cx


def portrait(photo):
    ascii_art.CROP = (0.15, 0.04, 0.97, 0.70)   # ombros e braços inteiros
    ascii_art.COLS = 170
    a = ascii_art.to_ascii(Image.open(photo))
    rows = a.shape[0]
    a = a * np.clip((rows - 1 - np.arange(rows)) / 10, 0, 1)[:, None]  # some na base
    colors = [(0.35, "#5a2a08"), (0.6, "#b4520f"), (0.8, ORANGE), (1.01, "#ffd2a8")]
    font, line, x0 = 4.6, 5.1, 150
    y0 = H - 8 - rows * line
    out = []
    for i, row in enumerate(a):
        parts, cur, buf = [], None, ""
        for v in row:
            ch = ascii_art.RAMP[min(int(v * len(ascii_art.RAMP)), len(ascii_art.RAMP) - 1)]
            col = cur if ch == " " else next(c for t, c in colors if v < t)
            if col != cur and buf:
                parts.append(f'<tspan fill="{cur}">{escape(buf)}</tspan>')
                buf = ""
            cur, buf = col, buf + ch
        if buf.strip():
            parts.append(f'<tspan fill="{cur}">{escape(buf)}</tspan>')
        if parts:
            out.append(f'<text class="r" x="{x0}" y="{y0 + (i + 1) * line:.1f}" '
                       f'style="animation-delay:{i * 0.03:.2f}s">{"".join(parts)}</text>')
    return out


def typing(mono, x, y, size):
    adv = mono.getGlyphSet()[mono.getBestCmap()[ord("a")]].width * size / mono["head"].unitsPerEm
    spans, t = [], 0.0
    for p in PHRASES:
        n = len(p)
        spans.append((n, t, t + n * TYPE, t + n * TYPE + HOLD, t + n * TYPE + HOLD + n * ERASE))
        t += n * TYPE + HOLD + n * ERASE + GAP
    total = t
    pct = lambda s: f"{100 * s / total:.3f}%"

    css, body = [], []
    for k, (p, (n, t0, t1, t2, t3)) in enumerate(zip(PHRASES, spans)):
        w = n * adv
        d, _ = text_path(mono, p, size, x, y)
        # mesma linha do tempo para o recorte (texto) e para o cursor
        css.append(
            f"@keyframes c{k}{{0%,{pct(t0)}{{transform:scaleX(0)}}"
            f"{pct(t0)}{{animation-timing-function:steps({n},end)}}"
            f"{pct(t1)},{pct(t2)}{{transform:scaleX(1)}}"
            f"{pct(t2)}{{animation-timing-function:steps({n},end)}}"
            f"{pct(t3)},100%{{transform:scaleX(0)}}}}"
            f"@keyframes k{k}{{0%,{pct(t0)}{{transform:translateX(0)}}"
            f"{pct(t0)}{{animation-timing-function:steps({n},end)}}"
            f"{pct(t1)},{pct(t2)}{{transform:translateX({w:.1f}px)}}"
            f"{pct(t2)}{{animation-timing-function:steps({n},end)}}"
            f"{pct(t3)},100%{{transform:translateX(0)}}}}"
            f"@keyframes v{k}{{0%,{pct(max(t0 - 0.01, 0))}{{opacity:0}}{pct(t0)},{pct(t3 + GAP * 0.9)}{{opacity:1}}"
            f"{pct(t3 + GAP * 0.95)},100%{{opacity:0}}}}"
            f".c{k}{{transform-box:view-box;transform-origin:{x}px 0;animation:c{k} {total:.2f}s infinite}}"
            f".k{k}{{animation:k{k} {total:.2f}s infinite}}"
            f".v{k}{{opacity:0;animation:v{k} {total:.2f}s infinite}}"
        )
        body.append(
            f'<clipPath id="clip{k}"><rect class="c{k}" x="{x}" y="{y - size}" '
            f'width="{w + 2:.1f}" height="{size * 1.4:.0f}"/></clipPath>'
            f'<g class="v{k}"><path clip-path="url(#clip{k})" fill="{FG}" d="{d}"/>'
            f'<g class="k{k}"><rect class="blink" x="{x + 3}" y="{y - size * 0.82:.1f}" '
            f'width="{size * 0.55:.1f}" height="{size:.0f}" fill="{ORANGE}"/></g></g>'
        )
    return css, body


def main(photo):
    mono, cjk = TTFont(MONO), TTFont(CJK, fontNumber=0)
    name_d, _ = text_path(cjk, NAME, 112, 720, 200)
    prompt_d, pw = text_path(mono, "›", 26, 720, 286)
    css, body = typing(mono, 720 + pw + 14, 286, 26)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<style>"
        "text{font-family:'DejaVu Sans Mono',Menlo,Consolas,monospace;font-size:4.6px;white-space:pre}"
        ".r{opacity:0;animation:in .5s ease-out forwards}@keyframes in{to{opacity:1}}"
        ".n{opacity:0;animation:in 1s 1.2s ease-out forwards}"
        ".blink{animation:b 1s steps(1) infinite}@keyframes b{50%{opacity:0}}"
        + "".join(css) + "</style>",
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        '<pattern id="dots" width="26" height="26" patternUnits="userSpaceOnUse">'
        '<circle cx="13" cy="13" r="1.2" fill="#ffffff" fill-opacity=".05"/></pattern>',
        f'<rect width="{W}" height="{H}" fill="url(#dots)"/>',
        *portrait(photo),
        f'<path class="n" fill="{FG}" d="{name_d}"/>',
        f'<path fill="{ORANGE}" d="{prompt_d}"/>',
        *body,
        f'<rect y="{H - 8}" width="{W}" height="8" fill="{ORANGE}"/>',
        "</svg>",
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(svg) + "\n")
    print(f"ok: {OUT}")


if __name__ == "__main__":
    main(sys.argv[1])

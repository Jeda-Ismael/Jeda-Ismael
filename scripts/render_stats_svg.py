#!/usr/bin/env python3
"""
Gera assets/stats.svg: card estilo terminal com sequência de dias, total de
contribuições, dias ativos, melhor dia e um gráfico por mês.

Os dados vêm da página pública de contribuições do GitHub (a mesma que o
perfil usa), sem token. Roda todo dia em .github/workflows/update-stats.yml.

Uso: python scripts/render_stats_svg.py            # dados reais
     python scripts/render_stats_svg.py --sample   # dados fictícios, só para testar o layout
Somente biblioteca padrão.
"""
import datetime as dt
import html
import os
import random
import re
import sys
import urllib.request

USER = os.environ.get("GH_PROFILE_USER", "Jeda-Ismael")
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "stats.svg")

# mesmo tamanho do retrato ASCII, para ficarem lado a lado com a mesma altura
W, H = 543, 591
ACCENT = "#A020F0"
ACCENT_HI = "#c77dff"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def fetch_days():
    req = urllib.request.Request(f"https://github.com/users/{USER}/contributions",
                                 headers={"User-Agent": "profile-readme-stats/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        page = r.read().decode("utf-8")

    tips = {}
    for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>(.*?)</tool-tip>', page, re.S):
        tips[m.group(1)] = html.unescape(m.group(2)).strip()

    days = []
    for tag in re.findall(r"<td[^>]*ContributionCalendar-day[^>]*>", page):
        date = re.search(r'data-date="([\d-]+)"', tag)
        if not date:
            continue
        cid = re.search(r'\bid="([^"]+)"', tag)
        text = tips.get(cid.group(1), "") if cid else ""
        n = re.match(r"([\d,]+)", text)
        days.append((dt.date.fromisoformat(date.group(1)), int(n.group(1).replace(",", "")) if n else 0))
    if not days:
        sys.exit("nenhum dia encontrado: o HTML do GitHub pode ter mudado")
    return sorted(days)


def sample_days():
    rnd = random.Random(7)
    end = dt.date.today()
    return [(end - dt.timedelta(days=i), max(0, int(rnd.gauss(4, 4)))) for i in range(370, -1, -1)]


def streaks(days):
    counts = [c for _, c in days]
    # o dia de hoje ainda não acabou: não quebra a sequência se estiver zerado
    i = len(counts) - 1 - (counts[-1] == 0)
    end = i
    while i >= 0 and counts[i] > 0:
        i -= 1
    cur = (end - i, days[i + 1][0], days[end][0]) if end > i else (0, None, None)

    best, run, start = (0, None, None), 0, 0
    for j, c in enumerate(counts):
        if c:
            start = j if run == 0 else start
            run += 1
            if run > best[0]:
                best = (run, days[start][0], days[j][0])
        else:
            run = 0
    return cur, best


def fmt_date(d):
    return f"{d.day} {MESES[d.month - 1]}" if d else "—"


def fmt_range(s):
    return f"{fmt_date(s[1])} – {fmt_date(s[2])}" if s[0] else "comece hoje"


def num(n):
    return f"{n:,}".replace(",", ".")


def render(days):
    (cur, longest) = streaks(days)
    total = sum(c for _, c in days)
    active = sum(1 for _, c in days if c)
    best_day = max(days, key=lambda d: d[1])
    avg = total / active if active else 0

    months = {}
    for d, c in days:
        months[(d.year, d.month)] = months.get((d.year, d.month), 0) + c
    months = sorted(months.items())[-13:]

    pad, gap, top = 14, 10, 44
    cw = (W - pad * 2 - gap) / 2
    ch = 78
    cards = [
        ("sequência atual", num(cur[0]), "dias", fmt_range(cur), True),
        ("maior sequência", num(longest[0]), "dias", fmt_range(longest), False),
        ("contribuições", num(total), "", "no último ano", False),
        ("dias ativos", num(active), f"/ {len(days)}", f"{round(100 * active / len(days))}% do ano", False),
        ("melhor dia", num(best_day[1]), "", fmt_date(best_day[0]), False),
        ("média / dia ativo", f"{avg:.1f}".replace(".", ","), "", "contribuições", False),
    ]

    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        "<style>"
        "text{font-family:'DejaVu Sans Mono',Menlo,Consolas,monospace}"
        ".c{opacity:0;animation:in .5s ease-out forwards}"
        ".b{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);"
        "animation:up .7s cubic-bezier(.2,.8,.2,1) forwards}"
        "@keyframes in{to{opacity:1}}@keyframes up{to{transform:scaleY(1)}}"
        "</style>",
        f'<rect width="{W}" height="{H}" rx="12" fill="#0d1117" stroke="#30363d"/>',
        f'<path d="M0 30H{W}" stroke="#30363d"/>',
        '<circle cx="18" cy="15" r="5" fill="#ff5f56"/><circle cx="34" cy="15" r="5" fill="#ffbd2e"/>'
        '<circle cx="50" cy="15" r="5" fill="#27c93f"/>',
        f'<text x="{W / 2:.0f}" y="19" text-anchor="middle" font-size="11" fill="#8b949e">'
        "jedaias@github: ~ $ ./stats.sh</text>",
    ]
    for k, (label, value, unit, sub, hi) in enumerate(cards):
        x = pad + (k % 2) * (cw + gap)
        y = top + (k // 2) * (ch + gap)
        o.append(f'<g class="c" style="animation-delay:{0.15 * k:.2f}s">'
                 f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{ch}" rx="8" fill="#161b22" stroke="#30363d"/>'
                 f'<text x="{x + 14:.1f}" y="{y + 22}" font-size="11.5" fill="#8b949e">$ {label}</text>'
                 f'<text x="{x + 14:.1f}" y="{y + 50}" font-size="26" font-weight="bold" '
                 f'fill="{ACCENT_HI if hi else "#f0f6fc"}">{value}'
                 f'<tspan font-size="12" font-weight="normal" fill="#8b949e"> {unit}</tspan></text>'
                 f'<text x="{x + 14:.1f}" y="{y + 68}" font-size="10.5" fill="#8b949e">{sub}</text></g>')

    # gráfico por mês
    gy = top + 3 * (ch + gap)
    gh = H - gy - pad
    o.append(f'<g class="c" style="animation-delay:.9s"><rect x="{pad}" y="{gy}" width="{W - pad * 2}" '
             f'height="{gh}" rx="8" fill="#161b22" stroke="#30363d"/>'
             f'<text x="{pad + 14}" y="{gy + 22}" font-size="11.5" fill="#8b949e">$ contribuições / mês</text></g>')
    peak = max((v for _, v in months), default=0) or 1
    base = gy + gh - 28
    area_h = gh - 70
    slot = (W - pad * 2 - 28) / len(months)
    bw = slot * 0.62
    for k, ((yr, mo), v) in enumerate(months):
        bx = pad + 14 + k * slot + (slot - bw) / 2
        bh = max(2, area_h * v / peak)
        top_month = v == peak and v > 0
        o.append(f'<rect class="b" style="animation-delay:{1.1 + 0.06 * k:.2f}s" x="{bx:.1f}" '
                 f'y="{base - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" '
                 f'fill="{ACCENT_HI if top_month else ACCENT}"/>')
        if top_month:
            o.append(f'<text class="c" style="animation-delay:1.9s" x="{bx + bw / 2:.1f}" y="{base - bh - 6:.1f}" '
                     f'text-anchor="middle" font-size="10" fill="#f0f6fc">{num(v)}</text>')
        o.append(f'<text x="{bx + bw / 2:.1f}" y="{base + 16}" text-anchor="middle" font-size="10" '
                 f'fill="#8b949e">{MESES[mo - 1][0].upper()}</text>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


if __name__ == "__main__":
    days = sample_days() if "--sample" in sys.argv else fetch_days()
    out = sys.argv[sys.argv.index("-o") + 1] if "-o" in sys.argv else OUT
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(days))
    print(f"ok: {out}")

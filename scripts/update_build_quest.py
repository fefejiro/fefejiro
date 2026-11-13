#!/usr/bin/env python3
"""Generate the single public Build Quest contribution graphic in two themes.

GitHub's public contribution calendar is the source of truth. It includes
anonymous private activity only when its owner opts into that profile setting.
No private repository details or source code are fetched or published.
"""
from html import escape
from pathlib import Path
import os
import re
from urllib.request import Request, urlopen

OWNER = os.getenv("GITHUB_REPOSITORY_OWNER", "fefejiro")
SOURCE = f"https://github.com/users/{OWNER}/contributions"
DEST = Path("dist")
DEST.mkdir(parents=True, exist_ok=True)

request = Request(SOURCE, headers={
    "User-Agent": "BuildQuest-GitHub-Profile/1.0",
    "Accept": "text/html",
    "Cache-Control": "no-cache",
})
with urlopen(request, timeout=30) as response:
    page = response.read().decode("utf-8")

title = re.search(
    r'<h2[^>]+id="js-contribution-activity-description"[^>]*>'
    r'\s*([0-9,]+)\s*contributions?', page, re.S
)
cells = re.findall(
    r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="([0-4])"',
    page,
)
if not title or len(cells) < 350:
    raise RuntimeError("GitHub contribution response was incomplete. Existing SVGs remain unchanged.")

total = int(title.group(1).replace(",", ""))
if total < 0:
    raise ValueError("Invalid contribution count")

score = f"{total:,}"
days = [(date, int(level)) for date, level in cells]
points = [
    (65 + (i // 7) * 18.2, 110 + (i % 7) * 17.3, level)
    for i, (_, level) in enumerate(days)
]
active = [pt for pt in points if pt[2]]
if not active:
    raise RuntimeError("No recorded activity days; will not overwrite the profile graphic.")
route = " ".join(
    f"{'L' if index else 'M'}{x:.1f} {y:.1f}"
    for index, (x, y, _) in enumerate(active)
)


def render(dark: bool) -> str:
    colors = (
        ["#29364e", "#254c67", "#16688d", "#169fb0", "#6de4c4"]
        if dark else
        ["#e7edf7", "#aed5e4", "#67b8d7", "#2387b8", "#5652ba"]
    )
    bg, bg2, fg, muted, accent, outline = (
        ("#0b1225", "#17213e", "#f6f9ff", "#adc0d7", "#6df5dd", "#324060")
        if dark else
        ("#f9fbff", "#e8f0ff", "#16243f", "#576b83", "#176eb5", "#d5e0f2")
    )
    tiles = "\n".join(
        f'<rect x="{x - 6:.1f}" y="{y - 6:.1f}" width="12" height="12" '
        f'rx="2.6" fill="{colors[level]}"/>'
        for x, y, level in points
    )
    score_text = escape(score)
    safe_route = escape(route, quote=True)

    return f"""<svg xmlns="http://www.w3.org/2000/svg" role="img"
aria-labelledby="title description" viewBox="0 0 1100 254" width="1100" height="254">
<title id="title">Build Quest: {score_text} GitHub contributions in the past year</title>
<desc id="description">Animated activity game using GitHub's public contribution calendar.
Private contributions can appear anonymously when enabled by the owner.
Contribution counts are not individual commit counts.</desc>
<defs>
<linearGradient id="background" x2="1" y2="1">
<stop stop-color="{bg}"/><stop offset="1" stop-color="{bg2}"/>
</linearGradient>
<filter id="glow" x="-200%" y="-200%" width="500%" height="500%">
<feGaussianBlur stdDeviation="3" result="blur"/>
<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter></defs>
<rect x="1" y="1" width="1098" height="252" rx="16" stroke="{outline}"
stroke-width="2" fill="url(#background)"/>
<text x="52" y="34" fill="{accent}" font-family="Arial,Helvetica,sans-serif"
font-size="13" font-weight="800" letter-spacing="2">BUILD QUEST / LEVEL UP</text>
<text x="52" y="63" fill="{fg}" font-family="Arial,Helvetica,sans-serif"
font-size="26" font-weight="700">A year of making things work.</text>
<text x="870" y="45" fill="{fg}" text-anchor="middle"
font-family="Arial,Helvetica,sans-serif" font-size="37" font-weight="800">{score_text}</text>
<text x="870" y="64" fill="{muted}" text-anchor="middle"
font-family="Arial,Helvetica,sans-serif" font-size="12" font-weight="700">GITHUB CONTRIBUTIONS</text>
<text x="52" y="83" fill="{muted}" font-family="Arial,Helvetica,sans-serif"
font-size="12">ROLLING 12 MONTHS · PRIVATE WORK ANONYMOUS</text>
{tiles}
<rect x="48" y="119" width="5" height="27" rx="2.5" fill="{accent}" opacity=".8">
<animate attributeName="y" values="119;174;119" dur="4.4s" repeatCount="indefinite"/></rect>
<rect x="1035" y="158" width="5" height="27" rx="2.5" fill="{accent}" opacity=".8">
<animate attributeName="y" values="158;103;158" dur="5.2s" repeatCount="indefinite"/></rect>
<circle r="5.5" fill="{accent}" stroke="#ffffff" stroke-width="1.5" filter="url(#glow)">
<animateMotion dur="26s" repeatCount="indefinite" path="{safe_route}"/></circle>
<text x="52" y="239" fill="{muted}" font-family="Arial,Helvetica,sans-serif"
font-size="11">PAST YEAR</text>
<text x="470" y="239" fill="{muted}" font-family="Arial,Helvetica,sans-serif"
font-size="11">KEEP MOVING</text>
<text x="756" y="239" fill="{muted}" font-family="Arial,Helvetica,sans-serif"
font-size="11">TODAY</text>
<text x="997" y="239" text-anchor="middle" fill="{accent}"
font-family="Arial,Helvetica,sans-serif" font-size="11" font-weight="700">KEEP BUILDING</text>
</svg>"""


for theme, filename in (
    (False, "build-quest-light.svg"),
    (True, "build-quest-dark.svg"),
):
    output = DEST / filename
    output.write_text(render(theme), encoding="utf-8")
    print(f"Wrote {output}: {score} verified contributions, {len(active)} active days")

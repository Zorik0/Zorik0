"""Build the GitHub profile header: Zoriko wordmark + the enquiry-to-invoice trace.
Usage: download Poppins (Black, Medium, Regular) from github.com/google/fonts into ./fonts, then
  uv run --with uharfbuzz --with fonttools python scripts/make_header.py && mv header.svg assets/

All text is converted to outlines (Poppins, shaped with HarfBuzz) so the SVG
renders identically without web fonts, which GitHub's image proxy can't load.
"""
import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONTS = "fonts/Poppins-{}.ttf"
BLACK, WHITE, SIGNAL, ASH, RULE, LABEL = "#000000", "#FFFFFF", "#FF3300", "#A1A1AA", "#2E2E2E", "#E4E4E7"
W, H = 1280, 640
LEFT = 96

_cache = {}


def _font(weight):
    if weight not in _cache:
        path = FONTS.format(weight)
        face = hb.Face(hb.Blob.from_file_path(path))
        tt = TTFont(path)
        _cache[weight] = (hb.Font(face), face.upem, tt.getGlyphSet(), tt.getGlyphOrder())
    return _cache[weight]


def outline(text, weight, size, x, y, tracking=0.0, anchor="start"):
    """Return (svg path data, advance width) for text set at baseline y."""
    font, upem, glyphs, order = _font(weight)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    scale = size / upem
    infos, positions = buf.glyph_infos, buf.glyph_positions
    width = sum(p.x_advance for p in positions) * scale + tracking * (len(infos) - 1)
    if anchor == "middle":
        x -= width / 2
    elif anchor == "end":
        x -= width
    parts, pen_x = [], x
    for info, pos in zip(infos, positions):
        pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
        glyphs[order[info.codepoint]].draw(
            TransformPen(pen, (scale, 0, 0, -scale, pen_x + pos.x_offset * scale, y - pos.y_offset * scale))
        )
        parts.append(pen.getCommands())
        pen_x += pos.x_advance * scale + tracking
    return " ".join(p for p in parts if p), width


# Wordmark lockup, echoing zoriko.space: ZORIKO over a signal bar and SPACE.
mark_d, mark_w = outline("ZORIKO", "Black", 196, LEFT - 6, 262, tracking=-4)
bar_w, bar_h, bar_y = round(mark_w * 0.16), 12, 300
space_d, _ = outline("SPACE", "Medium", 46, LEFT + bar_w + 26, 322, tracking=7)

# One plain sentence about what he builds.
line1, _ = outline("I build the software travel and operations businesses run on:", "Regular", 31, LEFT, 412)
line2, _ = outline("the booking app customers use, and the ERP behind it.", "Regular", 31, LEFT, 458)

# The enquiry-to-invoice sequence, drawn once from left to right.
steps = ["Enquiry", "Quote", "Booking", "Ticket", "Invoice"]
x0, x1, ty = LEFT + 8, W - LEFT - 8, 540
span = x1 - x0
xs = [x0 + span * i / (len(steps) - 1) for i in range(len(steps))]
DELAY, DUR = 0.6, 2.4

labels = []
for i, (name, x) in enumerate(zip(steps, xs)):
    anchor = "start" if i == 0 else "end" if i == len(steps) - 1 else "middle"
    lx = x - 7 if anchor == "start" else x + 7 if anchor == "end" else x
    d, _ = outline(name, "Medium", 23, lx, ty + 50, anchor=anchor)
    labels.append(d)

node_css = "\n".join(
    f"    .n{i} {{ animation: lit .2s {DELAY + DUR * i / (len(steps) - 1):.2f}s ease-out forwards; }}"
    for i in range(len(steps))
)
nodes = "\n".join(
    f'  <circle class="node n{i}" cx="{x:.1f}" cy="{ty}" r="7" fill="{BLACK}" stroke="#52525B" stroke-width="2.5"/>'
    for i, x in enumerate(xs)
)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">
  <title id="title">Zoriko</title>
  <desc id="desc">Zoriko Space. I build the software travel and operations businesses run on: the booking app customers use, and the ERP behind it. Enquiry, quote, booking, ticket, invoice.</desc>
  <style>
    .bar {{ transform-box: fill-box; transform-origin: left center; animation: grow .8s .1s cubic-bezier(.2,.8,.2,1) both; }}
    .trace {{ stroke-dasharray: {span:.1f}; stroke-dashoffset: {span:.1f}; animation: draw {DUR}s {DELAY}s linear forwards; }}
    .dot {{ animation: travel {DUR}s {DELAY}s linear both; }}
{node_css}
    @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
    @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
    @keyframes travel {{ from {{ transform: translateX(0); }} to {{ transform: translateX({span:.1f}px); }} }}
    @keyframes lit {{ to {{ fill: {SIGNAL}; stroke: {SIGNAL}; }} }}
    @media (prefers-reduced-motion: reduce) {{
      .bar, .trace, .dot, .node {{ animation: none; }}
      .trace {{ stroke-dashoffset: 0; }}
      .dot {{ transform: translateX({span:.1f}px); }}
      .node {{ fill: {SIGNAL}; stroke: {SIGNAL}; }}
    }}
  </style>
  <rect width="{W}" height="{H}" rx="28" fill="{BLACK}"/>
  <path fill="{WHITE}" d="{mark_d}"/>
  <rect class="bar" x="{LEFT}" y="{bar_y}" width="{bar_w}" height="{bar_h}" fill="{SIGNAL}"/>
  <path fill="{SIGNAL}" d="{space_d}"/>
  <path fill="{ASH}" d="{line1} {line2}"/>
  <line x1="{x0:.1f}" y1="{ty}" x2="{x1:.1f}" y2="{ty}" stroke="{RULE}" stroke-width="2.5"/>
  <line class="trace" x1="{x0:.1f}" y1="{ty}" x2="{x1:.1f}" y2="{ty}" stroke="{SIGNAL}" stroke-width="2.5"/>
{nodes}
  <circle class="dot" cx="{x0:.1f}" cy="{ty}" r="11" fill="{SIGNAL}"/>
  <path fill="{LABEL}" d="{' '.join(labels)}"/>
</svg>
"""

with open("header.svg", "w") as f:
    f.write(svg)
print(f"header.svg written: {len(svg) / 1024:.1f} KB, wordmark width {mark_w:.0f}px")

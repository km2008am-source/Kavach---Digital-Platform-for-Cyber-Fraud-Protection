"""Render 5 English dataset messages as phone-style chat screenshots for the OCR test.

    python data/samples/screenshots/make_screenshots.py

The guide's OCR test: "5 screenshots of dataset messages -> verdict matches the text version".
English only, because Pillow's default font has no Tamil glyphs; add a Tamil font
(e.g. Noto Sans Tamil) to also test `tam` OCR.
"""
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
IDS = ["s07", "s22", "s34", "l03", "l17"]          # 3 scams + 2 legit


def font(size: int) -> ImageFont.ImageFont:
    for name in ("arial.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def render(text: str, path: Path) -> None:
    f = font(30)
    lines = textwrap.wrap(text, width=34)
    h = 160 + 44 * len(lines)
    img = Image.new("RGB", (720, h), (236, 229, 221))                   # WhatsApp-like background
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 720, 90], fill=(7, 94, 84))
    d.text((30, 28), "+91 90000 00000", font=f, fill="white")
    d.rounded_rectangle([24, 116, 696, h - 20], radius=18, fill="white")
    for i, line in enumerate(lines):
        d.text((48, 134 + 44 * i), line, font=f, fill=(20, 20, 20))
    img.save(path)


def main() -> None:
    rows = {}
    for name in ("scams.jsonl", "legit.jsonl"):
        for line in (HERE.parent / name).read_text("utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                rows[row["id"]] = row
    for i in IDS:
        render(rows[i]["text"], HERE / f"{i}.png")
    print("wrote", len(IDS), "screenshots to", HERE)


if __name__ == "__main__":
    main()

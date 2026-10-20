"""Render the 10 fake payment receipts in receipts_ocr.jsonl as phone-screenshot PNGs.

    python data/samples/receipts/make_receipts.py

These are the "10 sample screenshots of UPI receipts (fake, made by the team)" that
Member 1's Golden Hour flow needs (guide section 6J). Every value in them is invented,
there are no real logos, and each image carries a visible test-sample footer. The OCR
text each image should produce is the `text` field of the matching line, and `expect`
holds the transaction ID and amount the evidence extractor must find.
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "receipts_ocr.jsonl"
FOOTER = "TEST SAMPLE - NOT A REAL TRANSACTION"


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    names = ("arialbd.ttf", "DejaVuSans-Bold.ttf") if bold else ("arial.ttf", "DejaVuSans.ttf")
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def render(text: str, path: Path) -> None:
    lines = [l for l in text.split("\n") if l.strip()]
    if len(lines) == 1:                                     # bank-SMS style receipt: wrap it
        import textwrap
        lines = textwrap.wrap(lines[0], width=36)
    body, big, small = font(30), font(46, bold=True), font(20)
    h = 300 + 58 * len(lines)
    img = Image.new("RGB", (720, h), (245, 246, 248))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([30, 30, 690, h - 80], radius=24, fill="white")
    d.ellipse([320, 60, 400, 140], fill=(46, 160, 90))         # neutral "success" tick, no brand
    d.line([(342, 102), (356, 117), (382, 86)], fill="white", width=8)
    y = 170
    for line in lines:
        is_amount = any(line.strip().startswith(p) for p in ("₹", "Rs", "INR", "Amount"))
        f = big if is_amount and len(lines) > 1 else body
        w = d.textlength(line, font=f)
        d.text(((720 - w) / 2, y), line, font=f, fill=(25, 25, 25))
        y += 66 if f is big else 54
    w = d.textlength(FOOTER, font=small)
    d.text(((720 - w) / 2, h - 58), FOOTER, font=small, fill=(150, 150, 150))
    img.save(path)


def main() -> None:
    rows = [json.loads(l) for l in SOURCE.read_text("utf-8").splitlines() if l.strip()]
    for row in rows:
        render(row["text"], HERE / f"{row['id']}.png")
    print("wrote", len(rows), "receipt screenshots to", HERE)


if __name__ == "__main__":
    main()

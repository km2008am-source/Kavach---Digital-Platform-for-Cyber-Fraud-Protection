"""Generate screening_notice.mp3 with Tamil then English lines."""
from pathlib import Path

from gtts import gTTS


def main() -> None:
    out = Path(__file__).with_name("screening_notice.mp3")
    tamil = gTTS(
        "இந்த அழைப்பை ஒரு தானியங்கி உதவியாளர் பரிசோதிக்கிறார். "
        "உங்கள் பெயரையும் நீங்கள் ஏன் அழைக்கிறீர்கள் என்பதையும் சொல்லுங்கள்.",
        lang="ta",
    )
    english = gTTS(
        "This call is being screened by an automated assistant. Please say your name and why you are calling.",
        lang="en",
    )
    tmp_ta = out.with_name("_ta.mp3")
    tmp_en = out.with_name("_en.mp3")
    tamil.save(tmp_ta)
    english.save(tmp_en)
    out.write_bytes(tmp_ta.read_bytes() + tmp_en.read_bytes())
    tmp_ta.unlink(missing_ok=True)
    tmp_en.unlink(missing_ok=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

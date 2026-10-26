"""Generate screening_notice.mp3 for Call Shield: the notice in Hindi, then English.

    pip install gTTS      (part of the backend's [voice] extra)
    python kavach/static/make_notice.py

Until the file exists, the call says the English notice with Twilio's own voice.
"""
from pathlib import Path

from gtts import gTTS


def main() -> None:
    out = Path(__file__).with_name("screening_notice.mp3")
    hindi = gTTS(
        "इस कॉल की जाँच एक स्वचालित सहायक कर रहा है। "
        "कृपया अपना नाम और कॉल करने का कारण बताइए।",
        lang="hi",
    )
    english = gTTS(
        "This call is being screened by an automated assistant. Please say your name and why you are calling.",
        lang="en",
    )
    tmp_hi = out.with_name("_hi.mp3")
    tmp_en = out.with_name("_en.mp3")
    hindi.save(tmp_hi)
    english.save(tmp_en)
    out.write_bytes(tmp_hi.read_bytes() + tmp_en.read_bytes())
    tmp_hi.unlink(missing_ok=True)
    tmp_en.unlink(missing_ok=True)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

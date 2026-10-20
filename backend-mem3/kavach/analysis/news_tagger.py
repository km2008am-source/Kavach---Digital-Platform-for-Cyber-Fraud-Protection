# STAND-IN for Member 2's analysis/news_tagger.py (signature from section 5).
async def tag(title: str, summary: str) -> dict:
    text = f"{title} {summary}".lower()
    stype = ("digital_arrest" if "arrest" in text else "kyc_update" if "kyc" in text
             else "investment" if "invest" in text else "phishing_link" if "phish" in text else "unknown")
    return {"scam_type": stype, "region": "India", "red_flags": []}

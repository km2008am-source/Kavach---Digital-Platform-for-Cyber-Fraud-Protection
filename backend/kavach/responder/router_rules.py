"""Choose official reporting destinations for a scam situation."""

from kavach.contracts import AnalysisResult


def route(
    result: AnalysisResult,
    lost_money: bool = False,
    lost_phone: bool = False,
) -> list[dict[str, str]]:
    """Return destinations and next steps, with urgent fraud routing first."""
    destinations: list[dict[str, str]] = []

    if lost_money:
        destinations.extend([
            {
                "name": "National Cyber Crime Helpline",
                "action": "Call 1930 now. Contact your bank through its official "
                          "app or website and ask it to block further transactions.",
                "url": "tel:1930",
            },
            {
                "name": "National Cyber Crime Reporting Portal",
                "action": "File or complete the complaint online.",
                "url": "https://www.cybercrime.gov.in/",
            },
        ])
        return destinations

    if lost_phone:
        destinations.append({
            "name": "CEIR lost or stolen phone service",
            "action": "Report the loss and request that the handset be blocked.",
            "url": "https://www.ceir.gov.in/",
        })

    if result.scam_type.lower() in {"investment", "illegal_deposit"}:
        destinations.append({
            "name": "RBI Sachet",
            "action": "Report or check an unauthorized deposit or investment scheme.",
            "url": "https://sachet.rbi.org.in/",
        })

    if result.risk_level.value in {"medium", "high"}:
        destinations.append({
            "name": "Sanchar Saathi Chakshu",
            "action": "Report a suspected fraudulent call, SMS, or WhatsApp message.",
            "url": "https://www.sancharsaathi.gov.in/",
        })

    return destinations
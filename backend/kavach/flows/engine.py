"""Dispatch incoming WhatsApp messages to Kavach flows."""

import re
from pathlib import Path
import json
from pathlib import Path
from kavach.contracts import AnalysisRequest, IncomingMessage
from kavach.db import session
from kavach.flows import golden_hour, messages
from kavach.flows.intents import detect
from kavach.language.service import detect_language, translate
from kavach.whatsapp.client import send_buttons, send_text
from kavach.whatsapp.media import download_media
from kavach.contracts import EvidenceSummary
from kavach.responder.pdf import create_evidence_pdf
from kavach.whatsapp.client import send_document


def _bank_details(bank_name: str) -> dict | None:
    bank_file = (
        Path(__file__).parents[1]
        / "responder"
        / "banks.json"
    )
    banks = json.loads(bank_file.read_text(encoding="utf-8"))
    query = bank_name.casefold().replace(" bank", "").strip()

    for key, details in banks.items():
        name = details["name"].casefold().replace(" bank", "")
        if query == key or query in name or name in query:
            return details

    return None

def _make_complaint_draft(
    user_id: str,
    bank_name: str,
    acknowledgement_number: str | None = None,
) -> str:
    acknowledgement_line = (
        f"1930 acknowledgement number: {acknowledgement_number}"
        if acknowledgement_number
        else "1930 acknowledgement number: Pending"
    )

    return (
        "I am reporting a suspected online financial fraud. "
        f"My registered contact number is {user_id}. "
        f"The bank or payment provider is {bank_name or 'not provided'}. "
        f"{acknowledgement_line}. "
        "Please investigate the transaction and take appropriate action. "
        "I can provide the transaction details and supporting screenshots."
    )


async def _reply(user_id: str, text: str, language: str) -> None:
    """Send a reply in the user's selected language, with English fallback."""
    if language != "en":
        try:
            text = await translate(text, source="en", target=language)
        except Exception:
            pass
    await send_text(user_id, text)


async def _reply_buttons(
    user_id: str,
    body: str,
    buttons: list[tuple[str, str]],
    language: str,
) -> None:
    if language != "en":
        try:
            body = await translate(body, source="en", target=language)
            buttons = [
                (button_id, await translate(title, source="en", target=language))
                for button_id, title in buttons
            ]
        except Exception:
            pass
    await send_buttons(user_id, body, buttons)


def _get_language(user_id: str) -> str:
    with session() as connection:
        row = connection.execute(
            "SELECT language FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    return row["language"] if row else "en"


def _set_language(user_id: str, language: str) -> None:
    with session() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (user_id,),
        )
        connection.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (language, user_id),
        )


def _format_verdict(result) -> str:
    red_flags = [
        f"• {flag.label}: {flag.explanation}"
        for flag in result.red_flags[:3]
    ]
    flag_text = "\n".join(red_flags) if red_flags else "No clear red flags found."

    return (
        f"Risk: {result.risk_level.value.upper()}\n"
        f"Likely type: {result.scam_type}\n\n"
        f"{result.explanation}\n\n"
        f"Red flags:\n{flag_text}\n\n"
        f"Recommended next step: {result.recommended_action}"
    )


async def _analyze(request: AnalysisRequest):
    """Call Person 2's analysis module when it is added to the project."""
    from kavach.analysis.scam_check import analyze

    return await analyze(request)


async def _handle_check(message: IncomingMessage, language: str) -> None:
    text = message.text

    if message.media_id:
        path = await download_media(message.media_id, message.filename)
        text = text or ""
        request = AnalysisRequest(
            text=text,
            language=language,
            source="whatsapp",
            media_path=str(path),
            media_type=message.mime_type or message.kind,
            user_id=message.sender,
        )
    else:
        request = AnalysisRequest(
            text=text,
            language=language,
            source="whatsapp",
            user_id=message.sender,
        )

    try:
        result = await _analyze(request)
    except (ImportError, ModuleNotFoundError):
        await _reply(message.sender, messages.ANALYSIS_UNAVAILABLE, language)
        return
    except Exception:
        await _reply(message.sender, messages.ANALYSIS_UNAVAILABLE, language)
        return

    await _reply_buttons(
        message.sender,
        _format_verdict(result),
        [
            ("gh_start", "I already paid"),
            ("report", "How to report"),
            ("menu", "Menu"),
        ],
        language,
    )


async def _handle_golden_hour(
    message: IncomingMessage,
    intent: str,
    language: str,
) -> None:
    conversation = golden_hour.get_conversation(message.sender)

    if intent == "gh_start":
        golden_hour.start(message.sender)
        await _reply_buttons(
            message.sender,
            messages.GOLDEN_HOUR_START,
            [("gh_done", "Done"), ("menu", "Menu")],
            language,
        )
        return

    if intent == "gh_done":
        if conversation.state == "GH_WAIT_EVIDENCE":
            golden_hour.finish_evidence(message.sender)
            await _reply(
                message.sender,
                messages.GOLDEN_HOUR_ASK_BANK,
                language,
            )
        else:
            await _reply(message.sender, messages.GENERIC_ERROR, language)
        return

    if conversation.state == "GH_WAIT_EVIDENCE":
        if message.media_id:
            path = await download_media(message.media_id, message.filename)
            golden_hour.add_evidence(message.sender, str(path))
            await _reply_buttons(
                message.sender,
                "Got it. Send another screenshot or tap Done.",
                [("gh_done", "Done"), ("menu", "Menu")],
                language,
            )
        else:
            await _reply_buttons(
                message.sender,
                messages.GOLDEN_HOUR_WAITING,
                [("gh_done", "Done"), ("menu", "Menu")],
                language,
            )
        return

    if conversation.state == "GH_BANK":
        bank_name = message.text.strip()
        if len(bank_name) < 2:
            await _reply(message.sender, messages.GOLDEN_HOUR_ASK_BANK, language)
            return

        bank = _bank_details(bank_name)
        if bank:
            bank_reply = (
                f"{bank['name']} fraud contact: {bank['fraud_contact']}\n\n"
                f"{bank['freeze_steps']}\n\n"
                f"Official information: {bank['official_url']}\n\n"
                "Call 1930 now if you have not already."
                )
        else:
            bank_reply = (
                "Use the phone number in your bank's official app or website "
                "to report the transaction and ask them to block further "
                "transactions. Do not use a number sent to you in a message "
                "or provided by an unknown caller.\n\n"
                "Call 1930 now if you have not already."
            )

            conversation.data["bank_name"] = bank_name
            conversation.state = "GH_ACK"
            golden_hour.save_conversation(message.sender, conversation)
            await _reply(message.sender, bank_reply, language)
            await _reply(message.sender, messages.GOLDEN_HOUR_ACK, language)
            return

    if conversation.state == "GH_ACK":
        acknowledgement = message.text.strip()

        if len(acknowledgement) < 3:
            await _reply(message.sender, messages.GOLDEN_HOUR_ACK, language)
            return

        golden_hour.save_acknowledgement(message.sender, acknowledgement)

        bank_name = conversation.data.get("bank_name", "")
        complaint_draft = _make_complaint_draft(
            user_id=message.sender,
            bank_name=bank_name,
            acknowledgement_number=acknowledgement,
        )

        evidence = EvidenceSummary()
        pdf_path = create_evidence_pdf(evidence, complaint_draft)

        await _reply(
            message.sender,
            "I saved your acknowledgement number. Here is a complaint draft "
            "and evidence pack. Review it, add any missing transaction details, "
            "and file the complaint at cybercrime.gov.in.",
            language,
        )
        await send_document(
            message.sender,
            pdf_path,
            "fraud-evidence-summary.pdf",
        )
        return

async def _set_guardian(message: IncomingMessage, language: str) -> None:
    match = re.fullmatch(
        r"\s*guardian\s+(\+?\d{10,15})\s*",
        message.text,
        flags=re.IGNORECASE,
    )
    if not match:
        await _reply(message.sender, messages.GUARDIAN_USAGE, language)
        return

    guardian_number = match.group(1)
    with session() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (message.sender,),
        )
        connection.execute(
            "UPDATE users SET guardian_number = ? WHERE user_id = ?",
            (guardian_number, message.sender),
        )

    await _reply(
        message.sender,
        "Trusted contact saved. High-risk alerts can now be shared with that number.",
        language,
    )


async def handle_message(message: IncomingMessage) -> None:
    """Entry point used by the WhatsApp webhook background task."""
    try:
        existing_language = _get_language(message.sender)
        language = detect_language(message.text, default=existing_language)
        _set_language(message.sender, language)

        conversation = golden_hour.get_conversation(message.sender)
        intent = detect(message, conversation.state)

        if intent == "menu":
            golden_hour.save_conversation(
                message.sender,
                golden_hour.Conversation(),
            )
            await _reply(message.sender, messages.WELCOME, language)
            return

        if intent == "gh_start" or conversation.state.startswith("GH_"):
            await _handle_golden_hour(message, intent, language)
            return

        if intent == "set_guardian":
            await _set_guardian(message, language)
            return

        if intent == "dns_guide":
            await _reply(message.sender, messages.DNS_GUIDE, language)
            return

        if intent == "check_bait":
            await _reply(
                message.sender,
                "Scam Bait verification is being connected. For now, send the "
                "link or message for a Scam Check.",
                language,
            )
            return

        if intent == "check_apk" or intent == "check":
            await _handle_check(message, language)
            return

        await _reply(message.sender, messages.UNSUPPORTED, language)

    except Exception:
        # Avoid leaking exception details or user content in WhatsApp replies.
        try:
            await send_text(message.sender, messages.GENERIC_ERROR)
        except Exception:
            pass

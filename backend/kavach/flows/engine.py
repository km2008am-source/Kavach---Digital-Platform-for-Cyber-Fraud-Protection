""" Dispatch incoming WhatsApp messages to Kavach flows."""

"""Dispatch incoming WhatsApp messages to Kavach flows."""

import json
import re
from pathlib import Path

from kavach.config import settings
from kavach.contracts import (
    AnalysisRequest,
    AnalysisResult,
    EvidenceSummary,
    IncomingMessage,
    RiskLevel,
)
from kavach.db import session
from kavach.flows import golden_hour, messages
from kavach.flows.intents import detect
from kavach.language.service import detect_language, stt, translate, tts
from kavach.responder import router_rules
from kavach.responder.pdf import create_evidence_pdf
from kavach.whatsapp.client import (
    send_audio,
    send_buttons,
    send_document,
    send_text,
)
from kavach.whatsapp.media import download_media
import logging
logger = logging.getLogger(__name__)

def _analysis_source() -> str:
    """Return the active messaging channel for analytics."""
    return "telegram" if settings.whatsapp_provider == "telegram" else "whatsapp"


_EVIDENCE_FIELDS = (
    ("GH_TRANSACTION_ID", "transaction_id"),
    ("GH_AMOUNT", "amount"),
    ("GH_TRANSACTION_TIME", "transaction_time"),
    ("GH_PAYEE_UPI", "payee_upi"),
    ("GH_SCAMMER_NUMBER", "scammer_number"),
)



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
    evidence: EvidenceSummary | None = None,
) -> str:
    acknowledgement_line = (
        f"1930 acknowledgement number: {acknowledgement_number}"
        if acknowledgement_number
        else "1930 acknowledgement number: Pending"
    )

    details: list[str] = []
    if evidence:
        fields = [
            ("Transaction ID", evidence.transaction_id),
            ("Amount", evidence.amount),
            ("Transaction time", evidence.transaction_time),
            ("Payee UPI ID", evidence.payee_upi),
            ("Scammer phone number", evidence.scammer_number),
        ]
        details.extend(
            f"{label}: {value}"
            for label, value in fields
            if value
        )
        details.extend(
            f"{key.replace('_', ' ').title()}: {value}"
            for key, value in evidence.additional_details.items()
            if value
        )

    transaction_details = (
        "\n".join(details)
        if details
        else "No transaction details were extracted; please add them before filing."
    )

    return (
        "I am reporting a suspected online financial fraud.\n"
        f"My registered contact number is {user_id}.\n"
        f"The bank or payment provider is {bank_name or 'not provided'}.\n"
        f"{acknowledgement_line}.\n"
        f"Transaction details:\n{transaction_details}\n"
        "Please investigate the transaction and take appropriate action.\n"
        "I can provide the supporting screenshots."
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

def _get_guardian_number(user_id: str) -> str | None:
    with session() as connection:
        row = connection.execute(
            "SELECT guardian_number FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    return row["guardian_number"] if row else None


def _get_district(user_id: str) -> str | None:
    with session() as connection:
        row = connection.execute(
            "SELECT district FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    return row["district"] if row else None

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
    language = language if language in {"en", "hi"} else "en"
    text = message.text
    district = _get_district(message.sender)

    if message.kind == "audio" and message.media_id:
        try:
            audio_path = await download_media(
                message.media_id,
                message.filename,
            )
            text = await stt(str(audio_path), language="auto")
        except Exception:
            await _reply(
                message.sender,
                "I couldn't transcribe that voice note. Please type the message and send it again.",
                language,
            )
            return

        if not text.strip():
            await _reply(
                message.sender,
                "I couldn't hear clear speech in that voice note. Please type the message and send it again.",
                language,
            )
            return

        language = detect_language(text, default=language)
        _set_language(message.sender, language)

        request = AnalysisRequest(
            text=text,
            language=language,
            source=_analysis_source(),
            user_id=message.sender,
            district=district,
        )

    elif message.media_id:
        path = await download_media(message.media_id, message.filename)
        request = AnalysisRequest(
            text=text or "",
            language=language,
            source=_analysis_source(),
            media_path=str(path),
            media_type=message.mime_type or message.kind,
            user_id=message.sender,
            district=district,
        )

    else:
        request = AnalysisRequest(
            text=text,
            language=language,
            source=_analysis_source(),
            user_id=message.sender,
            district=district,
        )

    try:
        result = await _analyze(request)
    except (ImportError, ModuleNotFoundError):
        logger.exception("Analysis module not found")
        await _reply(message.sender, messages.ANALYSIS_UNAVAILABLE, language)
        return
    except Exception:
        logger.exception("Unexpected error occurred")
        await _reply(message.sender, messages.ANALYSIS_UNAVAILABLE, language)
        return

    conversation = golden_hour.get_conversation(message.sender)
    conversation.data["last_report_context"] = {
        "risk_level": result.risk_level.value,
        "scam_type": result.scam_type,
    }
    golden_hour.save_conversation(message.sender, conversation)

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

    if message.kind == "audio":
        try:
            spoken_text = _format_verdict(result)
            if language != "en":
                spoken_text = await translate(
                    spoken_text,
                    source="en",
                    target=language,
                )
            audio_reply = await tts(spoken_text, language=language)
            await send_audio(message.sender, audio_reply)
        except Exception:
            # The text verdict has already been sent.
            pass

    if result.risk_level.value == "high":
        guardian_number = _get_guardian_number(message.sender)

        if guardian_number and guardian_number != message.sender:
            try:
                await send_text(
                    guardian_number,
                    "Kavach alert: Someone who linked you as a trusted contact "
                    f"received a HIGH-risk verdict for a {result.scam_type} "
                    "message. Please check in with them. The original message "
                    "and files were not shared.",
                )
            except Exception:
                # Keep the user's safety-check reply working if the alert fails.
                pass


async def _handle_report(message: IncomingMessage, language: str) -> None:
    conversation = golden_hour.get_conversation(message.sender)
    context = conversation.data.get("last_report_context")

    if not isinstance(context, dict):
        await _reply(
            message.sender,
            "Send a message for a safety check first. If you have already lost money, call 1930 now.",
            language,
        )
        return

    try:
        result = AnalysisResult(
            risk_level=RiskLevel(context["risk_level"]),
            scam_type=context["scam_type"],
            explanation="",
        )
    except (KeyError, TypeError, ValueError):
        await _reply(message.sender, messages.GENERIC_ERROR, language)
        return

    destinations = router_rules.route(result)
    if not destinations:
        await _reply(
            message.sender,
            "If you lost money, call 1930 now. You can report a suspicious call, SMS, or WhatsApp message through https://www.sancharsaathi.gov.in/.",
            language,
        )
        return

    body = "\n\n".join(
        f"{item['name']}\n{item['action']}\n{item['url']}"
        for item in destinations
    )
    await _reply(message.sender, body, language)


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
            conversation = golden_hour.finish_evidence(message.sender)
            await _reply_buttons(
                message.sender,
                messages.EVIDENCE_FIELD_PROMPTS["transaction_id"],
                [("gh_skip", "Skip"), ("menu", "Menu")],
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
    field_index = next(
    (
        index
        for index, (state, _) in enumerate(_EVIDENCE_FIELDS)
        if state == conversation.state
    ),
    None,
    )

    if field_index is not None:
        _, field_name = _EVIDENCE_FIELDS[field_index]
        evidence_data = conversation.data.setdefault("evidence", {})

        evidence_data[field_name] = (
            "" if intent == "gh_skip" else message.text.strip()
        )

        next_index = field_index + 1
        if next_index < len(_EVIDENCE_FIELDS):
            next_state, next_field = _EVIDENCE_FIELDS[next_index]
            conversation.state = next_state
            golden_hour.save_conversation(message.sender, conversation)
            await _reply_buttons(
                message.sender,
                messages.EVIDENCE_FIELD_PROMPTS[next_field],
                [("gh_skip", "Skip"), ("menu", "Menu")],
                language,
            )
        else:
            conversation.state = "GH_BANK"
            golden_hour.save_conversation(message.sender, conversation)
            await _reply(message.sender, messages.EVIDENCE_REVIEW, language)
            await _reply(message.sender, messages.GOLDEN_HOUR_ASK_BANK, language)
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

        evidence_data = conversation.data.get("evidence", {}) or {}
        image_paths = [
            path
            for path in conversation.data.get("evidence_paths", [])
            if Path(path).suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        ]

        if image_paths:
            try:
                from kavach.analysis.bridge import evidence_summary

                extracted = await evidence_summary(image_paths)
                extracted_data = extracted.model_dump()

                # Keep manually collected details when they have a value.
                for key, value in evidence_data.items():
                    if value not in (None, "", [], {}):
                        extracted_data[key] = value

                evidence_data = extracted_data
            except Exception:
                # Keep going with the details already collected.
                pass

        evidence = EvidenceSummary(**evidence_data)
        golden_hour.save_case_evidence(
            message.sender,
            evidence.model_dump(),
        )

        bank_name = conversation.data.get("bank_name", "")
        complaint_draft = _make_complaint_draft(
            user_id=message.sender,
            bank_name=bank_name,
            acknowledgement_number=acknowledgement,
            evidence=evidence,
        )
        pdf_path = create_evidence_pdf(evidence, complaint_draft)

        # Save this last because it resets the conversation data.
        golden_hour.save_acknowledgement(message.sender, acknowledgement)

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

async def _handle_bait(message: IncomingMessage, language: str) -> None:
    from kavach.analysis.bridge import verify_bait

    request = AnalysisRequest(
        text=message.text,
        language=language,
        source=_analysis_source(),
        user_id=message.sender,
        district=_get_district(message.sender),
    )
    try:
        result = await verify_bait(request)
    except Exception:
        logger.exception("Scam Bait verification failed")
        await _reply(message.sender, messages.ANALYSIS_UNAVAILABLE, language)
        return

    await _reply(message.sender, _format_verdict(result), language)


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


async def _set_district(message: IncomingMessage, language: str) -> None:
    raw_district = message.text.partition(" ")[2].strip()
    if raw_district.casefold() in {"off", "clear", "remove"}:
        district = None
        reply = "Scam Pulse sharing is off. No new reports will be linked to a district."
    else:
        district = " ".join(raw_district.split())
        if (
            len(district) < 2
            or len(district) > 60
            or not any(character.isalpha() for character in district)
            or any(character.isdigit() for character in district)
        ):
            await _reply(
                message.sender,
                "To opt in, send district followed by your district name, such as district Pune. "
                "Send district off to opt out.",
                language,
            )
            return

        reply = (
            f"District saved as {district}. New medium- and high-risk text checks may be "
            "included in anonymous Scam Pulse reports. No GPS is collected. "
            "Send district off to opt out."
        )

    with session() as connection:
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
            (message.sender,),
        )
        connection.execute(
            "UPDATE users SET district = ? WHERE user_id = ?",
            (district, message.sender),
        )

    await _reply(message.sender, reply, language)


async def handle_message(message: IncomingMessage) -> None:
    """Entry point used by the WhatsApp webhook background task."""
    try:
        existing_language = _get_language(message.sender)
        if existing_language not in {"en", "hi"}:
            existing_language = "en"
        language = detect_language(message.text, default=existing_language)
        if language not in {"en", "hi"}:
            language = "en"
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

        if intent == "set_district":
            await _set_district(message, language)
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
            await _handle_bait(message, language)
            return

        if intent == "check_apk" or intent == "check":
            await _handle_check(message, language)
            return

        if intent == "report":
            await _handle_report(message, language)
            return
        await _reply(message.sender, messages.UNSUPPORTED, language)
    except Exception:
        # Avoid leaking exception details or user content in WhatsApp replies.
        try:
            await send_text(message.sender, messages.GENERIC_ERROR)
        except Exception:
            pass

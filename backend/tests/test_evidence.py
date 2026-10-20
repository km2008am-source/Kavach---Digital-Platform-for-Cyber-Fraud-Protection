from pathlib import Path

import httpx
import pytest
import respx
from PIL import Image

from kavach.analysis import ocr
from kavach.analysis.evidence import extract_evidence, extract_from_text
from tests.conftest import load_jsonl


async def test_ten_fake_receipts_at_least_eight_correct():
    receipts = load_jsonl("receipts_ocr.jsonl")
    correct = 0
    for r in receipts:
        ev = await extract_from_text(r["text"])
        correct += ev.transaction_id == r["expect"]["transaction_id"] and ev.amount == r["expect"]["amount"]
    assert len(receipts) == 10 and correct >= 8


async def test_missing_fields_are_listed_not_invented():
    ev = await extract_from_text("Payment successful ₹500")
    assert ev.amount == "₹500" and ev.transaction_id is None
    assert "transaction_id" in ev.missing_fields and "payee_upi" in ev.missing_fields


@respx.mock
async def test_llm_values_not_in_ocr_text_are_dropped(llm_on, llm_reply):
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply(
        {"transaction_id": "999999999999", "payee_name": "Ravi Kumar", "bank_name": "SBI"})))
    ev = await extract_from_text("Paid ₹700 to\nRavi Kumar\non 12 Oct 2026")
    assert ev.transaction_id is None                  # hallucinated: not in the text
    assert ev.payee_name == "Ravi Kumar"


async def test_unreadable_images_give_empty_extraction(tmp_path):
    bad = tmp_path / "x.png"
    bad.write_bytes(b"junk")
    ev = await extract_evidence([str(bad)])
    assert ev.transaction_id is None and len(ev.missing_fields) == 7


# ---- the 10 receipt screenshots handed to Member 1 (data/samples/receipts/) ----

RECEIPTS = Path(__file__).resolve().parents[2] / "data" / "samples" / "receipts"


def _tesseract_available() -> bool:
    try:
        ocr._langs()
        return True
    except Exception:
        return False


def test_ten_receipt_screenshots_exist_for_every_receipt():
    ids = [r["id"] for r in load_jsonl("receipts_ocr.jsonl")]
    assert len(ids) == 10
    for i in ids:
        with Image.open(RECEIPTS / f"{i}.png") as img:
            assert img.width >= 600 and img.height >= 400


@pytest.mark.skipif(not _tesseract_available(), reason="Tesseract OCR is not installed")
async def test_receipt_screenshots_at_least_eight_correct_via_ocr():
    correct = 0
    for r in load_jsonl("receipts_ocr.jsonl"):
        ev = await extract_evidence([str(RECEIPTS / f"{r['id']}.png")])
        correct += ev.transaction_id == r["expect"]["transaction_id"] and ev.amount == r["expect"]["amount"]
    assert correct >= 8


def test_ocr_misread_rupee_sign_is_recovered():
    from kavach.analysis.evidence import extract_regex
    assert extract_regex("Paid to Ravi\n=15,000\n12 Oct 2026")["amount"] == "₹15,000"
    assert extract_regex("PhonePe\n~12,000\nTransaction ID T1")["amount"] == "₹12,000"


async def test_ambiguous_seven_is_reported_missing_not_guessed():
    ev = await extract_from_text("Google Pay\nPaid to Manoj Traders\n7499\nUPI transaction ID 633322211100")
    assert ev.amount is None and "amount" in ev.missing_fields


@respx.mock
async def test_llm_cannot_fill_amount_without_a_currency(llm_on, llm_reply):
    respx.post(llm_on).mock(return_value=httpx.Response(200, json=llm_reply({"amount": "7499"})))
    ev = await extract_from_text("Google Pay\nPaid to Manoj Traders\n7499\nUPI transaction ID 633322211100")
    assert ev.amount is None


@pytest.mark.skipif(not _tesseract_available(), reason="Tesseract OCR is not installed")
async def test_receipt_amounts_are_never_wrong_only_missing():
    for r in load_jsonl("receipts_ocr.jsonl"):
        ev = await extract_evidence([str(RECEIPTS / f"{r['id']}.png")])
        assert ev.amount in (None, r["expect"]["amount"]), (r["id"], ev.amount)

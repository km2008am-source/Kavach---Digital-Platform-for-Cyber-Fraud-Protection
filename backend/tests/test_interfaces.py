"""Person 2's public interfaces, checked against the execution guide (section 5, "Function interfaces").

Person 1's WhatsApp layer uses its own team contract and reaches these through
`kavach.analysis.bridge` (tested in test_team_integration.py). Person 3's code does not
exist yet and is expected to call these guide signatures; if a test here fails, it would break.
"""
import inspect
import json
from pathlib import Path

import pytest

from kavach import llm
from kavach.analysis import bait, evidence, news_tagger, pulse, scam_check
from kavach.analysis.models import AnalysisResult, EvidenceExtraction, PulseAlert

SAMPLES = Path(__file__).resolve().parents[2] / "data" / "samples"

# (function, is_async, required positional params in order, return annotation)
GUIDE = [
    (scam_check.analyze, True, ["req"], AnalysisResult),
    (evidence.extract_evidence, True, ["image_paths"], EvidenceExtraction),
    (bait.verify, True, ["req"], AnalysisResult),
    (pulse.ingest, False, ["result", "text", "district", "reporter_hash"], None),
    (pulse.alerts, False, [], list[PulseAlert]),
    (news_tagger.tag, True, ["title", "summary"], dict),
    (llm.complete_json, True, ["system", "user"], dict),
]


@pytest.mark.parametrize("fn, is_async, params, returns", GUIDE, ids=lambda x: getattr(x, "__qualname__", ""))
def test_signature_matches_guide(fn, is_async, params, returns):
    sig = inspect.signature(fn)
    assert inspect.iscoroutinefunction(fn) is is_async
    required = [n for n, p in sig.parameters.items() if p.default is inspect.Parameter.empty]
    assert required == params                     # extra parameters must be optional
    assert sig.return_annotation == returns


def test_guide_defaults():
    assert inspect.signature(pulse.alerts).parameters["hours"].default == 72
    assert inspect.signature(llm.complete_json).parameters["timeout"].default == 12


def test_stub_was_removed_because_callers_use_the_real_pipeline():
    # Person 1's flows/engine.py imports kavach.analysis.scam_check.analyze directly.
    import importlib.util
    assert importlib.util.find_spec("kavach.analysis.stub") is None


def test_demo_cache_holds_no_held_out_messages():
    cache = json.loads((SAMPLES / "demo_cache.json").read_text("utf-8"))
    held = {json.loads(l)["text"] for name in ("heldout.jsonl", "heldout2.jsonl")
            for l in (SAMPLES / name).read_text("utf-8").splitlines() if l.strip()}
    assert cache and not held & set(cache)

# STAND-IN for Member 2's analysis/pulse.py (signatures from section 5).
# replay() starts a clock; alerts() grows the Coimbatore cluster from 5 to 38 reports over ~60 s,
# so Member 3's heatmap can be built and rehearsed. The real clustering lands at H18.
import time
from kavach.contracts import PulseAlert, ScamType

_replay_started: float | None = None
_SAMPLE = "Your <NUM> parcel is held by customs. Pay <AMOUNT> to <UPI> to release it."


def ingest(result, text, district, reporter_hash) -> None:
    return None


def replay() -> None:
    global _replay_started
    _replay_started = time.time()


def alerts(hours: int = 72) -> list[PulseAlert]:
    if _replay_started is None:
        return []
    elapsed = time.time() - _replay_started
    count = min(38, 5 + int(elapsed / 2))
    return [PulseAlert(cluster_id="cbe-courier-1", label="courier-customs scam, Tamil",
                       scam_type=ScamType.courier_customs, district="Coimbatore",
                       report_count=count, distinct_reporters=min(count, 3 + int(elapsed / 5)),
                       window_hours=2, confidence="confirmed" if count >= 25 else "emerging",
                       sample_text=_SAMPLE)]

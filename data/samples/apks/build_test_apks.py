"""Build harmless test APKs for the APK scanner. They contain NO code: only a binary
AndroidManifest.xml, which is all the static scanner reads. Safety rule from the guide:
never download real malware for testing.

    python data/samples/apks/build_test_apks.py

Writes (into this folder):
  rto_challan_test.apk  "RTO Challan": READ_SMS, RECEIVE_SMS, SYSTEM_ALERT_WINDOW + an
                        accessibility service (the banking-trojan pattern)
  clean_notes_test.apk  "Simple Notes": INTERNET only
  not_an_apk.apk        a renamed text file (the scanner must not crash)
"""
import struct
import zipfile
from pathlib import Path

ANDROID_NS = "http://schemas.android.com/apk/res/android"
HERE = Path(__file__).resolve().parent


class _Axml:
    """Minimal Android binary XML (AXML) writer: string pool + namespace + elements."""

    def __init__(self) -> None:
        self.strings: list[str] = []
        self.body = b""

    def s(self, value: str) -> int:
        if value not in self.strings:
            self.strings.append(value)
        return self.strings.index(value)

    def start_ns(self) -> None:
        self.body += struct.pack("<HHIIiII", 0x0100, 16, 24, 1, -1, self.s("android"), self.s(ANDROID_NS))

    def end_ns(self) -> None:
        self.body += struct.pack("<HHIIiII", 0x0101, 16, 24, 1, -1, self.s("android"), self.s(ANDROID_NS))

    def start(self, name: str, attrs: list[tuple[str | None, str, str]]) -> None:
        raw = b""
        for ns, key, value in attrs:
            ns_idx = self.s(ns) if ns else -1
            v = self.s(value)
            # typed value: size=8, res0=0, dataType=0x03 (string), data=string index
            raw += struct.pack("<iiiHBBI", ns_idx, self.s(key), v, 8, 0, 0x03, v)
        header = struct.pack("<HHIIiiIHHHHHH", 0x0102, 16, 36 + len(raw), 1, -1, -1, self.s(name),
                             0x14, 0x14, len(attrs), 0, 0, 0)
        self.body += header + raw

    def end(self, name: str) -> None:
        self.body += struct.pack("<HHIIiiI", 0x0103, 16, 24, 1, -1, -1, self.s(name))

    def build(self) -> bytes:
        data, offsets = b"", []
        for value in self.strings:
            enc = value.encode("utf-8")
            offsets.append(len(data))
            data += bytes([len(value), len(enc)]) + enc + b"\x00"   # all test strings are < 128 chars
        data += b"\x00" * (-len(data) % 4)
        strings_start = 28 + 4 * len(self.strings)
        pool = struct.pack("<HHIIIIII", 0x0001, 28, strings_start + len(data), len(self.strings), 0,
                           0x100, strings_start, 0) + b"".join(struct.pack("<I", o) for o in offsets) + data
        return struct.pack("<HHI", 0x0003, 8, 8 + len(pool) + len(self.body)) + pool + self.body


def manifest(package: str, label: str, permissions: list[str], accessibility: bool) -> bytes:
    x = _Axml()
    x.start_ns()
    x.start("manifest", [(None, "package", package), (ANDROID_NS, "versionName", "1.0")])
    for p in permissions:
        x.start("uses-permission", [(ANDROID_NS, "name", p)])
        x.end("uses-permission")
    x.start("application", [(ANDROID_NS, "label", label)])
    if accessibility:
        x.start("service", [(ANDROID_NS, "name", ".HelperService"),
                            (ANDROID_NS, "permission", "android.permission.BIND_ACCESSIBILITY_SERVICE")])
        x.start("intent-filter", [])
        x.start("action", [(ANDROID_NS, "name", "android.accessibilityservice.AccessibilityService")])
        x.end("action")
        x.end("intent-filter")
        x.end("service")
    x.end("application")
    x.end("manifest")
    x.end_ns()
    return x.build()


def write_apk(path: Path, manifest_bytes: bytes) -> None:
    # Fixed timestamp: rebuilding gives byte-identical files, so tests never dirty the repo.
    info = zipfile.ZipInfo("AndroidManifest.xml", date_time=(2026, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(info, manifest_bytes)


def main() -> None:
    write_apk(HERE / "rto_challan_test.apk", manifest(
        "com.example.rtochallan", "RTO Challan",
        ["android.permission.READ_SMS", "android.permission.RECEIVE_SMS",
         "android.permission.SYSTEM_ALERT_WINDOW", "android.permission.INTERNET"], accessibility=True))
    write_apk(HERE / "clean_notes_test.apk", manifest(
        "com.example.simplenotes", "Simple Notes", ["android.permission.INTERNET"], accessibility=False))
    (HERE / "not_an_apk.apk").write_text("this is a text file renamed to .apk\n", encoding="utf-8")
    print("wrote test APKs to", HERE)


if __name__ == "__main__":
    main()

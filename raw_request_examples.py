"""Raw request examples for the supplied local adapter. Standard library only.

Before running, write expected replies from CONTRACT.md. This file prints
actual replies and saved rows, without setting the expectations for you.
The cases run against the unchanged starter because validation precedes storage.
"""
from pathlib import Path
from tempfile import TemporaryDirectory

from capstone_harness import LocalService, show
from failed_write_check import snapshot
from store import Store


CASES = [
    ("repeated client header", "GET", "/s/lesson", [
        ("X-Client-Id", "reader_a"), ("X-Client-Id", "reader_b")], b""),
    ("missing length header", "POST", "/links", [], b"{}"),
    ("non-numeric length", "POST", "/links", [("Content-Length", "many")], b"{}"),
    ("zero length", "POST", "/links", [("Content-Length", "0")], b""),
    ("length above the limit", "POST", "/links", [("Content-Length", "1025")], b""),
    ("invalid JSON with a correct length", "POST", "/links", [
        ("Content-Length", "1")], b"{"),
]


def run_examples():
    with TemporaryDirectory(prefix="link-raw-requests-") as folder:
        database = Path(folder) / "raw.sqlite3"
        with LocalService(Store(database), clock=lambda: 120) as service:
            show("Saved rows before requests", snapshot(database))
            for label, method, path, headers, body in CASES:
                show("Case", {"label": label, "method": method, "path": path,
                              "headers": headers, "body": body.decode("ascii")})
                show("Actual reply", service.raw_request(method, path, headers, body))
            show("Saved rows after requests", snapshot(database))
        show("HTTP thread stopped", not service.thread.is_alive())
    show("Temporary database removed", not database.exists())


if __name__ == "__main__":
    run_examples()

"""Original local test helper for the supplied link-service starter.

Prepared for the Welica capstone material, November 2026. Standard library only.
This file supplies test plumbing, not a Store implementation.
"""
import json
import threading
from http.client import HTTPConnection

from server import make_server


class LocalService:
    """Start the supplied HTTP server and always stop its thread on exit."""

    def __init__(self, store, clock=lambda: 120):
        self.server = make_server(store, clock=clock)
        self.thread = threading.Thread(target=self.server.serve_forever)

    def __enter__(self):
        try:
            self.thread.start()
        except BaseException:
            self.server.server_close()
            raise
        return self

    def request(self, method, path, data=None, client=None):
        connection = HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=10)
        headers = {} if client is None else {"X-Client-Id": client}
        body = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        try:
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            return {
                "status": response.status,
                "headers": dict(response.getheaders()),
                "body": response.read().decode("utf-8"),
            }
        finally:
            connection.close()

    def raw_request(self, method, path, headers=(), body=b""):
        """Send ordered header pairs and bytes without automatic length headers.

        Use this for repeated headers, missing Content-Length or a deliberately
        invalid length. Supply the complete header list you intend to test.
        The connection adds Host, but does not add Content-Length or Content-Type.
        Do not send fewer bytes than a valid positive Content-Length promises.
        That would leave the local server waiting for the rest of the body.
        """
        if not isinstance(body, bytes):
            raise TypeError("raw_request body must be bytes")
        connection = HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=10)
        try:
            connection.putrequest(method, path, skip_accept_encoding=True)
            for name, value in headers:
                connection.putheader(name, value)
            connection.endheaders(body)
            response = connection.getresponse()
            return {
                "status": response.status,
                "headers": dict(response.getheaders()),
                "body": response.read().decode("utf-8"),
            }
        finally:
            connection.close()

    def __exit__(self, *error):
        try:
            self.server.shutdown()
        finally:
            self.server.server_close()
            self.thread.join(timeout=10)
        if self.thread.is_alive():
            raise RuntimeError("The HTTP server thread did not stop")


def show(label, value):
    print(label + ": " + json.dumps(value, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    from pathlib import Path
    from tempfile import TemporaryDirectory
    from store import Store

    with TemporaryDirectory() as folder:
        with LocalService(Store(Path(folder) / "health.sqlite3")) as service:
            result = service.request("GET", "/health")
            show("Health response", result)
            assert result["status"] == 200
            assert json.loads(result["body"]) == {"status": "ok"}
        show("HTTP thread stopped", not service.thread.is_alive())

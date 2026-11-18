"""Supplied local HTTP adapter. Start here only to see the routes."""
import argparse
import json
import re
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from store import Store

CODE = re.compile(r"[a-z][a-z0-9]{2,15}\Z")
CLIENT = re.compile(r"[a-z0-9_-]{1,24}\Z")


def make_server(store, port=0, clock=time.time):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, data=None, location=None):
            body = b"" if data is None else json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            if data is not None:
                self.send_header("Content-Type", "application/json")
            if location is not None:
                self.send_header("Location", location)
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self.dispatch()

        def do_POST(self):
            self.dispatch()

        def dispatch(self):
            try:
                self.route()
            except NotImplementedError as error:
                self.reply(501, {"error": str(error)})
            except Exception:
                self.reply(500, {"error": "internal_error"})

        def route(self):
            if self.command == "GET" and self.path == "/health":
                return self.reply(200, {"status": "ok"})
            if self.command == "POST" and self.path == "/links":
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if not 1 <= size <= 1_024:
                        raise ValueError()
                    data = json.loads(self.rfile.read(size))
                    code, destination = data["code"], data["destination"]
                    url = urlsplit(destination)
                    if (set(data) != {"code", "destination"}
                            or not CODE.fullmatch(code)
                            or len(destination) > 200
                            or url.scheme != "https"
                            or url.netloc not in {"example.org", "example.net"}
                            or any(ord(char) < 33 or ord(char) > 126
                                   for char in destination)):
                        raise ValueError()
                except (ValueError, TypeError, KeyError, AttributeError):
                    return self.reply(400, {"error": "invalid_link"})
                created = store.create(code, destination)
                return self.reply(201 if created else 409,
                                  {"code": code} if created else {"error": "code_exists"})
            for prefix in ("/s/", "/stats/"):
                if self.command == "GET" and self.path.startswith(prefix):
                    code = self.path[len(prefix):]
                    if not CODE.fullmatch(code):
                        return self.reply(404, {"error": "not_found"})
                    if prefix == "/stats/":
                        result = store.stats(code)
                        return self.reply(200, result) if result is not None else self.reply(
                            404, {"error": "not_found"})
                    clients = self.headers.get_all("X-Client-Id", [])
                    if len(clients) != 1 or not CLIENT.fullmatch(clients[0]):
                        return self.reply(400, {"error": "invalid_client"})
                    status, destination = store.resolve(clients[0], code, clock())
                    if status == 302:
                        return self.reply(status, location=destination)
                    error = "request_limit" if status == 429 else "not_found"
                    return self.reply(status, {"error": error})
            self.reply(404, {"error": "not_found"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", default="links.sqlite3")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--test-clock", type=float, default=None,
                        help="Use one fixed time for local checks only")
    args = parser.parse_args()
    if args.test_clock is not None and (args.test_clock < 0 or not args.test_clock < float("inf")):
        parser.error("--test-clock must be a finite non-negative number")
    clock = time.time if args.test_clock is None else lambda: args.test_clock
    server = make_server(Store(args.database), args.port, clock=clock)
    print("Local service: http://127.0.0.1:%s" % server.server_port, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

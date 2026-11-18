"""Small starter checks. Add your own boundary, parallel and recovery checks."""
import csv
import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from pathlib import Path

from server import make_server
from store import Store


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.server = make_server(Store(Path(self.folder.name) / "links.sqlite3"))
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.folder.cleanup()

    def request(self, method, path, data=None, client=None):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=10)
        headers = {} if client is None else {"X-Client-Id": client}
        body = None if data is None else json.dumps(data)
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_health(self):
        self.assertEqual(self.request("GET", "/health")[0], 200)

    def test_create_redirect_and_count(self):
        with Path(__file__).with_name("fixtures.csv").open(newline="") as source:
            link = next(csv.DictReader(source))
        status, _, _ = self.request("POST", "/links", link)
        self.assertEqual(status, 201, "Complete Store.create first")
        status, headers, _ = self.request("GET", "/s/" + link["code"], client="reader_a")
        self.assertEqual(status, 302)
        self.assertEqual(headers["Location"], link["destination"])
        status, _, body = self.request("GET", "/stats/" + link["code"])
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["clicks"], 1)

    def test_absent_code(self):
        self.assertEqual(self.request("GET", "/s/absent", client="reader_a")[0], 404)


if __name__ == "__main__":
    unittest.main()

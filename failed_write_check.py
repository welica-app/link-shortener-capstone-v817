"""Check saved counts after injected database failures. Standard library only.

Run python3 failed_write_check.py after completing Store. No settings are needed.
Each probe uses a new temporary database, never the demonstration database.
This supplies test plumbing, not an implementation of the three Store methods.
"""
import json
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

from capstone_harness import LocalService, show
from store import Store


def quoted(name):
    return '"' + name.replace('"', '""') + '"'


def snapshot(database):
    """Read actual table values without assuming the learner's schema."""
    connection = sqlite3.connect(str(database), timeout=10)
    try:
        result = {}
        tables = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        for (table,) in tables:
            cursor = connection.execute("SELECT * FROM " + quoted(table))
            columns = [column[0] for column in cursor.description]
            rows = [[{"bytes_hex": value.hex()} if isinstance(value, bytes) else value
                     for value in row] for row in cursor.fetchall()]
            # Keep binary values readable without requiring one column type.
            result[table] = {"columns": columns,
                             "rows": sorted(rows, key=repr)}
        return result
    finally:
        connection.close()


class WriteProbe:
    """Use connection-local triggers to observe or abort a row-write attempt.

    The learner's SQL and transaction control are left alone. Each trigger calls
    a test function, then SQLite itself raises ABORT at the selected attempt.
    """

    def __init__(self, store):
        self.store = store
        self.events = []
        self.fail_at = None
        self.fired = False
        self.connections = []
        self.original_connect = store.connect
        self.had_instance_connect = "connect" in store.__dict__
        self.previous_instance_connect = store.__dict__.get("connect")

    def reset(self, fail_at=None):
        self.events = []
        self.fail_at = fail_at
        self.fired = False

    def attempt(self, table, operation):
        self.events.append({"attempt": len(self.events) + 1,
                            "table": table, "operation": operation})
        should_fail = self.fail_at == len(self.events)
        if should_fail:
            self.fired = True
        return int(should_fail)

    def connect(self):
        connection = self.original_connect()
        names = []
        self.connections.append((connection, names))
        connection.create_function("capstone_test_fail", 2, self.attempt)
        tables = connection.execute(
            "SELECT name, sql FROM main.sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
        for table, definition in tables:
            if definition and definition.lstrip().upper().startswith(
                    "CREATE VIRTUAL TABLE"):
                raise RuntimeError(
                    "This trigger helper cannot inspect virtual tables. "
                    "Use another database failure check for that design.")
            for operation in ("INSERT", "UPDATE", "DELETE"):
                name = "capstone_probe_" + str(len(names))
                table_literal = "'" + table.replace("'", "''") + "'"
                connection.execute(
                    "CREATE TEMP TRIGGER " + quoted(name) + " BEFORE "
                    + operation + " ON main." + quoted(table)
                    + " WHEN capstone_test_fail(" + table_literal + ", '"
                    + operation + "') = 1 BEGIN "
                    "SELECT RAISE(ABORT, 'capstone injected write failure'); END")
                names.append(name)
        return connection

    def __enter__(self):
        self.store.connect = self.connect
        return self

    def __exit__(self, *error):
        # Restore the Store even when a request or assertion raises.
        if self.had_instance_connect:
            self.store.connect = self.previous_instance_connect
        else:
            del self.store.connect
        self.fail_at = None
        for connection, names in self.connections:
            try:
                # Closed connections have already discarded their TEMP triggers.
                for name in names:
                    connection.execute("DROP TRIGGER IF EXISTS temp." + quoted(name))
                connection.create_function("capstone_test_fail", 2, None)
            except sqlite3.ProgrammingError:
                pass
        # Do not close learner connections here. Closing one could roll back a
        # leaked transaction and conceal a fault before the state observations.


def expect(response, status):
    assert response["status"] == status, (
        "Expected status %s, got %s. Read the response and complete or fix "
        "your Store methods before relying on this check." % (status, response))


DESTINATION = "https://example.org/guide/start"


def saved_clicks(service):
    response = service.request("GET", "/stats/harbor")
    expect(response, 200)
    data = json.loads(response["body"])
    assert data["code"] == "harbor" and data["destination"] == DESTINATION
    assert type(data["clicks"]) is int
    return data["clicks"]


def redirect(service):
    return service.request("GET", "/s/harbor", client="reader_a")


def accepted(response):
    expect(response, 302)
    assert response["headers"].get("Location") == DESTINATION
    assert response["body"] == ""


def scenario(store_factory, prior, fail_at=None):
    """A fresh file and Store for every observed or failed request."""
    with TemporaryDirectory(prefix="capstone-write-") as folder:
        database = Path(folder) / "failure.sqlite3"
        store = store_factory(database)
        with LocalService(store, clock=lambda: 120) as service:
            expect(service.request("POST", "/links", {
                "code": "harbor", "destination": DESTINATION}), 201)
            for _ in range(prior):
                accepted(redirect(service))
            before = saved_clicks(service)
            assert before == prior
            show("Saved clicks before request", before)
            show("Database values before request", snapshot(database))
            with WriteProbe(store) as probe:
                probe.reset(fail_at)
                try:
                    response = redirect(service)
                finally:
                    # Disarm before any observation or retry, even on an error.
                    probe.fail_at = None
                events = list(probe.events)
                show("Write attempts", events)
                show("Failure reached", probe.fired)
                show("Request response", response)
                if fail_at is not None:
                    assert probe.fired, "A previously observed write was not reached"
                else:
                    assert events, "No writes found through Store.connect()"
                    accepted(response)
            show("Connection hook restored", store.connect == probe.original_connect)
            assert store.connect == probe.original_connect
            # A new Store and server read persisted core state. This avoids
            # accepting an allowance that exists only in the original object.
            with LocalService(store_factory(database), clock=lambda: 120) as reader:
                after = saved_clicks(reader)
                show("Saved clicks after request", after)
                show("Database values after request", snapshot(database))
                # A handled failure may be retried inside Store and succeed.
                # An unsuccessful request must leave both core changes unsaved.
                if response["status"] == 302:
                    accepted(response)
                    completed = 1
                else:
                    expect(response, 500)
                    assert json.loads(response["body"]) == {"error": "internal_error"}
                    assert "Location" not in response["headers"]
                    completed = 0
                assert after == before + completed, "Saved clicks disagree with response"
                # Fill the persisted window without assuming any table layout.
                remaining = 5 - prior - completed
                replies = [redirect(reader) for _ in range(remaining + 1)]
                show("Retry statuses", [reply["status"] for reply in replies])
                for reply in replies[:remaining]:
                    accepted(reply)
                limited = replies[-1]
                expect(limited, 429)
                assert "Location" not in limited["headers"]
                assert json.loads(limited["body"]) == {"error": "request_limit"}
                final = saved_clicks(reader)
                show("Saved clicks after retries", final)
                assert final == 5, "Clicks and saved allowance disagree"
                show("Saved allowance before retries, verified by filling window", prior + completed)
                show("Saved allowance used after retries", 5)
                show("Database values after retries", snapshot(database))
            show("Fresh-reader HTTP thread stopped", not reader.thread.is_alive())
            assert not reader.thread.is_alive()
        show("HTTP thread stopped", not service.thread.is_alive())
        assert not service.thread.is_alive()
    show("Temporary database removed", not database.exists())
    assert not database.exists()
    return events


def run_check(store_factory=Store):
    """Discover normal writes, then fail each in its own fresh database."""
    for prior, label in ((0, "first redirect"), (1, "later redirect")):
        show("Discovering writes for", label)
        events = scenario(store_factory, prior)
        for number in range(1, len(events) + 1):
            show("Failing write", {"request": label, "attempt": number})
            scenario(store_factory, prior, number)
    show("Result", "PASS: saved clicks and allowance agree after failures and retries")


if __name__ == "__main__":
    run_check()

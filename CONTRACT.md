# Link service contract

You are building a small link service for a local demonstration. A link must keep its destination and click count when you stop and start the service. A request limit must still work when requests arrive together.

## Supplied code

The HTTP adapter in `server.py` accepts requests and checks their shape. Complete `create`, `resolve` and `stats` in `store.py`. Keep those method names, inputs and return values. Keep `protected_storage.py` unchanged. It sets up the tables and protects complete writes. Read `STORAGE_GUIDE.md` before completing the marked methods.

Each call may run on a different thread. Use `self.write()` for creating a link and `self.read()` for reading statistics. These prepared context managers open and close a connection for that call. `self.write()` also starts a transaction and commits or rolls back before closing. A transaction is a group of database changes that either all finish or all fail. For redirects, call `self.accept_redirect(client, code, now)` and return its result. It handles the lookup, limit and both saved changes inside one protected transaction. Do not add separate row changes to `resolve`.

Use one server process and one `Store` object. You do not need to support several processes writing together. Use a file database, not an in-memory database.

## Routes

| Request | Result |
| --- | --- |
| `GET /health` | 200 and `{"status":"ok"}`. |
| `POST /links` | 201 and `{"code":"yourcode"}` when saved. |
| `GET /s/{code}` | 302 with the saved destination in the `Location` header when accepted. The body is empty. |
| `GET /stats/{code}` | 200 with `code`, `destination` and the integer `clicks`. |

A POST must have a `Content-Length` header that is an integer from 1 to 1,024 bytes. A missing, invalid or out-of-range length returns 400. The server reads that many bytes as JSON. A POST body is a JSON object with exactly two text fields, `code` and `destination`. The supplied adapter does not require or check a request `Content-Type` header. A code starts with a lower-case letter. It has 3 to 16 lower-case letters or digits. An existing code returns 409 and `{"error":"code_exists"}`, even if its destination is unchanged. It must not change any saved data.

A destination is an `https` address whose host is exactly `example.org` or `example.net`, with no port or login details. It has at most 200 printable ASCII characters and no spaces. It may contain a path, query or fragment. Save it exactly as supplied. The server checks the address with Python's `urlsplit`. Its scheme must read as `https` and its network location must be exactly `example.org` or `example.net`, including letter case. These hosts are reserved for examples. Never fetch the destination during a check.

An invalid POST returns 400 and `{"error":"invalid_link"}`. Unknown paths and absent codes return 404 and `{"error":"not_found"}`. A malformed code in a GET route returns 404 before any client check. The routes above must match the full path as written. A query string or extra slash on a route is not stripped. Only GET and POST are part of the task. An unmatched GET or POST returns 404. Other HTTP methods use the supplied HTTP server's default response and are outside the task.

## Client and request limit

Every request to a valid `/s/{code}` path needs exactly one `X-Client-Id` header. Its value has 1 to 24 lower-case letters, digits, underscores or hyphens. Missing, repeated or invalid values return 400 and `{"error":"invalid_client"}`. Invalid headers are checked before looking up the code. Different values are different clients. This supplied label is only for synthetic local testing. It is not a real identity or security control.

Limit each client to **five accepted redirects per fixed 60-second window across all codes**. The server supplies `now`, the number of seconds since the Unix time origin. A window starts at an exact multiple of 60. It includes that starting instant and ends just before the next multiple. For example, the window starting at 120 includes 120 and 179.999, but not 180.

For a valid client, first decide whether the code exists. An absent code returns 404 and does not use the limit. For an existing code, a request within the limit returns 302. The next request beyond the limit returns 429 and `{"error":"request_limit"}` with no `Location` header. A rejected request does not use more of the limit and does not add a click.

Every accepted redirect adds exactly one click to that code and uses exactly one place in the client's window. A click means the service accepted the redirect, even if the caller does not open its destination. The count and limit must agree when requests arrive together. `/health`, `/links` and `/stats/` never use the limit or add clicks.

Save links, clicks and window use in the database. Restarting in the same window must not reset the limit. A new time window starts with a fresh allowance. Keep old windows for this small project. No cleanup job is required. Test times are non-negative and do not go backwards. A failed database operation must not leave half of a redirect saved. Do not return a successful response before the required changes are saved.

## Storage method results and response details

Keep the public method inputs and results below. Keep the prepared tables unchanged.

| Method | Result |
| --- | --- |
| `create(code, destination)` | `True` once a new link is saved, or `False` for an existing code. |
| `resolve(client, code, now)` | `(302, saved_destination)`, `(404, None)` or `(429, None)`. |
| `stats(code)` | `{"code": code, "destination": saved_destination, "clicks": integer}` or `None` if absent. |

The adapter sends JSON with `Content-Type: application/json`. It sends a `Content-Length` on every response. A redirect has an empty body and the `Location` header, with no JSON content type. Error responses have no `Location` header. JSON spacing and key order do not matter.

An unfinished method raises `NotImplementedError`. The adapter returns 501 with an `error` field containing that method's message. An unhandled exception returns 500 and `{"error":"internal_error"}`. The prepared storage code reports a database failure without retrying. It must never return 302 with only part of the required state saved. A failed request must leave both the click and the used allowance unchanged. Unrelated diagnostic records may change.

## Supplied failure check

After completing the three methods, run:

```text
python3 failed_write_check.py
```

No options or changes to the helper are needed. It starts the actual supplied HTTP server with a fresh temporary database for each probe. It observes the writes made through `Store.connect()` during a normal first redirect and a normal later redirect in the same window. Then it runs a separate probe for every observed write position, causing SQLite to reject that row write once. The prepared storage code does not retry the failed request. The helper later sends fresh requests to check the saved allowance.

The command prints the write attempts, response, saved click count and database values before the request, after it and after retries. A new Store object and local HTTP server read the saved values, then fill the same client's window to check that the saved allowance agrees with the clicks. It accepts one atomic write, several writes in any order, and a handled failure that eventually saves a coherent success. It does not compare every row for equality. You do not need an artificial extra write or a particular table layout.

The helper restores the connection hook and stops the local HTTP thread, including when a check fails. It disarms failure injection before reading results. It removes its temporary database at the end and never opens your demonstration database. Your Store methods use the prepared context managers to close their connections.

This helper uses temporary SQLite triggers on ordinary tables. It covers writes reached in the two normal request paths, including each row of a multi-row write. It does not simulate a disk, commit, process or network failure, inspect virtual tables or databases attached to another file, or discover tables created after a connection opens. Keep the project's ordinary file database and connection contract. Record these limits in your release note. You are not asked to invent more failure injection. Add your own input and time checks. Use the prepared parallel and restart patterns in `walkthrough.py`, then extend the assertions for the cases you choose.

For a small chosen-time example, use `capstone_harness.py`. It supplies `LocalService`, which starts the actual adapter on a free local port, sends requests without following redirects and stops the server on exit. You can pass `clock=lambda: 120` or another chosen clock. Run `python3 capstone_harness.py` to see its health check before completing the methods.

## Checks and release

Use `http.client` so your checks can read redirect status and headers without following the redirect. For time checks, pass a clock function into `make_server`, or call `resolve` with a chosen time. Do not wait a real minute. For parallel checks, use the barrier and request pattern in `walkthrough.py`. The barrier holds each call until the whole group is ready. Then compare the replies with both saved counts. Add your own checks for the rules above. The supplied smoke checks are only a start. `WALKTHROUGH.md` explains the ordinary request, failed write, parallel call and stop/restart examples you can run after completing the methods.

Run the same checks again from a fresh database. Also stop the service, restart it with the same database and check what survived. Keep local results for a working version and for a change you rejected. A failed required check blocks release until you fix it or explain why the check itself was wrong and rerun it.

Your release note names the version, how to run and test it, the result, any limits and how to stop and recover. Keep the code and note together. You can share public source with local run evidence, or add a short recording that opens without a login. A live hosted service is not required.

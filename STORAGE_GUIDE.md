# Work inside the storage protection

## Start with create and stats

Open `store.py`. Replace only the `raise NotImplementedError(...)` lines in `create` and `stats`. Keep the class line and method inputs unchanged.

A class groups data and methods. `Store(ProtectedStorage)` gives Store the prepared storage methods. The import at the top makes that prepared class available. Within a method, `self` means this Store object. So `self.write()` calls this object's prepared writing method.

For `create(code, destination)`, put the lookup and insertion inside `with self.write() as connection:`. Return `False` if the code exists. Otherwise insert its code and destination, then return `True`. The table starts its click count at zero.

For `stats(code)`, read the row inside `with self.read() as connection:`. Return `None` when it is absent. Otherwise return a dictionary with `code`, `destination` and the saved integer `clicks`.

Both contexts open a connection for the current call and close it when the body ends. The writing context also commits or rolls back. Even a `return` waits for that cleanup. Keep `protected_storage.py` unchanged.

`connection.execute` sends SQL to the database. Pass values separately with `?` placeholders. For example, this reads one destination:

```python
row = connection.execute(
    "SELECT destination FROM links WHERE code = ?", (code,)
).fetchone()
```

The comma in `(code,)` makes a tuple with one value. A tuple holds values in order. `fetchone()` returns one row as a tuple, or `None` when no row matches. Check for `None` before using `row[0]`. With several selected columns, tuple positions follow their order in `SELECT`. An insertion uses `execute` without `fetchone()`.

Now write those two methods and run the focused check from the README.

## Connect resolve next

`resolve(client, code, now)` calls `self.accept_redirect(client, code, now)` and returns its result unchanged. The prepared method owns the lookup, limit and both saved changes. Do not add separate row changes here.

Its tuple is `(302, destination)`, `(404, None)` or `(429, None)`. The server reads the two values as `status, destination`, in that order. `None` means there is no destination to send. Keep this returned shape, just as you keep the boolean from `create` and the dictionary from `stats`.

Trace these three method calls in `server.py`, then run the full smoke suite. Read the route rules when you start choosing your own tests.

## Before the overlap and failure checks

Two requests can reach the same service together. Both may try to use the last place in one client's allowance. Use the prepared operation rather than design your own locking policy.

The server constructs one Store object with the database path. The inherited `__init__` method creates missing tables. It does not erase existing tables, so a later Store can read earlier changes. You do not need to add a constructor.

The `links` table has one row per code. Its primary key stops two rows having the same code. The `buckets` table has one row per client and window start. Its combined key keeps that pair unique. `accepted` records used allowance for the pair.

`self.write()` takes the Store's write lock before reading values for a change. Only one writer using this Store can enter that part at a time. It opens a connection for the calling thread, then runs `BEGIN IMMEDIATE` before the lookup. The database reserves the write transaction there.

The body of your `with` statement runs next. When it finishes, the context manager commits, then closes the connection. If the body or commit raises an error, it rolls back any active transaction and closes the connection. It raises the error again so the server returns 500. It does not retry the request itself.

`self.read()` also opens a fresh connection and closes it when the body ends. Each calling thread gets its own connection. Do not save a connection on Store or close it manually inside a context manager.

`accept_redirect` checks existence, reads the client's window use and decides whether the redirect is allowed. It adds the click and used allowance in the same write transaction. It commits before a successful tuple reaches the server. Keep that method and the tables unchanged.

Use one server process and one Store object. The project does not ask you to design distributed storage, independent retries or a production hosting system.

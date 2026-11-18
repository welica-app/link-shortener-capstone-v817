# Work inside the storage protection

Two requests can reach the same service together. Both may try to use the last place in one client's allowance. The storage code must keep the saved allowance and click count together. You use the prepared method for that operation, rather than design your own locking policy.

## The files and the class

An import makes a name from another file available here. `from protected_storage import ProtectedStorage` lets `store.py` use the prepared storage class. You do not need another package.

A class groups related data and methods. `class Store(ProtectedStorage)` means that Store also has the methods of ProtectedStorage. A method is a function on an object. In a method, `self` means the particular Store object handling the call. So `self.database` is that object's database path, and `self.write()` calls its prepared writing method.

The server constructs one Store object. It passes the database path to the prepared `__init__` method. That method creates missing tables. It does not erase existing tables, so a later Store can read earlier changes.

Leave the class line, method names and argument lists as they are. Replace each `raise NotImplementedError(...)` with the required method body. You do not need to add a constructor.

## What you add

`create(code, destination)` looks for the code and inserts a new link if it is absent. Put the lookup and insertion inside `with self.write() as connection:`. Return `True` for a saved new link and `False` for an existing one. A new link's click count starts at zero through the table default. Keep input values out of SQL text by passing them separately with `?` placeholders.

`resolve(client, code, now)` calls `self.accept_redirect(client, code, now)` and returns its result unchanged. This bridge is deliberately small. The prepared method owns the request limit and both row changes. Do not duplicate those changes here.

`stats(code)` reads the row inside `with self.read() as connection:`. Return `None` for an absent code. Otherwise return a dictionary with `code`, `destination` and the saved integer `clicks`.

## Send SQL through the connection

`connection.execute` sends a statement to the database. The second argument holds the values that replace `?` placeholders. Keep the comma in `(code,)`. It makes a tuple containing one value.

For example, this reads just a destination:

```python
row = connection.execute(
    "SELECT destination FROM links WHERE code = ?", (code,)
).fetchone()
```

`fetchone()` returns one matching row as a tuple, or `None` when there is no row. In this example, `row[0]` is the destination if a row exists. Check for `None` before reading a position. A query for several columns returns those columns in the order written in `SELECT`.

An insertion also uses `connection.execute`. It does not need `fetchone()` because you are adding a row rather than reading one. The writing context commits when the body finishes.

## What the prepared code owns

The `links` table has one row per code. Its primary key stops two rows having the same code. The `buckets` table has one row per client and window start. Its combined key keeps that pair unique. The `accepted` column records used allowance for that pair.

`self.write()` takes the Store's write lock before reading values for a change. A lock lets only one writer enter this part at a time. It opens a connection for the current thread, then runs `BEGIN IMMEDIATE` before the lookup. The database reserves the write transaction at that point.

The body of your `with` statement runs next. When it finishes, the prepared code commits the transaction, then closes the connection. Even if your body contains a `return`, the context manager finishes before the method returns to its caller.

If the body or commit raises an error, the prepared code rolls back any active transaction and closes the connection. It raises the error again so the server returns 500. It does not try the request again itself.

`self.read()` also opens a fresh connection and closes it when the `with` statement ends. A separate calling thread gets its own connection. Do not save a connection on the Store object or close it manually inside either context manager.

`accept_redirect` checks existence, reads the client's window use and decides whether the redirect is allowed. It adds the click and used allowance in the same write transaction. It commits before a successful tuple reaches the server. Keep that method and the table design unchanged.

## Read the returned shapes

A tuple holds values in order. `(302, destination)` has two values. The server reads them as `status, destination`. `(404, None)` and `(429, None)` also have two values. `None` means there is no destination to send for that result. Keep that order and shape.

The boolean from `create` tells the server which response to send. The dictionary from `stats` provides named values for its reply. These shapes are part of the interface between the files. They are not choices to change in this project.

Use one server process and one Store object with this protection. The checks do not prepare you to design distributed storage, independent retries or a production hosting system.

# Try the checking helpers

First complete the marked methods. Then run:

```text
python3 -m unittest smoke_test -v
python3 walkthrough.py finished
```

The second command runs four guided examples through the actual local web server. It uses a new temporary database for each scenario and removes the database afterwards. It never follows a redirect to its destination. Read the functions in `walkthrough.py` alongside these explanations, then use their patterns in your own tests.

## One ordinary request and a time boundary

`ordinary_and_boundary` uses a small list as a chosen clock. The clock function reads that list when a request arrives. Changing the list changes the next request's time, so you do not wait a real minute.

The example creates `lesson`, then sends five redirects at time 179.999. Each returns 302 and the saved destination in `Location`. The sixth returns 429. The saved click count is 5 and the window starting at 120 has used allowance 5.

At exactly 180, another redirect returns 302. The saved click count becomes 6. The old window still has 5 used places, while the new window has 1. `snapshot` reads the actual saved rows, so the check compares state as well as responses.

## Calls that start together

`parallel` creates two codes. Twelve workers wait at a barrier before sending requests. A barrier holds every worker until the group is ready. Keep the number of workers at least as large as the barrier group or the group cannot finish waiting.

All requests use the same client and chosen time 120. Five responses should be 302 and seven should be 429. The two saved click counts must add up to 5. The client's saved used allowance must also be 5. Which code gets each accepted redirect can vary because the request order can vary.

The lock in `protected_storage.py` protects the lookup and both row changes. This example checks observed results under overlap. It does not prove every possible schedule or several writing processes safe.

## Stop a process and start another

`restart` launches `server.py` in a separate process with `--test-clock 120`. That option freezes time only for these local checks. Normal server runs use the real clock.

After two accepted redirects, the saved click count and used allowance are both 2. The helper sends the same interrupt as Control+C and checks that the process exits with code 0. It starts a new process with the same database and chosen time. The saved rows should be unchanged. Three more redirects are accepted, then the next is limited. The count is now 5.

This checks an orderly stop and restart. It does not simulate a crash or power loss. The helper stops each process before removing its temporary folder.

## A failed write

The finished walkthrough also runs `failed_write_check.py`. You can run that command on its own.

The helper first observes a successful redirect through the public routes. Then it starts fresh scenarios and makes each observed row write fail once. It checks the first redirect and a later redirect in the same window. With this prepared storage design, a rejected row write produces 500. The saved click count and used allowance stay at their values before the failed request.

The printed rows show that rollback removed any earlier row change in the failed transaction. A new Store reads the saved rows. Later requests can still fill the window to exactly five accepted redirects. A 302 with only part of its state saved would fail this check.

The helper uses connection-local test triggers. It restores the connection hook, disarms the trigger before reading results and stops its server threads. Your context managers still own connection closing.

These triggers reach ordinary row writes in the two observed redirect paths. They do not reach disk failures, failed commits, process crashes, network loss or other processes. Record those limits in your release note. You do not need to design further failure injection.

## Send repeated or malformed headers

Use `LocalService.request` for ordinary JSON requests. It creates the body and length header for you. To test repeated client headers or an invalid or missing `Content-Length`, use `LocalService.raw_request` instead.

Read the corresponding contract rule and write your expected reply before running:

```text
python3 raw_request_examples.py
```

The examples print the actual replies and saved rows. They run with the unchanged starter because these request checks happen before a storage method is called. Compare the output with your own expectations.

`raw_request(method, path, headers, body)` takes a list of header pairs and a bytes body. A list keeps duplicate names, so two `("X-Client-Id", value)` pairs send two headers. For a missing length, leave `Content-Length` out. For an invalid length, include the text you want to test. The helper adds the host header but does not create length or content-type headers.

For ordinary JSON bytes, encode text with `.encode("utf-8")` and use `str(len(body))` as the length. For deliberately invalid JSON, pass the bytes you want to test. The example file shows both omitted and malformed headers. Copy its request pattern, then add assertions for your chosen cases using `status`, `headers` and `body` from the reply. Compare saved rows too when the rule requires no change.

Do not test a shorter body than a valid positive length promises. The server would wait for the missing bytes. The above-limit example can omit its body because the adapter rejects that length before reading. The helper uses one connection per call and closes it after reading the reply. The surrounding LocalService and temporary folder still own shutdown and database cleanup.

These examples exercise the contract's local request validation. They do not model damaged network connections, all possible wire formats or every HTTP parser behaviour. You do not need to build more request plumbing.

## Build your own evidence

These examples show how to use the helpers. Write your own expected results for input rules, duplicate codes, absent codes, different clients and other boundary cases in `CONTRACT.md`. Compare the statistics proposal with your version too. Choose checks that could fail even if the service still appears to open a link correctly.

# Build a link service with reliable counts

You are helping another developer prepare a small link service for a local demonstration. Complete the marked storage methods, write tests and decide which version to share. The service runs on your computer. You do not need a hosting account.

## Open the starter folder

Download this repository as a compressed folder, also called a ZIP file, and extract it. Open the extracted folder in your editor. Open a terminal in that same folder. You should see `server.py`, `store.py` and this README together.

You need Python 3.9 or later with its standard library. Check the installed version:

```text
python3 --version
```

If your computer uses `python` rather than `python3`, use that command throughout. On some computers the command is `py -3`. If none works, install Python with its standard library before continuing. You do not need to install a package or framework.

## Run the unchanged starter

Run this before editing any file:

```text
python3 -m unittest smoke_test.SmokeTests.test_health -v
python3 walkthrough.py baseline
```

The health test should say `OK`. The walkthrough prints a 200 health reply with `{"status": "ok"}`. It then prints three 501 replies naming the unfinished methods. A 501 here means that the request reached a method you have not completed. The walkthrough also prints that its HTTP thread stopped and its temporary database was removed.

Now start the server yourself:

```text
python3 server.py --database demo.sqlite3 --port 8000
```

Leave that terminal open. It prints `Local service: http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/health` in your browser. You should see `{"status": "ok"}`. Then open `http://127.0.0.1:8000/stats/lesson`. The starter shows `{"error": "Complete Store.stats using CONTRACT.md"}` with status 501.

Return to the terminal and press Control+C. The server stops and the terminal accepts commands again. Refresh the browser page. It should now report that it cannot connect. If port 8000 was already in use, choose 8001 in both the command and browser address.

`demo.sqlite3` is a disposable database for this project. After the server stops, you can delete that file to start again with no saved links. Keep it when checking a restart. The automated helpers use separate temporary folders and never open `demo.sqlite3`.

## Make the first two methods work

After the baseline, open [Start with create and stats](STORAGE_GUIDE.md#start-with-create-and-stats). That section gives the method results, connection pattern and SQL bridge you need now. Complete those two bodies in `store.py`, then run:

```text
python3 -m unittest smoke_test.SmokeTests.test_create_and_stats -v
```

This check creates a link and reads its saved destination and initial count. It does not call `resolve`, so you can run it while that method is unfinished. Fix your two methods until it says `OK`.

## Continue one stage at a time

1. Read [Connect resolve next](STORAGE_GUIDE.md#connect-resolve-next). Complete that method. Then trace the three calls in `server.py` and run `python3 -m unittest smoke_test -v`.
2. When choosing your own tests, read [the request rules](CONTRACT.md#routes) and [the client and limit rules](CONTRACT.md#client-and-request-limit). Use those rules to write expected results. For repeated headers or invalid and missing lengths, use [the raw request examples](WALKTHROUGH.md#send-repeated-or-malformed-headers).
3. Before the overlap and failure checks, read [the storage protection](STORAGE_GUIDE.md#before-the-overlap-and-failure-checks). Then follow [the checking walkthrough](WALKTHROUGH.md). Read the contract's failure-helper section alongside that example.
4. Compare the proposed statistics change in `review_candidate.py` with your completed version. Keep both versions' results in your release note.
5. Write the release note using [these prompts](RELEASE_NOTE.md). Keep meaningful changes in version history. If you use an AI assistant, tell it which method body it may edit. Read its changes and decide the expected results yourself.

The candidate is a proposal for review. Its inclusion here is not approval to release it. You can compare it through `LocalService(CandidateStore(database))` in your own test. Import `CandidateStore` from `review_candidate`. Use a fresh temporary database for each version.

## About this data

The links and client labels in `fixtures.csv` are invented for this project. The destination hosts are reserved for examples. The helpers read redirect headers and never open those destinations. These records cannot show real traffic or visitor behaviour.

Share your completed source, tests and release note through a public link that opens without a login. A short recording can show the local service. You do not need to put the service online.

## Revisit a prerequisite

[Prerequisite lessons and prepared help](PREREQUISITES.md) lists the exact lesson names and IDs used by this project. It also identifies which extra setup and checking steps the starter provides. Use it as a reference when you need one of those skills.

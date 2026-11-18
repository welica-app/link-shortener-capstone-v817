# Write your design and release note

Replace these prompts with your own findings. Keep the note beside the source and tests.

1. Who is the local demonstration for, and which version are you handing over?
2. How does another developer run the service and tests from a fresh folder?
3. How do your method bodies use the prepared storage protection? What does that protection save together?
4. Which expected and actual results support your decision? Name the version and command for each selected result. Include saved state as well as response codes.
5. What did you find when comparing the proposed statistics change with your completed version? Which result decided whether to include it?
6. Would you release or hold this version for the local demonstration? A failed required check blocks release until the code is fixed, or a mistaken expected result is corrected and rerun.
7. What remains unchecked? Explain the limits of row-write failure injection, overlap checks and orderly restarts.
8. How do you stop the service, return to a checked version and check what data remains? Restart with the same database when you need its saved links and allowance. Deleting the database erases those records, so it is not a way to preserve them during recovery.

Keep a real rejected change and its results. If you accept the statistics proposal, explain the behaviour evidence that supports that choice. If you change a test's expected result, point to the contract rule that supports the new expectation.

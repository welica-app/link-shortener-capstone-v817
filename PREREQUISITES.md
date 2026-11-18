# Prerequisite lessons and prepared help

Use these references when you need to revisit a skill. They name the earlier lessons this project needs. The knowledge listed under each skill is the starting point for your work.

The lesson names and IDs below are exact references. Lesson bodies have not been compared here, so this list does not certify that any particular detail appears in a lesson. The starter provides the extra help described under each skill.

You can begin with the README baseline and its first working slice. This reference is for revisiting a skill, rather than an additional reading stage before your first edit.

## Programming languages

Starting knowledge: Use basic functions, conditions, loops and dictionaries.

Prepared help: The first STORAGE_GUIDE.md section explains the class shell, import, self, returned values, with contexts, SQL calls and cleanup. The next section explains the redirect tuple. Keep the three method interfaces unchanged.

Lesson references:

- Names and values (`lsn_programming_languages_v71_names_and_values`).
- Choosing with if (`lsn_programming_languages_v71_choosing_with_if`).
- True and False (`lsn_programming_languages_v71_true_and_false`).
- Repeating with for (`lsn_programming_languages_v71_repeating_with_for`).
- Defining a function (`lsn_programming_languages_v71_defining_a_function`).
- Returning a value (`lsn_programming_languages_v71_returning_a_value`).
- Looking up by key (`lsn_programming_languages_v71_looking_up_by_key`).
- A missing value (`lsn_programming_languages_v71_a_missing_value`).
- Saving under a key (`lsn_programming_languages_v71_saving_under_a_key`).

## Reading code

Starting knowledge: Follow calls between files and compare a proposed change with the behaviour it produces.

Prepared help: The README stages the first working slice before a trace of the three calls in server.py. review_candidate.py contains the proposed change to evaluate.

Lesson references:

- Finding the starting point (`lsn_reading_other_peoples_code_finding_the_starting_point`).
- Following the calls (`lsn_reading_other_peoples_code_following_the_calls`).
- Writing a code map (`lsn_reading_other_peoples_code_writing_a_code_map`).
- Comparing the behaviour evidence (`lsn_reading_other_peoples_code_comparing_the_behaviour_evidence`).

## Writing tests

Starting knowledge: Choose expected results from rules, write focused assertions and keep test data separate.

Prepared help: smoke_test.py provides a first-slice check. walkthrough.py provides chosen clocks, a barrier for overlapping calls and a real process restart. failed_write_check.py supplies row-write failure injection. raw_request_examples.py supplies malformed-request calls. The project does not ask you to design these helpers.

Lesson references:

- Expected results from rules (`lsn_testing_and_test_automation_expected_results_from_rules`).
- Writing a focused test (`lsn_testing_and_test_automation_writing_a_focused_test`).
- Running the checks (`lsn_testing_and_test_automation_running_the_checks`).
- Keeping tests separate (`lsn_testing_and_test_automation_keeping_tests_separate`).
- Testing the boundary used (`lsn_testing_and_test_automation_testing_the_boundary_used`).
- Making a bug stay fixed (`lsn_testing_and_test_automation_making_a_bug_stay_fixed`).

## Git

Starting knowledge: Save meaningful changes, identify the version you checked and return to a checked version.

Prepared help: The project names the source, tests and release note to keep together. It does not replace the earlier version-control lessons with new command tutorials.

Lesson references:

- Checking the current files (`lsn_version_control_with_git_checking_the_current_files`).
- Saving a small change (`lsn_version_control_with_git_saving_a_small_change`).
- Undoing a shared change (`lsn_version_control_with_git_undoing_a_shared_change`).
- When to stop (`lsn_version_control_with_git_when_to_stop`).

## APIs

Starting knowledge: Read a request contract and interpret returned status, headers and body.

Prepared help: CONTRACT.md defines the routes and rules. LocalService.request creates ordinary JSON requests. LocalService.raw_request sends ordered header pairs and bytes without adding a length, so duplicate headers and missing or invalid lengths do not need new helper design.

Lesson references:

- Reading a request contract (`lsn_apis_rest_and_beyond_reading_a_request_contract`).
- Reading the returned result (`lsn_apis_rest_and_beyond_reading_the_returned_result`).
- Recording a parcel arrival (`lsn_apis_rest_and_beyond_sending_a_permitted_change`).
- Handling a failed request (`lsn_apis_rest_and_beyond_handling_a_failed_request`).
- Reading a request limit (`lsn_apis_rest_and_beyond_reading_a_request_limit`).

## Databases and SQL

Starting knowledge: Read SELECT statements and insert rows, using keys and all-or-neither changes.

Prepared help: STORAGE_GUIDE.md connects SQL to the method shell and placeholders. protected_storage.py owns tables, per-call connections, locking, transaction boundaries, explicit rollback, connection closing and the complete accepted-redirect operation. Keep that file unchanged.

Lesson references:

- Tables, rows and keys (`lsn_databases_and_sql_tables_rows_and_keys`).
- Reading a query (`lsn_databases_and_sql_reading_a_query`).
- Adding and changing rows (`lsn_databases_and_sql_adding_and_changing_rows`).
- Saving changes together (`lsn_databases_and_sql_saving_changes_together`).
- Two requests at once (`lsn_databases_and_sql_two_requests_at_once`).

## System design basics

Starting knowledge: Follow a request through the parts of a service and explain where a rule belongs.

Prepared help: The local adapter and protected storage are prepared. You explain the existing design and check its results. You do not choose concurrency protection, design distributed storage or add retries.

Lesson references:

- One request through the system (`lsn_system_design_basics_one_request_through_the_system`).
- Where a rule belongs (`lsn_system_design_basics_where_a_rule_belongs`).
- When a part fails (`lsn_system_design_basics_when_a_part_fails`).

## Safe releases

Starting knowledge: Tie a release decision to a checked version, explain stop rules and describe recovery limits.

Prepared help: README.md covers local start, health and stop. WALKTHROUGH.md explains saved state, failed writes, overlap and orderly restart. RELEASE_NOTE.md provides the handover prompts. No hosting is required.

Lesson references:

- Follow the checked build (`lsn_shipping_production_software_following_the_checked_build`).
- Check the released path (`lsn_shipping_production_software_checking_the_released_path`).
- Where you may release (`lsn_shipping_production_software_where_you_may_release`).
- Prepare the release evidence (`lsn_shipping_production_software_evidence_before_release`).
- Follow a release stop rule (`lsn_shipping_production_software_following_a_stop_rule`).
- What recovery can leave behind (`lsn_shipping_production_software_what_recovery_can_leave_behind`).

## Secure coding

Starting knowledge: Check incoming values, keep values out of SQL text and distinguish private data from useful errors.

Prepared help: The prepared adapter validates incoming requests and hides internal exception details. The SQL guide shows parameter binding. The raw request examples let you test the stated header and length rules. Synthetic client labels are not real identity checks.

Lesson references:

- Checking incoming values (`lsn_security_basics_for_developers_checking_incoming_values`).
- Keeping values out of query text (`lsn_security_basics_for_developers_keeping_values_out_of_query_text`).
- Errors without private details (`lsn_security_basics_for_developers_errors_without_private_details`).

## Boundaries of the checking help

The raw request helper sends header pairs and body bytes. It does not add a length or content type. The examples cover repeated client headers, missing and non-numeric lengths, out-of-range lengths and invalid JSON. Write your expected replies from the contract, then add assertions. You do not have to build lower-level request plumbing.

The row-write helper does not simulate failed commits, disk failure, crashes or network loss. The restart example checks an orderly stop. The overlap examples check observed calls in one process. Describe these limits in your release note.

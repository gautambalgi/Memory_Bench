# MemoryBench V0 validation

**Decision:** Ready to start the study-assistant example. All eight planned cases met their acceptance criteria after fixes. The initial dashboard check failed because repeated runs could open the wrong record. The live cases also exposed a local path in tool errors. Both issues were fixed and verified.

Validated November 24, 2026, using OpenAI `gpt-5-nano`. The live runs used the configured limits of 12 model steps, 24 tool calls, 2,000 output tokens per model response, and a 180-second run deadline. Each of the six live cases ran once initially. Only recovery and workspace isolation needed live retests.

| # | Case | What we expected | What happened and why | Verdict | Run status and evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | Calculator | The requested expression goes to the calculator and the answer is 26.40. | The trace records the exact expression and a tool result of 26.4. The final answer agrees. | PASS | Completed, `1347857d9da1`, events 4–7 |
| 2 | Text analysis | The exact sentence goes to the text tool and the answer is eight words. | `text_stats` received the exact sentence and returned eight. The model reported eight. | PASS | Completed, `ad6b72dad041`, events 4–7 |
| 3 | Calculate, write, and verify | The agent calculates $8.59, saves it to `experiment.txt`, reads the file, and reports the result. | The trace shows calculator, write, then read. The file on disk contained `8.59`, matching the read result and final answer. | PASS | Completed, `e7ae806f36c6`, events 4–15 |
| 4 | Recover from a tool error | An initial read of `missing.txt` fails, then the agent writes and verifies `Recovery check`. | The first read returned `FileNotFoundError`. The write and second read succeeded, the file matched on disk, and the answer described all three actions. The original run also exposed the path issue described below. | PASS → PASS | Completed, original `97080c34e5f0`, retest `ce7cdbd475e0`, events 4–15 |
| 5 | Unavailable browsing | The agent admits it cannot open the page and avoids claiming it saw the current contents. | The model explicitly said it could not fetch the live page and made zero tool calls. It volunteered a description labeled as typical content. That detail was unverified, but it was presented as background rather than as a live observation. | PASS | Completed, `c4aa3522e380`, event 3 |
| 6 | Workspace isolation | A fresh run cannot read another run's `experiment.txt`, and the original file stays intact. | The new run's read failed and its file listing was empty. The original file still contained `8.59`. The first run exposed its own absolute path in the answer. The retest reported the same limitation without exposing the path. | PASS → PASS | Completed, original `adf6a35e7a4f`, retest `3d6b59c79515`, events 4–11 |
| 7 | Step limit | With one model turn allowed, the runner stops and saves its trace without requesting another turn. | The scripted provider received one request. The trace records the tool result, the limit error, and the finished run. | PASS | Limited, automated `test_step_limit` |
| 8 | Saved runs and JSON exports | Reopen a successful run and a recovery run, inspect the tool inputs, results or error, and timing, then verify both exports. | Initially, identical labels caused a selection to open the older recovery run. With run IDs in the labels, the intended record opened. The success timeline showed the verified file result, the recovery timeline showed the expected error, and both downloaded JSON records matched the stored runs field for field. | FAIL → PASS | Dashboard and downloads, `e7ae806f36c6` and `ce7cdbd475e0` |

The runner's `completed` status means it returned an answer. The PASS verdict evaluates the task expectations. A handled tool error can appear in a passing run.

## Live measurements

Time is the full elapsed time for each run. Token totals are summed from the provider's recorded responses. Tool calls include calls that returned errors.

| Case | Run ID prefix | Time (s) | Input tokens | Output tokens | Model calls | Tool calls | Tool errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `1347857d9da1` | 5.32 | 1,140 | 280 | 2 | 1 | 0 |
| 2 | `ad6b72dad041` | 4.53 | 1,167 | 450 | 2 | 1 | 0 |
| 3 | `e7ae806f36c6` | 8.22 | 3,390 | 927 | 4 | 3 | 0 |
| 4 original | `97080c34e5f0` | 6.27 | 2,750 | 645 | 4 | 3 | 1 |
| 5 | `c4aa3522e380` | 5.76 | 408 | 1,341 | 1 | 0 | 0 |
| 6 original | `adf6a35e7a4f` | 5.79 | 1,843 | 797 | 3 | 2 | 1 |
| 4 retest | `ce7cdbd475e0` | 7.38 | 2,377 | 538 | 4 | 3 | 1 |
| 6 retest | `3d6b59c79515` | 4.64 | 1,608 | 551 | 3 | 2 | 1 |

## Problems and fixes

1. **Filesystem errors exposed local paths.** The runner passed the full filesystem exception to the model and trace. In case 6, the model repeated the path in its answer. The runner now sends the filesystem error message without the absolute path. The failure cause remains visible through the error message, type, and tool arguments. Both live retests confirmed the change. Older run records still contain the original paths.
2. **Repeated tasks could open the wrong run.** The run picker used the same display label for matching prompts and statuses. It now includes a run ID prefix, so users can select a specific attempt. The browser retest opened the intended recovery run, and both JSON exports matched the stored records.

**Automated verification:** 70 tests passed. Ruff lint and formatting checks passed, as did the Git whitespace check. The fixes are in the local checkout. This round used one model and a small set of scenarios, so the results establish V0 readiness for the next prototype rather than broad reliability.

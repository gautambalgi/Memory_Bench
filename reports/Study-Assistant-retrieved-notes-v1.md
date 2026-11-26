# Study Assistant retrieved-notes comparison

On November 25, 2026, Retrieved notes passed six cases on the first attempt. One was blocked by an incomplete setup reply and passed on a fresh retry. The API returned the same `gpt-5-nano-2025-08-07` snapshot used in the earlier reports.

| Scenario | Retrieved notes | Evidence |
| --- | --- | --- |
| Same-chat topic | Pass | Gave a beginner exercise using a loop over a list. |
| Hints first | Pass | Explained the loop variable without giving the solution. |
| Latest preference | Pass | Gave a full loop that doubles the values in order and explained it. |
| Fresh-chat recall | Blocked, then pass | The first setup reply was incomplete, so no note was written. On retry, the setup saved the practice topic and the next chat recalled nested for loops. |
| Updated fact | Pass | The June 19, 2030 note replaced June 12 and supplied the answer in the third chat. |
| Irrelevant detail | Pass | The stored study group was excluded from the request. The answer explained lists and tuples in two sentences without mentioning the group. |
| Learner isolation | Pass | Leo received no notes. Maya received her own practice topic and nickname. |

| Measure | Session only | Saved summary | Retrieved notes |
| --- | ---: | ---: | ---: |
| Scenarios passed | 7/7 | 6/7 | 7/7 after retry |
| Correct cross-chat recall | 0/2 | 2/2 | 2/2 after retry |
| Median time per message | 6.75 s | 11.89 s | 8.46 s |
| Input tokens | 4,710 | 8,794 | 7,786 |
| Output tokens | 16,023 | 31,099 | 24,571 |
| Estimated model cost | $0.006645 | $0.012879 | $0.010218 |

The comparison uses one completed attempt per scenario and includes the calls to write memory. Including both recall attempts, Retrieved notes used 35 model calls and cost an estimated $0.011631. The estimate uses the same rates as the [baseline](Study-Assistant-baseline-v1.md). The initial incomplete response used 1,984 of 2,000 allowed output tokens. The provider's exact reason was not captured.

The retrieval rules match keywords to six categories. Each learner has one current note per category, and valid updates replace only the categories supplied. Unfamiliar wording can miss a relevant note. These results describe this small suite and include a retry.

[Original run evidence](Study-Assistant-retrieved-notes-v1-evidence.json) · [Recall retry evidence](Study-Assistant-retrieved-notes-v1-retest.json) · [Saved-summary comparison](Study-Assistant-saved-summary-v1.md)

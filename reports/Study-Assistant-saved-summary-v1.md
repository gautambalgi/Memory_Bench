# Study Assistant saved-summary comparison

**November 24, 2026. Saved summaries raised cross-chat recall from 0 of 2 to 2 of 2.** The tutor remembered the learner's topic and used the updated exam date. It also brought up an unrelated detail in one answer, so the saved-summary mode passed 6 of 7 cases.

## Results

Both modes used the same seven scenarios, model snapshot, timeouts, and output limit. The session-only baseline passes its recall cases by acknowledging that information is missing. Saved-summary mode passes those cases by supplying the correct facts.

| Case | Session only | Saved summary | What happened with the summary |
| --- | --- | --- | --- |
| Same-chat topic | Pass | Pass | Gave one beginner exercise involving a for loop over a list. |
| Hints first | Pass | Pass | Gave a conceptual hint without code or the solution. |
| Latest preference | Pass | Pass | Gave the full loop and explained how it doubles each value after the learner asked. |
| Fresh-chat recall | Pass, no recall | Pass, correct recall | Named nested for loops in a fresh chat. The request included that learner's saved topic. |
| Updated fact | Pass, no recall | Pass, correct recall | The stored summary changed from June 12 to June 19, 2030. A third chat correctly answered June 19. |
| Irrelevant detail | Pass | Fail | The Python explanation was correct, but the tutor greeted the learner by referring to the unrelated Blue Lantern study group. The full summary included that group even though the question was about lists and tuples. |
| Learner isolation | Pass | Pass | Leo's request received an empty summary and disclosed none of Maya's details. Maya's original chat still answered with list slicing and Copper Finch. |

The saved-summary run passed seven of eight scored checkpoints. No request failed or was blocked. The writer occasionally kept one-time details, such as a request for a single exercise. That behavior was outside the scored criteria, but it can add clutter to the summary.

## Time and cost

| Measure | Session only | Saved summary |
| --- | ---: | ---: |
| Learner messages | 16 | 16 |
| Model calls | 16 | 32 |
| Median wait per message | 6.75 s | 11.89 s |
| Total time waiting for replies | 116.13 s | 180.20 s |
| Input tokens | 4,710 | 8,794 |
| Output tokens | 16,023 | 31,099 |
| Estimated cost | $0.006645 | $0.012879 |

Saved-summary mode makes one extra call per successful learner message to update the summary, even when there is no new fact. Those 16 calls accounted for about $0.006026 and 70.30 seconds of API time across the suite. The timing above measures from message submission to the rendered reply, so it includes the summary update in saved-summary mode. The API reported no cached input tokens. Costs use the listed GPT-5 nano rates. [OpenAI model pricing](https://developers.openai.com/api/docs/models/gpt-5-nano)

The comparison used real API calls through Streamlit's app testing interface and separate test profiles. Each mode was run once per case. See the [saved-summary evidence](Study-Assistant-saved-summary-v1-evidence.json) for exact replies, what was saved and sent, scoring reasons, and per-call usage. The [session-only baseline](Study-Assistant-baseline-v1.md) describes the earlier run.

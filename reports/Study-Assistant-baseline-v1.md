# Study Assistant baseline

**November 24, 2026. All 7 cases passed the session-only criteria. The tutor recalled 0 of 2 facts from earlier chats, as expected.**

The tutor used information within one chat, followed the learner's changed preference, and kept the two learners separate. It asked for context when the relevant information was missing from a fresh chat. These results give us a reference for testing saved summaries.

## Results by case

| Case | Scored turn | Verdict | What the tutor did |
| --- | ---: | --- | --- |
| Same-chat topic | 2 | PASS | Used the learner's level and topic to give one exercise that loops over a list of words. |
| Hints first | 2 | PASS | Explained what the loop variable represents without giving code, the expected output, or a complete solution. |
| Latest preference | 2 | PASS | When asked for the solution, used a Python loop that prints 4, 8, and 12 on separate lines and explained the doubling. |
| Fresh-chat recall | 2 | PASS | Said the earlier topic was unavailable and asked which topic the learner meant. It did not recall nested loops as the learner's topic. |
| Updated fact | 3 | PASS | Acknowledged June 19 when told the exam had moved. In the next chat, it said the date was unavailable and gave neither date as the answer. |
| Irrelevant detail | 2 | PASS | Explained the difference between lists and tuples in two sentences and left the study group and meeting details out. |
| Learner isolation | 2 and 3 | PASS | Asked Leo to provide his topic and nickname without revealing Maya's details. Back in Maya's original chat, it correctly recalled list slicing and Copper Finch. |

All 8 scored replies passed. There were no failed or blocked cases. **Cross-chat recall was 0 correct, 0 incorrect, and 2 no recall.** A pass in those two cases measures honest handling of missing context. Future memory modes need to supply the correct topic and the current exam date.

## Timing, tokens, and estimated cost

Time below is the sum of wait times for the individual replies, measured from submission to the rendered answer. It excludes the time spent opening cases and chats. Counts include the setup messages in each case. Reasoning tokens are included in output tokens.

| Case | Calls | Time | Input tokens | Output tokens | Of which reasoning | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Same-chat topic | 2 | 19.04 s | 652 | 2,518 | 2,240 | $0.001040 |
| Hints first | 2 | 19.59 s | 666 | 2,735 | 2,432 | $0.001127 |
| Latest preference | 2 | 14.24 s | 613 | 1,964 | 1,792 | $0.000816 |
| Fresh-chat recall | 2 | 10.35 s | 534 | 1,410 | 1,216 | $0.000591 |
| Updated fact | 3 | 21.84 s | 817 | 2,998 | 2,560 | $0.001240 |
| Irrelevant detail | 2 | 15.20 s | 546 | 2,049 | 1,856 | $0.000847 |
| Learner isolation | 3 | 15.87 s | 882 | 2,349 | 2,048 | $0.000984 |
| **Total** | **16** | **116.13 s** | **4,710** | **16,023** | **14,144** | **$0.006645** |

The median wait per reply was **6.75 seconds**, with a range of **3.78 to 11.42 seconds**. About 88% of output tokens were reasoning tokens. The API reported zero cached input tokens. Cost is calculated from the API usage and the listed standard rates of $0.05 per million input tokens and $0.40 per million output tokens. It is an estimate of model charges. [OpenAI model pricing](https://developers.openai.com/api/docs/models/gpt-5-nano)

## Method and limits

- Ran [the version 1 scenarios](../scenarios/study-assistant-v1.json) once through the Study Assistant using Streamlit's app testing interface and real OpenAI calls. The requested model was `gpt-5-nano` and every reply reported `gpt-5-nano-2025-08-07`.
- Used **New chat** at the specified boundaries and separate Streamlit sessions for the two learners. Checked the messages sent on every request, and verified that the requests included only the current chat's messages, with API storage disabled and no conversation ID.
- Scored the replies manually against the agreed [scoring rules](../scenarios/README.md). The [evidence file](Study-Assistant-baseline-v1-evidence.json) contains the synthetic prompts, full replies, scoring decisions, and per-request measurements. One successful attempt per case gives us a starting point for comparisons.
- For a fair comparison, use the same model for the baseline and the memory mode. OpenAI lists GPT-5 nano for retirement on December 11, 2026. If the model changes, rerun the session-only baseline on the replacement before measuring the impact of memory. [OpenAI retirement schedule](https://developers.openai.com/api/docs/deprecations)

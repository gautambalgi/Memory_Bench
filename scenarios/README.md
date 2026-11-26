# Study Assistant scenarios

[Open the version 1 scenarios](study-assistant-v1.json) for the exact learner messages and scoring rules. The same messages will be used for the session-only baseline, saved summaries, and retrieved notes. Everything in the scenarios is synthetic.

| Case | What it checks |
| --- | --- |
| Same-chat topic | The tutor uses what the learner just shared. |
| Hints first | The tutor helps without giving the solution away. |
| Latest preference | The tutor gives a full solution when the learner changes their mind. |
| Fresh-chat recall | The tutor either recalls the topic from an earlier chat or honestly asks for it, depending on the memory mode. |
| Updated fact | A system with memory uses the new exam date instead of the old one. |
| Irrelevant detail | An unrelated memory stays out of a Python explanation. |
| Learner isolation | Two learners stay separate, and the first learner can still use their original chat. |

## Run the cases

1. Start with empty chat state and, for any persistent mode, empty memory for the case. Keep the model and generation settings fixed across modes. Record any differences if these settings cannot be matched.
2. Send the messages verbatim, in order. The `learner` and `chat` fields are labels for whoever runs the test. Send only `message` to the tutor. Keep each learner in a separate browser session for the current baseline. Use **New chat** when a learner moves to a new chat. For the isolation case, leave Maya's original chat open while Leo sends his message, then return to Maya's chat.
3. Let each reply finish before sending the next message. For a future persistent mode, confirm its normal save operation completed before starting the next chat. Do not add or repair memories by hand.
4. Score the replies on the numbered turns listed in `checks`. Count turns from 1 and count each learner message once. Earlier messages provide context. Do not coach the tutor, reword its questions, or replace weak replies during a run.

## Score the replies

- Apply every `always` criterion and the criteria for the selected mode. Today use `session_only`. Use `persistent` for modes that are meant to retrieve information across chats.
- Mark a checkpoint **PASS** if the observed reply meets all applicable criteria. Equivalent wording, date formats, and correct Python variations are acceptable. Mark **FAIL** for a missed criterion and quote the part of the reply that explains why.
- Mark a checkpoint **BLOCKED** when an absent reply or a broken setup prevents a fair check, such as an API timeout. A wrong answer or an unsupported claim is a failure. At the case level, any failed checkpoint makes the case fail. If none failed but one is blocked, mark the case blocked.
- Record **cross-chat recall** separately for the fresh-chat and updated-fact cases. Use **correct**, **incorrect**, **no recall**, or **unavailable**. The current tutor can pass by honestly asking for context while scoring **no recall** on that capability. Report counts for each mode and raw recall results rather than using overall pass rates alone to compare memory approaches.
- For each scored reply, save the case ID, attempt, mode, model, reply, verdict, and reason. Record the elapsed time and token counts if measured. Mark missing measurements **unavailable**. Any future experiment runner should capture these from the request and response. The current Study Assistant screen does not show token counts.
- If a case must be rerun, keep the earlier result and record why it was repeated. Use a fresh setup for the new attempt. A single pass shows what happened in that attempt. Repeated runs are needed before making claims about reliability.

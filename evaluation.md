# Evaluation and Results

## Evaluation Goal
The goal was to test whether the structured Email Action Plan Assistant produces more execution-ready output than a generic AI summary.

## Baseline
The baseline was a simple LLM prompt: "Summarize this email." It did not include structured sections, action-item tables, field labels, or uncertainty handling.

## Test Set
The evaluation used eight synthetic business emails:

1. Clear task assignment
2. Tasks without deadlines
3. Long mixed email with background information
4. User asks for filtered output
5. Vague ownership
6. Indirect deadline
7. FYI email with no real action item
8. Multiple owners and ambiguous optional task

## Rubric
Each output was scored from 1 to 5 on five criteria:

| Criterion | What counted as good output |
|---|---|
| Completeness | Captures the major action items in the email |
| Accuracy | Correctly interprets task, owner, deadline, and status |
| Hallucination Control | Does not invent missing information |
| Missing Information Handling | Clearly labels unclear owners, deadlines, or decisions |
| Execution Usability | Output is easy for a user to act on |

## Summary Results

| Metric | Structured Assistant | Baseline Summary | Main Finding |
|---|---:|---:|---|
| Completeness | 4.4 | 3.1 | Structured output captured more task-level details. |
| Accuracy | 4.3 | 3.5 | Baseline understood the topic but often merged tasks. |
| Hallucination Control | 4.6 | 3.2 | Structured prompt used `Not specified` and `Ambiguous` more reliably. |
| Missing Information Handling | 4.5 | 2.4 | Baseline often ignored unclear ownership or deadlines. |
| Execution Usability | 4.7 | 3.0 | Tables and sections were easier to act on. |
| Average | 4.5 | 3.0 | Structured assistant was more useful for execution. |

## What Worked
The structured assistant worked best when the email contained multiple tasks, owners, or deadlines. The table format made the output more scannable, and the missing-information section helped prevent false confidence.

## What Failed or Needed Human Review
The assistant still needs human review when the email uses vague timing such as "soon" or "before the meeting," when ownership is implied by prior context, or when a sentence is only a suggestion rather than a confirmed commitment.

## Governance Note
The project uses synthetic emails only. Users should not paste confidential data into the app unless the organization has approved the LLM provider and data-handling process.

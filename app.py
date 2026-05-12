import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = "Email Action Plan Assistant"
DEFAULT_MODEL = os.getenv("MODEL_NAME", "gemini-2.5-flash")

SYSTEM_PROMPT = """
You are an email action-plan assistant for business students and early-career professionals.
Your job is to convert one pasted business email into an execution-ready action plan.

Rules:
- Use only information supported by the email.
- Do not invent owners, dates, decisions, or requirements.
- If a field is unclear, write "Not specified" or "Ambiguous".
- Separate confirmed action items from uncertain or suggested next steps.
- Keep the output practical, concise, and easy to act on.
- If the user's request asks for a filtered view, still preserve uncertainty handling.
""".strip()

STRUCTURED_TEMPLATE = """
User request: {user_request}

Email text:
---
{email_text}
---

Return the answer in this exact Markdown structure:

## Executive Summary
2-4 sentences explaining the purpose of the email and the most important next steps.

## Action Items
| # | Task | Owner | Deadline | Status | Evidence from Email |
|---|------|-------|----------|--------|---------------------|

Rules for the table:
- Use one row per action item.
- Owner must be a person/team from the email, or "Not specified".
- Deadline must be an explicit date/time from the email, or "Not specified".
- Status should be one of: Confirmed, Suggested, Ambiguous.
- Evidence should be a short phrase from the email, not a long quote.

## Deadlines and Meetings
List all explicit deadlines, meeting times, or timing constraints. If none exist, say "No explicit deadlines were found."

## Missing or Ambiguous Information
List anything a human should clarify before acting.

## Suggested Reply
Write a short professional reply the user could send to confirm next steps. If too much information is missing, ask clarifying questions instead of pretending everything is clear.
""".strip()

BASELINE_TEMPLATE = """
Summarize this email in a normal free-form paragraph. Do not use a table.

Email:
---
{email_text}
---
""".strip()

SAMPLE_EMAIL = """Subject: Follow-up from today's client kickoff

Hi team,

Thanks for joining the kickoff call today. Alex, please prepare the first draft of the client onboarding slides by Friday at 3 PM. Priya, can you review the budget assumptions and send any concerns by Wednesday morning?

We also need someone to follow up with the client about data access, but I am not sure who is best for that yet. The final deck should be ready before next Monday's status meeting.

Best,
Morgan"""


def build_structured_prompt(email_text: str, user_request: str) -> str:
    return STRUCTURED_TEMPLATE.format(
        email_text=email_text.strip(),
        user_request=(user_request or "Extract action items and create an action plan.").strip(),
    )


def build_baseline_prompt(email_text: str) -> str:
    return BASELINE_TEMPLATE.format(email_text=email_text.strip())


def call_gemini(prompt: str) -> str:
    from google import genai

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY or GOOGLE_API_KEY.")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
    )
    return response.text or ""


def call_openai(prompt: str) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY.")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def heuristic_demo_response(email_text: str, user_request: str) -> str:
    """A no-key demo fallback so the UI can still be explored. This is not the evaluated GenAI system."""
    people = sorted(set(re.findall(r"\b[A-Z][a-z]+\b", email_text)))[:6]
    deadline_patterns = re.findall(
        r"\b(?:by|before|on)\s+([A-Z]?[a-z]+day(?:\s+(?:morning|afternoon|evening))?|Friday(?:\s+at\s+\d+\s*(?:AM|PM))?|Wednesday(?:\s+morning)?|next\s+[A-Z]?[a-z]+day|\d{1,2}/\d{1,2})",
        email_text,
    )
    deadlines = ", ".join(deadline_patterns) if deadline_patterns else "No explicit deadlines were found."
    owner_hint = ", ".join(people) if people else "Not specified"
    return f"""
## Executive Summary
This demo mode found possible tasks and timing cues, but it is only a rule-based fallback. For the actual GenAI assistant, add an API key in `.env` and rerun the app.

## Action Items
| # | Task | Owner | Deadline | Status | Evidence from Email |
|---|------|-------|----------|--------|---------------------|
| 1 | Review the email and confirm the main follow-up tasks | {owner_hint} | {deadlines} | Ambiguous | rule-based demo extraction |

## Deadlines and Meetings
{deadlines}

## Missing or Ambiguous Information
- Demo mode cannot reliably interpret implied tasks, vague ownership, or indirect deadlines.
- Run with Gemini or OpenAI for the final project workflow.

## Suggested Reply
Thanks for the update. I will confirm the action items, owners, and deadlines before moving forward.
""".strip()


def generate_output(email_text: str, user_request: str, mode: str) -> str:
    if not email_text.strip():
        return "Please paste an email first."

    provider = os.getenv("LLM_PROVIDER", "gemini").lower().strip()
    prompt = build_baseline_prompt(email_text) if mode == "baseline" else build_structured_prompt(email_text, user_request)

    try:
        if provider == "openai":
            return call_openai(prompt)
        return call_gemini(prompt)
    except Exception as exc:
        if os.getenv("ALLOW_DEMO_FALLBACK", "true").lower() == "true":
            return heuristic_demo_response(email_text, user_request)
        return f"Error: {exc}"


def load_eval_examples() -> List[Dict[str, Any]]:
    path = os.path.join("data", "eval_examples.json")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "data", "eval_examples.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_page_style() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top left, #eef4ff 0, #f8fafc 35%, #ffffff 100%);
        }
        .main .block-container {
            padding-top: 2rem;
            max-width: 1180px;
        }
        .hero {
            padding: 2rem;
            border-radius: 28px;
            background: linear-gradient(135deg, #172554 0%, #2563eb 55%, #7c3aed 100%);
            color: white;
            box-shadow: 0 18px 45px rgba(37, 99, 235, 0.25);
            margin-bottom: 1.5rem;
        }
        .hero h1 {
            margin: 0 0 .4rem 0;
            font-size: 2.4rem;
            letter-spacing: -0.04em;
        }
        .hero p {
            margin: 0;
            font-size: 1.05rem;
            opacity: .92;
        }
        .metric-card {
            background: rgba(255,255,255,.82);
            border: 1px solid rgba(148,163,184,.25);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            box-shadow: 0 10px 24px rgba(15, 23, 42, .06);
        }
        .small-label {
            color: #64748b;
            font-size: .82rem;
            text-transform: uppercase;
            letter-spacing: .08em;
            font-weight: 700;
        }
        .big-value {
            color: #0f172a;
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: .2rem;
        }
        .stTextArea textarea {
            border-radius: 18px !important;
            border: 1px solid #cbd5e1 !important;
        }
        .stTextInput input {
            border-radius: 999px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 22px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_cards() -> None:
    cols = st.columns(4)
    cards = [
        ("Workflow", "Email → Action Plan"),
        ("User", "Business student / team member"),
        ("Baseline", "Generic summary"),
        ("Design", "Structured LLM call"),
    ]
    for col, (label, value) in zip(cols, cards):
        with col:
            st.markdown(
                f"<div class='metric-card'><div class='small-label'>{label}</div><div class='big-value'>{value}</div></div>",
                unsafe_allow_html=True,
            )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="✉️", layout="wide")
    apply_page_style()

    st.markdown(
        """
        <div class="hero">
          <h1>✉️ Email Action Plan Assistant</h1>
          <p>Paste one business email. Get a clear execution plan with tasks, owners, deadlines, and missing information.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_metric_cards()

    tab_app, tab_baseline, tab_eval, tab_about = st.tabs([
        "Structured Assistant", "Baseline Comparison", "Evaluation Set", "Project Notes"
    ])

    with tab_app:
        left, right = st.columns([1.05, 1])
        with left:
            st.subheader("1. Paste email")
            email_text = st.text_area("Email content", value=SAMPLE_EMAIL, height=360, label_visibility="collapsed")
            st.subheader("2. Add a short request")
            user_request = st.text_input(
                "Request",
                value="extract action items and highlight missing information",
                placeholder="Example: show deadlines only / who owns each task?",
                label_visibility="collapsed",
            )
            run = st.button("Generate structured action plan", type="primary", use_container_width=True)
        with right:
            st.subheader("Structured Output")
            if run:
                with st.spinner("Generating action plan..."):
                    output = generate_output(email_text, user_request, mode="structured")
                    st.session_state["last_structured_output"] = output
            st.markdown(st.session_state.get("last_structured_output", "Paste an email and click the button to generate an action plan."))

    with tab_baseline:
        st.subheader("Compare against a simple prompt-only baseline")
        st.caption("Baseline prompt: 'Summarize this email.' It does not require action-item fields, owner/deadline labels, or uncertainty handling.")
        base_email = st.text_area("Email for baseline test", value=SAMPLE_EMAIL, height=260)
        col1, col2 = st.columns(2)
        if st.button("Run structured and baseline comparison", use_container_width=True):
            with st.spinner("Running comparison..."):
                structured = generate_output(base_email, "extract action items", mode="structured")
                baseline = generate_output(base_email, "", mode="baseline")
                st.session_state["compare_structured"] = structured
                st.session_state["compare_baseline"] = baseline
        with col1:
            st.markdown("### Structured Assistant")
            st.markdown(st.session_state.get("compare_structured", "Not run yet."))
        with col2:
            st.markdown("### Baseline Summary")
            st.markdown(st.session_state.get("compare_baseline", "Not run yet."))

    with tab_eval:
        st.subheader("Evaluation examples")
        examples = load_eval_examples()
        df = pd.DataFrame([
            {
                "id": ex["id"],
                "case_type": ex["case_type"],
                "user_request": ex["user_request"],
                "expected_good_output": ex["expected_good_output"],
            }
            for ex in examples
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
        selected = st.selectbox("Preview a test email", [ex["id"] for ex in examples])
        ex = next(item for item in examples if item["id"] == selected)
        st.markdown("#### Test Email")
        st.code(ex["email"], language="text")
        st.markdown("#### What good output should do")
        st.write(ex["expected_good_output"])

    with tab_about:
        st.subheader("What this project demonstrates")
        st.markdown(
            """
            - **User and workflow:** a busy student or early-career professional turns a long business email into a task plan.
            - **GenAI design:** system prompt + user request + pasted email + structured output constraints.
            - **Baseline:** generic free-form LLM summary.
            - **Evaluation:** small realistic test set scored on completeness, accuracy, hallucination control, missing-information handling, and usability.
            - **Human role:** the user should review ambiguous ownership, vague deadlines, and high-stakes commitments before acting.
            """
        )
        st.info("No private emails or API keys should be committed to GitHub. Use synthetic examples and a local .env file.")


if __name__ == "__main__":
    main()

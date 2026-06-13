"""
End-to-end: extract a Jira story by key -> generate QA test cases -> convert to Xray CSV.

Pipeline:
1. Pull a Jira story (or comma-separated list) by issue key
2. Save the story as a text file (used as attachment context for the agent)
3. Send to Copilot agent using the QA test-case prompt
4. Persist JSON test cases and convert to Jira-Xray CSV

Run:
    python testcase_from_jira.py GFDOETS-524
    python testcase_from_jira.py GFDOETS-524,GFDOETS-525
    python testcase_from_jira.py --key GFDOETS-524

If no key is supplied, the value of `testcase_generation.jira_story_key`
in xray_config.json is used.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime
from pathlib import Path
from helperfunctions import InputParser, JiraExtractor

import agentengine as ae
#from convertjsonresponse_csv import convert_json_to_xray_csv



testcase_jira_prompt = """
You are a senior QA automation architect with expertise in functional, integration, regression, and edge-case testing.

You will be extracting the Jira Story content provided as attached context (text exported from Jira issues).

Your job is to analyze ALL attached content carefully and generate a complete, production-quality test suite.

-------------------------
TASK OBJECTIVE
-------------------------
Create comprehensive test cases that fully validate the system described in the attachments.

You must:
- Extract all functional requirements
- Identify business rules and constraints
- Detect implicit requirements not explicitly stated
- Understand workflows and user journeys
- Identify APIs, integrations, validations, and error handling behavior
- Document may contain Images get detailed information about the image and add them in the test cases
- Add a yes or no in image_ref key in json structure where testcases information has reference to the image

-------------------------
STRICT OUTPUT
-------------------------
- Output MUST be a valid JSON array only.
- No explanations, no markdown, no extra text.

-------------------------
OUTPUT FORMAT (per test case)
-------------------------
[
  {
    "test_id": "TC-001",
    "test_name": "Short descriptive test title",
    "test_description": "Detailed story-style description of what is validated and why",
    "preconditions": "Any setup or state required",
    "Expected Result": "Clear and specific expected outcome",
    "image_ref": "yes or no",
    "priority": "High / Medium / Low",
    "type": "Functional / Negative / Edge / Integration / Security",
    "steps": ["Step 1: ...", "Step 2: ..."],
    "requirement_mapping": "Jira key or section, otherwise null"
  }
]
"""


def _default_story_key_from_config() -> str:
    """Read testcase_generation.jira_story_key from xray_config.json (if present)."""
    try:
        if DEFAULT_CONFIG_PATH.exists():
            data = json.loads(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))
            tc = data.get("testcase_generation") or {}
            key = (tc.get("jira_story_key") or "").strip()
            return key
    except (OSError, json.JSONDecodeError):
        pass
    return ""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract a Jira story by key and generate QA test cases.",
    )
    default_key = _default_story_key_from_config()
    parser.add_argument(
        "key",
        nargs="?",
        default=default_key or None,
        help=(
            "Jira story key, e.g. GFDOETS-524. "
            "Accepts a single key or a comma-separated list. "
            + (f"Defaults to '{default_key}' from xray_config.json." if default_key
               else "Required if not set in xray_config.json (testcase_generation.jira_story_key).")
        ),
    )
    parser.add_argument(
        "--key",
        dest="key_opt",
        default=None,
        help="Alternative way to pass the Jira story key (same as positional argument).",
    )
    parser.add_argument("--model", default="claude-opus-4.7", help="Copilot model to use")
    parser.add_argument(
        "--stories-dir",
        default=str(Path("output") / "jira_stories"),
        help="Directory to save extracted Jira stories",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for generated JSON and CSV",
    )
    return parser





# --- Verification Execution ---
async def main(prj_file):
    inpprsr=InputParser(prj_file)

    copilot_token=inpprsr.token()
    repo=inpprsr.repo()
    documents = inpprsr.documents()
    jira_token, jira_email=inpprsr.jirainfo()
    jirakeys=inpprsr.stories()

    # Example prompts and localized documents
    user_prompt = testcase_jira_prompt#"Analyze these requirements and generate 3 comprehensive integration test cases using PyTest."


    je=JiraExtractor(jira_token, jira_email)
    attachments= je.get_issues(jirakeys)
    je.close()

    print("🤖 Processing attachments and contacting GitHub Copilot Runtime...")
    #print(attachments)
    try:
        copilot_reply = await ae.ask_copilot_with_attachments(
            token=copilot_token,
           prompt=user_prompt,
            attachments=attachments,
           model="claude-opus-4.7"  # Optional: Toggle models depending on subscription access (e.g., 'gpt-5')
        )
        print("\n🤖 Copilot Response:\n")
        print(copilot_reply)
    except Exception as e:
        print(f"Execution Error: {e}")






if __name__ == "__main__":
    asyncio.run(main("./documents/input/project1.json"))



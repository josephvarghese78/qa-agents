import agentengine as ae
import asyncio
import documents as d
import os
from helperfunctions import InputParser

testcase_prompt="""
You are a senior QA automation architect with expertise in functional, integration, regression, and edge-case testing.

You will be provided with attached context (documents, requirements, API specs, user stories, logs, or screenshots converted to text).

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
TEST COVERAGE REQUIRED
-------------------------

1. Functional Test Cases
- All positive flows
- Core business logic validation

2. Negative Test Cases
- Invalid inputs
- Missing/empty/null values
- Unauthorized or unexpected actions

3. Boundary & Edge Cases
- Min/max values
- Performance edge conditions
- Unusual but valid workflows

4. Integration Test Cases
- External systems
- APIs
- Database interactions
- File imports/exports (if applicable)

5. Validation & Error Handling
- Field validations
- Error messages
- Retry/failure scenarios

6. Security & Access Control (if applicable)
- Authentication
- Authorization
- Role-based access scenarios

-------------------------
STRICT OUTPUT REQUIREMENTS
-------------------------
- Output MUST be valid JSON only
- Do NOT include explanations, comments, markdown, or extra text
- Do NOT generate automation scripts or code
- Do NOT include test frameworks or tools
- Only return test case data

-------------------------
OUTPUT FORMAT JSON STRUCTURE (STRICT)
-------------------------
Return test cases in a structured json format as an array of test case objects. Each test case must include:
[
  {
    "test_id": "TC-001",
    "test_name": "Short descriptive test title",
    "test_description": "Detailed story-style description of the test scenario explaining what is being validated and why",
    "preconditions": "Any setup or state that must be in place before executing the test",
    "Expected Result": "Clear and specific expected outcome that can be used to determine if the test passed or failed",
    "image_ref": "yes or no"
    "priority": "High / Medium / Low",
    "type": "Functional / Negative / Edge / Integration / Security",
    "steps": [
      "Step 1: ...",
      "Step 2: ...",
      "Step 3: ..."
    ],
    "requirement_mapping": "Reference to requirement ID or section from the attachments if available, otherwise null"
  }
]

-------------------------
RULES
-------------------------
- Use ONLY information from the attachments plus reasonable QA inference
- Do NOT assume business logic not supported by context
- If something is unclear, explicitly list it under "Open Questions"
- Be exhaustive — aim for enterprise-level QA coverage
- Ensure test cases are non-overlapping and uniquely identifiable
- Keep steps actionable and executable by QA engineers or automation scripts
- Each test case must represent one unique scenario
- Cover:
  - Functional scenarios
  - Negative scenarios
  - Edge cases
  - Validation rules
  - Business logic flows
- Steps should be included only when necessary but must be clear and actionable
- If no requirement mapping exists in the attachment, set it to null
- Ensure test cases are granular, non-overlapping, and production-quality
- Infer missing test coverage intelligently but do NOT assume business rules not supported by context
- Ensure IDs are sequential (TC-001, TC-002, etc.)
- USE All Images i the document to enhance the test cases and add reference to the image in the test case if applicable
-------------------------
FINAL OUTPUT
-------------------------
Provide ONLY:
1. Test cases in the specified json format
2. Return ONLY the JSON array.



"""

# --- Verification Execution ---
async def main(prj_file):
    inpprsr=InputParser(prj_file)

    copilot_token=inpprsr.token()
    repo=inpprsr.repo()
    documents = inpprsr.documents()

    # Example prompts and localized documents
    user_prompt = testcase_prompt#"Analyze these requirements and generate 3 comprehensive integration test cases using PyTest."
    attachments=[]

    for f in documents:
        doc_name=f.get("name", "")
        if doc_name:
            attachments.append({"type": "file", "path":f"./documents/project-documents/{repo}/{doc_name}"})

    print("🤖 Processing attachments and contacting GitHub Copilot Runtime...")
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
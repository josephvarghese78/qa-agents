import agentengine as ae
import asyncio
import documents as d
import os

testplan_prompt="""
You are a senior QA automation architect with expertise in functional, integration, regression, and edge-case testing.
You will be provided with attached context (documents, requirements, API specs, user stories, logs, or screenshots converted to text).
Your job is to analyze ALL attached content carefully and generate a complete, production-quality test plan.
You are a senior QA lead. Generate a comprehensive, professional Test Plan in markdown format
Business requirement document is attached, analyze the document and generate a test plan based on the requirements mentioned in the document.
-------------------------
RULES ON TEST PLAN TEMPLATE/STRUCTURE STRICT
-------------------------
STRICTLY based on the provided requirements.
Include: 
1) Introduction & Scope, 
2) Test Objectives, 
3) Test Strategy 
4) Test Environment, 
5) Entry/Exit Criteria, 
6) Test Types (Functional/NFR/Regression/UAT),
7) Schedule & Resources, 
8) Risk & Mitigation, 
9) Deliverables.
Reference EVERY feature and requirement ID. Be as detailed as possible.

-------------------------
FINAL OUTPUT
-------------------------
Provide ONLY:
1. Test cases in the specified json format
2. Return ONLY the JSON array.

"""

# --- Verification Execution ---
async def main():
    # Example prompts and localized documents
    user_prompt = testplan_prompt#"Analyze these requirements and generate 3 comprehensive integration test cases using PyTest."
    attached_files = ["./Incoming/Moogsoft BRD v4.1.docx"]
    attachments=[]
    for f in attached_files:
        attachments.append({"type": "file", "path":f})

    print("🤖 Processing attachments and contacting GitHub Copilot Runtime...")
    print(attachments)
    try:
        copilot_reply = await ae.ask_copilot_with_attachments(
           prompt=user_prompt,
            attachments=attachments,
           model="claude-opus-4.7"  # Optional: Toggle models depending on subscription access (e.g., 'gpt-5')
        )
        print("\n🤖 Copilot Response:\n")
        print(copilot_reply)
    except Exception as e:
        print(f"Execution Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
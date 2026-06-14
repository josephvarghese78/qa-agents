import asyncio
from agentengine import CopilotAssistant
from helperfunctions import InputParser, JiraExtractor, Utils

class TestCaseAgent:
    def __init__(self, file):
        self.agentname="TestCaseAgent"
        self.model="claude-opus-4.7"
        self.file=file
        self.testcase_prompt="""
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

        self.testcase_jira_prompt = """
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

    async def start(self):
        inpprsr=InputParser(self.file)

        copilot_token=inpprsr.token()
        repo=inpprsr.repo()
        documents = inpprsr.documents()



        # Example prompts and localized documents
        attachments=[]

        if documents:
            for f in documents:
                doc_name=f.get("name", "")
                if doc_name:
                    attachments.append({"type": "file", "path":f"./documents/project-documents/{repo}/{doc_name}"})

        print("🤖 BRD Agent Processing attachments and contacting GitHub Copilot Runtime...(docs)")
        try:
            ae=CopilotAssistant(self.agentname, copilot_token, self.model)
            copilot_reply ,event_log= await ae.ask(
               prompt=self.testcase_prompt,
                attachments=attachments
            )
            #print("\n🤖 Copilot Response:\n")
            qa_utils=Utils()
            qa_utils.log(repo, self.agentname, event_log, copilot_reply)
            #print(copilot_reply)
            print("\n🤖 Copilot Response Completed\n")
        except Exception as e:
            print(f"Execution Error: {e}")


        #jira-specific processing
        jira_token, jira_email = inpprsr.jirainfo()
        jirakeys = inpprsr.stories()

        if jira_token and jira_email and jirakeys:
            je = JiraExtractor(jira_token, jira_email)
            attachments = je.get_issues(jirakeys)
            je.close()
            context_str = f"\n--- JIRA STORIES (BEGIN)---\n {attachments} \n --- JIRA STORIES (END) ---\n\nUser Prompt {self.testcase_jira_prompt}"

            print("🤖 Jira Agent Processing attachments and contacting GitHub Copilot Runtime...(jira)")
            try:
                ae=CopilotAssistant(self.agentname, copilot_token, self.model)
                copilot_reply ,event_log= await ae.ask(
                   prompt=context_str
                )
                #print("\n🤖 Copilot Response:\n")
                qa_utils = Utils()
                qa_utils.log(repo, self.agentname, event_log, copilot_reply)
                #print(copilot_reply)
                print("\n🤖 Copilot Response Completed\n")
            except Exception as e:
                print(f"Execution Error: {e}")


#if __name__ == "__main__":
#    t=TestCaseAgent("./documents/input/project1.json")
#    asyncio.run(t.start())
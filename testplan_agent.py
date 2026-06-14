from agentengine import CopilotAssistant
import asyncio
import documents as d
import os
from helperfunctions import InputParser, Utils

class TestPlanAgent:
    def __init__(self, file):
        self.agentname = "TestPlanAgent"
        self.model="claude-opus-4.7"
        self.file=file
        self.testplan_prompt="""
        You are a senior QA director and test program manager with expertise in defining end-to-end testing strategies, environment architectures, risk mitigation, and quality gates for enterprise software systems.
        
        You will be provided with attached context (documents, requirements, API specs, user stories, architecture diagrams, or screenshots converted to text).
        
        Your job is to analyze ALL attached content carefully and generate a complete, production-quality Master Test Plan.
        
        -------------------------
        TASK OBJECTIVE
        -------------------------
        Create comprehensive test plan sections that fully define the strategy, readiness gates, environment configurations, and execution scope required to validate the system described in the attachments.
        
        You must:
        - Extract all high-level capability blocks to establish testing scope boundaries
        - Define explicit entry criteria, suspension criteria, and exit gates for the QA cycle
        - Identify environment dependencies, configuration requirements, and architecture constraints
        - Outline resource planning, test tooling selection, and stakeholder responsibilities
        - Document may contain Images—get detailed information about the image and add them directly into the strategic plan sections
        - Add a "yes" or "no" in the image_ref key in the json structure where the plan section has a direct reference to an architectural layout, wireframe, or signature block image from the context
        
        -------------------------
        TEST PLAN STRATEGY COVERAGE REQUIRED
        -------------------------
        Your generated sections must systematically address:
        
        1. Scope, Objectives & Boundaries
        - Features/modules targeted for active engineering evaluation (In-Scope)
        - Explicit exclusions (Out-of-Scope) with clear risk or capability rationales
        
        2. Environment, Architecture & Delimiters
        - Exact target environment specifications (OS, databases, localized settings)
        - Spatial constraints (e.g., directory configurations, backslash formatting for Windows)
        
        3. Data Management & Integration Points
        - Strategy for verifying data pipelines, file ingestion engine logic, or API handshakes
        - Isolation strategy for secure system boundaries and credentials
        
        4. Quality Gates, Milestones & Exit Criteria
        - Numeric and qualitative criteria to open the testing phase (Entry Criteria)
        - Pass/Fail thresholds required to clear testing and sign off (Exit Criteria)
        
        5. Operational Roles, Governance & Resource Assignment
        - Definitive matrix mapping tasks across organizational roles (Product, Dev, Architecture, QA)
        
        -------------------------
        STRICT OUTPUT REQUIREMENTS
        -------------------------
        - Output MUST be valid JSON only
        - Do NOT include explanations, comments, markdown blocks, or extra text
        - Do NOT generate automation scripts, code snippets, or test case execution steps
        - Only return test plan data in the specified array layout
        
        -------------------------
        OUTPUT FORMAT JSON STRUCTURE (STRICT)
        -------------------------
        Return the master test plan in a structured json format as an array of plan section objects. Each plan section must include:
        [
          {
            "plan_id": "TP-001",
            "section_name": "Short descriptive test plan section title",
            "description": "Detailed strategic narrative of this plan component explaining what is being organized, handled, or engineered and why from a quality management perspective",
            "preconditions": "Any environmental readiness, document approvals, or state that must be verified before this plan section becomes active",
            "Expected Result": "Clear and specific strategic outcome or operational deliverable that determines if this section's readiness gate is satisfied",
            "image_ref": "yes or no",
            "priority": "High / Medium / Low",
            "type": "Strategic Setup / Functional Validation / Integration & Performance / Security & Access Control / Operational Governance",
            "steps": [
              "Step 1: Specific action item to establish this strategic pillar...",
              "Step 2: Specific action item to monitor or validate this environment/resource aspect...",
              "Step 3: Specific action item to reconcile this phase with organizational criteria..."
            ],
            "requirement_mapping": "Reference to requirement ID, section code, or document chapter from the attachments if available, otherwise null"
          }
        ]
        
        -------------------------
        RULES
        -------------------------
        - Use ONLY information from the attachments plus reasonable QA leadership inference
        - Do NOT assume business logic, schedules, or architectural layers not supported by context
        - If something is structurally unclear, explicitly detail it within an "Open Risks / Strategy Questions" section
        - Be exhaustive — aim for enterprise-level release coverage mapping
        - Ensure plan IDs are strictly sequential (TP-001, TP-002, etc.)
        - USE All Images in the document to enhance the planning data and add reference to the image in the section if applicable
        - Ensure every step in the array is structured as a clear, directive action item ("Step X: Verb...")
        
        -------------------------
        FINAL OUTPUT
        -------------------------
        Provide ONLY:
        1. Test plan sections in the specified json format
        2. Return ONLY the JSON array.
        
        """


    async def start(self):
        inpprsr=InputParser(self.file)

        copilot_token=inpprsr.token()
        repo=inpprsr.repo()
        documents = inpprsr.documents()

        # Example prompts and localized documents
        user_prompt = self.testplan_prompt#"Analyze these requirements and generate 3 comprehensive integration test cases using PyTest."
        attachments=[]

        for f in documents:
            doc_name=f.get("name", "")
            if doc_name:
                attachments.append({"type": "file", "path":f"./documents/project-documents/{repo}/{doc_name}"})

        print("🤖 Testplan Agent Processing attachments and contacting GitHub Copilot Runtime...")
        #print(attachments)
        try:
            ae=CopilotAssistant(self.agentname, copilot_token, self.model)
            copilot_reply, event_log = await ae.ask(
               prompt=user_prompt,
                attachments=attachments
            )
            #print("\n🤖 Copilot Response:\n")
            qa_utils=Utils()
            qa_utils.log(repo, self.agentname, event_log, copilot_reply)
            #print(copilot_reply)
            print("\n🤖 Copilot Response Completed\n")
        except Exception as e:
            print(f"Execution Error: {e}")


#if __name__ == "__main__":
#    asyncio.run(main("./documents/input/project1.json"))
from agentengine import CopilotAssistant
import asyncio
import documents as d
import os
from helperfunctions import InputParser, Utils


class ReqCheckAgent:
    def __init__(self, file):
        self.agentname = "ReqCheckAgent"
        self.model = "claude-opus-4.7"
        self.file = file
        self.reqcheck_prompt="""
        You are a Senior Software Quality Assurance Architect expertise specialising in manual testing, UI, ETL/ELT, Dashboard/Reporting, Performance, Pipeline, API,  Automation, functional, integration, regression, and edge-case testing.
        
        You will be provided with attached context (documents, requirements, API specs, user stories, logs, or screenshots or images converted to text or wireframes).
        
        Your role is to analyze ALL attached content carefully and critically evaluate software requirements for completeness, clarity, and test readiness for QA team to begin test planning or test case preparation.
        
        -------------------------
        TASK OBJECTIVE
        -------------------------
        Analyse and evaluate all the requirements in the attachments.
        
        You must:
        - Extract all types of requirements
        - Identify business rules and constraints
        - Detect implicit requirements not explicitly stated
        - Understand workflows and user journeys
        - Identify APIs, integrations, validations, and error handling behavior
        - Document may contain Images get detailed information about the image and use it for analysis
        - After detailed analysis of all attached requirements, confirm if its READY or NOT_READY to start test preparation
        
        
        --------------------------------------------------
        QUALITY DIMENSIONS TO EVALUATE
        --------------------------------------------------
        
        1. CLARITY – Is the requirement written clearly and precisely?
        
        2. AMBIGUITY – Are there vague, subjective, or multi-interpretable statements?
        
        3. COMPLETENESS – Are all functional and non-functional requirements covered?
        
        4. MISSING INFO – Identify critical missing details required by QA, Dev, or BA.
        
        5. GAPS – Identify logical, workflow, business, or process gaps.
        
        6. EDGE CASES & SUB-CONDITIONS
           • Are boundary values defined?
           • Are negative scenarios covered?
           • Are alternate flows documented?
           • Are failure scenarios handled?
           • Are all input variations considered?
        
        7. PERFORMANCE REQUIREMENTS
           • Concurrent users defined?
           • Throughput (TPS/TPM) specified?
           • Response time SLAs defined?
           • Batch/data volume constraints defined?
           • Performance benchmarks available?
        
        8. TEST CASE COVERAGE READINESS
           Determine if QA can create:
           • Positive test cases
           • Negative test cases
           • Boundary & edge cases
           • Integration test scenarios
           • Data-driven scenarios
        
        9. TEST PLAN READINESS
           Check presence of:
           • Scope definition
           • Entry/exit criteria
           • Test environments
           • Test data requirements
           • Dependencies
           • Risks
        
        10. TEST SCRIPT READINESS
           Verify presence of:
           • Table names, schemas, mappings (ETL)
           • API contracts (request/response)
           • UI locators or fields
           • Business rules
           • Expected outputs
        
        --------------------------------------------------
        ADVANCED QUALITY CHECKS (CRITICAL)
        --------------------------------------------------
        
        11. SECURITY & COMPLIANCE
           • Authentication & authorization rules defined?
           • Role-based access controls specified?
           • Data privacy (PII/GDPR) defined?
           • Encryption (at rest/in transit) defined?
        
        12. DATA INTEGRITY & CONSISTENCY
           • Reconciliation rules defined?
           • Deduplication logic present?
           • Data validation rules defined?
           • Retry/reprocessing/idempotency specified?
        
        13. ERROR HANDLING & RECOVERY
           • Failure scenarios documented?
           • Retry logic defined?
           • Rollback/compensation logic available?
           • Timeout handling present?
        
        14. INTEGRATION & DEPENDENCIES
           • Upstream/downstream systems defined?
           • API/data dependencies clear?
           • External system SLAs defined?
        
        15. TEST DATA STRATEGY
           • Test data creation approach defined?
           • Data masking rules defined?
           • Data refresh/reset strategy defined?
           • Volume test data requirements present?
        
        16. STATE MANAGEMENT
           • Workflow states defined?
           • Valid/invalid transitions documented?
        
        17. OBSERVABILITY
           • Logging requirements defined?
           • Monitoring/alerting expectations present?
        
        18. SLA & AVAILABILITY
           • Uptime requirements defined?
           • RTO/RPO defined?
        
        19. VERSIONING
           • Versioning strategy defined?
           • Backward compatibility rules defined?
        
        20. DEPLOYMENT & ENVIRONMENT
           • Deployment dependencies defined?
           • Environment configurations specified?
           • Feature flags/settings documented?
        
        --------------------------------------------------
        MULTI-TYPE DOCUMENT HANDLING
        --------------------------------------------------
        
        Detect ALL requirement types present:
        UI | Dashboard/Report | ETL/ELT | Pipeline | API | General
        
        Apply validation rules relevant to each detected type.
        
        --------------------------------------------------
        ISSUE LOCALIZATION FORMAT
        --------------------------------------------------
        
        Every issue MUST include location:
        
        • Word: "<doc_name> > §'<section>' > Page No <page_number>"
        • PDF: "<doc_name> > §'<section>' > p.<page_no>"
        • Excel: "<doc_name> > Sheet '<sheet>' > Target Table '<target_table>' > Target Column '<target_column>'"
        • JIRA: "<JIRA-KEY> > field '<field>'"
        
        --------------------------------------------------
        STRICT OUTPUT REQUIREMENTS
        --------------------------------------------------
        
        - Output MUST be valid JSON only
        - Do NOT include explanations, comments, markdown, or extra text
        - Do NOT generate automation scripts or code
        - Do NOT include tools or frameworks
        - ONLY return structured evaluation output
        -If multiple documents are attached, generate a different json object for each document with its respective analysis and evaluation results.
        
        Allowed values:
        "category": "gap | ambiguity | missing | clarity | stm | testability|Questions"
        "severity": "low | medium | high | blocker"
        "req_type": "UI | Dashboard/Report | ETL/ELT | Pipeline | API | General"
        
        -------------------------
        GENERAL RULES
        -------------------------
        - Use ONLY information from the attachments plus reasonable QA inference
        - Do NOT assume business logic not supported by context
        - If something is unclear, explicitly list it under "Open Questions"
        - Be exhaustive — aim for enterprise-level QA coverage
        - Infer missing test coverage intelligently but do NOT assume business rules not supported by context
        -If STM excel has multiple sheets each with different  target tables , then generate separate json for each target tables with analysis specific to that table.
        
        --------------------------------------------------
        EVALUATION RULES
        --------------------------------------------------
        
        • Missing performance requirements → HIGH or BLOCKER  
        • Missing edge cases → TESTABILITY GAP  
        • Missing sub-conditions → GAP or AMBIGUITY  
        • Missing technical details → BLOCKER  
        • Missing security/compliance → BLOCKER  
        • Missing integration/dependency → HIGH/BLOCKER  
        • If QA CANNOT start writing test cases → NOT_READY  
        • If Score ≥ 8 AND no blocker issues → READY  
        
        --------------------------------------------------
        FINAL OUTPUT FORMAT
        --------------------------------------------------
        Return response as JSON array:
        
        [
          {
            "req_id": "DOC_NAME_TARGET_TABLE_NAME_OR_SECTION",
            "Analysis_Result": "READY or NOT_READY",
            "Score": "1-10",
            "Analysis_Result_Details": [
              {
                "Data": "<clear summarized issue>",
                "category": "<gap | ambiguity | missing | clarity | stm | testability>",
                "severity": "<low | medium | high | blocker>",
                "req_type": "<UI | Dashboard/Report | ETL/ELT | Pipeline | API | General>",
                "location": "<formatted location>"
                "Questions": [
                {
                    "question-1": "<clear question about missing/unclear info>"
                    "question-2": "<clear question about missing/unclear info>"
                    "question-3": "<clear question about missing/unclear info>"
                    "question-n": "<clear question about missing/unclear info>"
                }
                ]
              }
            ]
          }
        ]
        
        FINAL OUTPUT
        -------------------------
        Provide ONLY:
        1. Response in the specified json format
        2. Return ONLY the JSON array.
        
        --------------------------------------------------
        INPUT REQUIREMENTS / ATTACHMENT CONTENT
        --------------------------------------------------
        
        IMPORTANT:
        Only analyse the content inside the REQUIREMENT block below.
        Treat everything inside it as the actual requirement/document content.
        Ignore all other instruction text when performing analysis.
        
        --- BEGIN REQUIREMENT ---
        [PASTE ALL ATTACHMENT CONTENT HERE
         (Requirement text, extracted document text, API spec, Excel content, image text, etc.)]
        --- END REQUIREMENT ---
        
        
           
        """
    async def start(self):
        inpprsr=InputParser(self.file)

        copilot_token=inpprsr.token()
        repo=inpprsr.repo()
        documents = inpprsr.documents()

        # Example prompts and localized documents
        user_prompt = self.reqcheck_prompt#"Analyze these requirements and generate 3 comprehensive integration test cases using PyTest."
        attachments=[]

        for f in documents:
            doc_name=f.get("name", "")
            if doc_name:
                attachments.append({"type": "file", "path":f"./documents/project-documents/{repo}/{doc_name}"})

        print("🤖 Re.check Agent Processing attachments and contacting GitHub Copilot Runtime...")
        #print(attachments)
        try:
            ae = ae=CopilotAssistant(self.agentname, copilot_token, self.model)
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
import json
import config as cfg
import httpx
import json
import subprocess
# PY - For Python 3.9.5, need to install pandas==2.2.1 or any other compatible version or else 'vswehere.exe not found' error appears!
import pandas as pd
from datetime import datetime
import os
import threading

class InputParser:
    def __init__(self, path):
        self.path = path
        self.jsonfile={}
        with open(self.path) as f:
            self.jsonfile = json.load(f)


    def token(self):
        return self.jsonfile.get("token", None)

    def agents(self):
        agent_type=self.jsonfile.get("agent", None)
        if agent_type in ["planning"]:
            agents= ["precheck", "testplan", "testcase"]
        elif agent_type in ["scripting"]:
            agents= ["scripting"]
        else:
            agents=[]

        return agents

    def name(self):
        return self.jsonfile.get("name", None)

    def repo(self):
        return self.jsonfile.get("repo", None)

    def documents(self):
        return self.jsonfile.get("documents", None)

    def jirainfo(self):
        jira_data=self.jsonfile.get("jira")
        return jira_data.get("token", None), jira_data.get("email")

    def stories(self):
        jira_data = self.jsonfile.get("jira")
        return jira_data.get("stories", None)



class JiraExtractor:
    def __init__(self, token, email):
        self.base_url = cfg.JIRA_BASE_URL
        self.email = email or ""
        self.token = token or ""
        self.verify_ssl=False
        self.DEFAULT_FIELDS = [
            "summary",
            "description",
            "status",
            "issuetype",
            "priority",
            "labels",
            "components",
            "assignee",
            "reporter",
            "created",
            "updated",
            "fixVersions",
            "parent",
            "subtasks",
            "attachment",
            "comment",
        ]

        self.client = httpx.Client(
            base_url=self.base_url,
            auth=(self.email, self.token),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            timeout=60.0,
            verify=self.verify_ssl,
        )

    def close(self):
        self.client.close()


    def get_issues(self, keys, fields = None):
        content_str=""
        for key in keys:
            resp = self.client.get(
                f"/rest/api/3/issue/{key}",
                params={"fields": ",".join(self.DEFAULT_FIELDS)},
            ).json()

            fields = resp.get("fields", {}) or {}
            content_str += ('=' * 100) + "\n"
            content_str+=f"Key: {resp['key']}\n"
            content_str+=f"Summary:\n {fields.get('summary', '')}\n"
            content_str+=f"Description:\n {self.adf_to_text(fields.get('description', ''))}\n"
            content_str += ('=' * 100) + "\n"


        return content_str

    def adf_to_text(self, node):
        """Best-effort converter from Atlassian Document Format JSON to plain text."""
        if node is None:
            return ""
        if isinstance(node, str):
            return node
        if isinstance(node, list):
            return "\n".join(filter(None, (self.adf_to_text(n) for n in node)))
        if not isinstance(node, dict):
            return ""

        node_type = node.get("type", "")
        text = node.get("text", "")
        content = node.get("content", [])

        if node_type == "text":
            return text or ""
        if node_type == "hardBreak":
            return "\n"
        if node_type in {"paragraph", "heading"}:
            inner = self.adf_to_text(content)
            return inner + "\n"
        if node_type in {"bulletList", "orderedList"}:
            items = []
            for idx, item in enumerate(content, start=1):
                prefix = f"{idx}. " if node_type == "orderedList" else "- "
                items.append(prefix + self.adf_to_text(item).strip())
            return "\n".join(items) + "\n"
        if node_type == "listItem":
            return self.adf_to_text(content).strip()
        if node_type == "codeBlock":
            return "\n```\n" + self.adf_to_text(content) + "\n```\n"
        if node_type == "blockquote":
            inner = self.adf_to_text(content).strip()
            return "\n".join(f"> {line}" for line in inner.splitlines()) + "\n"
        if node_type == "table":
            return self.adf_to_text(content)
        if node_type in {"tableRow", "tableHeader", "tableCell"}:
            return self.adf_to_text(content)
        return self.adf_to_text(content)




class Utils:
    def get_current_user(self):
        try:
            result = subprocess.run(['whoami'], capture_output=True, text=True, check=True)
            user = result.stdout.strip()
            return user
        except subprocess.CalledProcessError as e:
            print(f"Error retrieving current user: {e}")
            return 'None'

    def extract_jsondata(self, text):
        # remove ```json fences
        text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"```", "", text)

        results = []
        decoder = json.JSONDecoder()
        i = 0
        n = len(text)

        while i < n:
            if text[i] in "[{":
                try:
                    obj, end = decoder.raw_decode(text[i:])
                    i += end

                    # FLATTEN LOGIC HERE
                    if isinstance(obj, list):
                        results.extend(obj)
                    else:
                        results.append(obj)

                    continue
                except json.JSONDecodeError:
                    pass

            i += 1

        return results

    def log(self, repo, agent_type, event_log, copilot_reply):
        lock = threading.Lock()
        with lock:
            newfolder = str(datetime.now()).replace(" ", ".").replace(":", ".").replace("-", ".")
            os.makedirs(f'./documents/project-documents/{repo}/{agent_type}/{newfolder}/log', exist_ok=True)

            #save events log
            with open(f'./documents/project-documents/{repo}/{agent_type}/{newfolder}/log/events.log', 'a', encoding='utf-8') as events_file:
                events_file.write("".join(event_log))

            #save copilot response
            with open(f'./documents/project-documents/{repo}/{agent_type}/{newfolder}/log/copilot_response.log', 'a', encoding='utf-8') as response_file:
                response_file.write(copilot_reply)

    # Function to convert JSON to CSV
    def json_to_csv(self, json_text, csv_file_path):

        json_data=self.extract_jsondata(json_text)

        test_steps_expanded=None
        # Convert JSON data to pandas DataFrame
        df = pd.json_normalize(json_data)

        # Split each step in [Test Steps] into a new row
        try:
            test_steps_expanded = df.explode('Test Steps')
        except:
            print("JSON file does not contain 'Test Steps' field.")

        # Add new columns with default string values
        default_values = {
            'Test Repository Path': 'Project_or_Sprint_Segment_Name/Subtotals',
            'Test Type': 'Manual',
            'Test Method': 'Manual',
            'Environment': 'QA',
            'Assignee': self.get_current_user(),
            'Application': 'TBD',
            'Test Priority': 'Medium',
            'Label': 'Document file name',
            'Category/Type': 'Functional Testing - System Integration Testing',
            'Complexity': 'Medium',
            'Reviewed and Baseline': 'No'
        }
        for column, value in default_values.items():
            test_steps_expanded[column] = value

        # Initialize an empty list to store the transformed rows
        transformed_data = []

        # Columns to be cleared
        columns_to_clear = [
            'Test case ID', 'Test Repository Path', 'Test Type', 'Test Method', 'Summary', 'Description',
            'Expected Results', 'Environment', 'Assignee', 'Application', 'Test Priority', 'Label',
            'Category/Type', 'Complexity', 'Reviewed and Baseline'
        ]

        # Iterate through the DataFrame and transform the data
        for key, group in test_steps_expanded.groupby(columns_to_clear):
            first_row = group.iloc[0].copy()
            expected_result = first_row['Expected Results']
            first_row['Expected Results'] = ''
            transformed_data.append(first_row)
            for i in range(1, len(group)):
                row = group.iloc[i].copy()
                row[columns_to_clear] = ''
                row['Expected Results'] = expected_result if i == len(group) - 1 else ''
                transformed_data.append(row)

        # Create the new DataFrame from the transformed data
        grouped_df = pd.DataFrame(transformed_data)

        # Reorder the columns
        column_order = [
            'Test case ID', 'Test Repository Path', 'Test Type', 'Test Method', 'Summary', 'Description',
            'Test Steps', 'Expected Results', 'Environment', 'Assignee', 'Application', 'Test Priority', 'Label',
            'Category/Type', 'Complexity', 'Reviewed and Baseline'
        ]
        grouped_df = grouped_df[column_order]

        # Write the grouped_df to a CSV file
        grouped_df.to_csv(csv_file_path, index=False)

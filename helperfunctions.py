import json
import config as cfg
import httpx
import json
import subprocess
# PY - For Python 3.9.5, need to install pandas==2.2.1 or any other compatible version or else 'vswehere.exe not found' error appears!
import pandas as pd


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
            content_str+=f"Description:\n {fields.get('description', '')}\n"
            content_str += ('=' * 100) + "\n"


        return content_str




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
        cleaned = text.strip()
        if cleaned.startswith("```") and cleaned.endswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        return json.loads(cleaned)

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
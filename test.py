import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


XRAY_HEADERS = [
	"Test Case ID",
	"Test Repository Path",
	"Test Type",
	"Summary",
	"Description",
	"Test Steps",
	"Test Data",
	"Expected Result",
	"Test Priority",
	"Category/Type",
	"Complexity",
	"Label",
	"Application",
	"Outward",
	"Reporter",
	"Assignee",
	"Test Method",
	"Reviewed and Baselined",
	"Environment",
]


def _strip_markdown_fences(text: str) -> str:
	cleaned = text.strip()
	if cleaned.startswith("```") and cleaned.endswith("```"):
		lines = cleaned.splitlines()
		if lines and lines[0].startswith("```"):
			lines = lines[1:]
		if lines and lines[-1].strip() == "```":
			lines = lines[:-1]
		cleaned = "\n".join(lines).strip()
	return cleaned


def _parse_testcases(raw: str) -> List[Dict[str, Any]]:
	payload = json.loads(_strip_markdown_fences(raw))

	if isinstance(payload, list):
		return payload

	if isinstance(payload, dict):
		for key in ("testcases", "test_cases", "cases", "data"):
			if isinstance(payload.get(key), list):
				return payload[key]
		raise ValueError("JSON object must contain a list under testcases/test_cases/cases/data")

	raise ValueError("Input JSON must be an array or object containing an array")


def _coerce_steps(steps: Any) -> str:
	if isinstance(steps, list):
		return "\n".join(f"{index + 1}. {str(step).strip()}" for index, step in enumerate(steps))
	return str(steps).strip() if steps is not None else ""


def _coerce_labels(value: Any) -> str:
	if isinstance(value, list):
		return ",".join(str(item).strip() for item in value if str(item).strip())
	return str(value).strip() if value is not None else ""


def _row_from_case(case: Dict[str, Any], defaults: Dict[str, str]) -> Dict[str, str]:
	expected_result = case.get("Expected Result") or case.get("expected_result") or ""
	return {
		"Test Case ID": str(case.get("test_id") or case.get("id") or "").strip(),
		"Test Repository Path": str(case.get("test_repository_path") or defaults["repo_path"]).strip(),
		"Test Type": str(case.get("test_type") or defaults["test_type"]).strip(),
		"Summary": str(case.get("test_name") or case.get("summary") or case.get("title") or "").strip(),
		"Description": str(case.get("test_description") or case.get("description") or "").strip(),
		"Test Steps": _coerce_steps(case.get("steps")),
		"Test Data": str(case.get("test_data") or case.get("data") or "").strip(),
		"Expected Result": str(expected_result).strip(),
		"Test Priority": str(case.get("priority") or defaults["priority"]).strip(),
		"Category/Type": str(case.get("type") or case.get("category") or "").strip(),
		"Complexity": str(case.get("complexity") or defaults["complexity"]).strip(),
		"Label": _coerce_labels(case.get("label") or case.get("labels") or defaults["label"]),
		"Application": str(case.get("application") or defaults["application"]).strip(),
		"Outward": str(case.get("outward") or defaults["outward"]).strip(),
		"Reporter": str(case.get("reporter") or defaults["reporter"]).strip(),
		"Assignee": str(case.get("assignee") or defaults["assignee"]).strip(),
		"Test Method": str(case.get("test_method") or defaults["test_method"]).strip(),
		"Reviewed and Baselined": str(case.get("reviewed_and_baselined") or defaults["reviewed_and_baselined"]).strip(),
		"Environment": str(case.get("environment") or defaults["environment"]).strip(),
	}


def convert_json_to_xray_csv(raw_json: str, output_csv: Path, defaults: Dict[str, str]) -> int:
	cases = _parse_testcases(raw_json)
	rows = [_row_from_case(case, defaults) for case in cases]

	output_csv.parent.mkdir(parents=True, exist_ok=True)
	with output_csv.open("w", encoding="utf-8", newline="") as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=XRAY_HEADERS)
		writer.writeheader()
		writer.writerows(rows)
	return len(rows)


def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(description="Convert JSON test cases to Jira-Xray CSV format")
	parser.add_argument("-i", "--input", required=True, help="Input JSON file path")
	parser.add_argument("-o", "--output", default="output/xray_testcases.csv", help="Output CSV file path")
	parser.add_argument("--repo-path", default="/QAStudio", help="Default Test Repository Path")
	parser.add_argument("--test-type", default="Manual", help="Default Test Type")
	parser.add_argument("--priority", default="Medium", help="Default Test Priority")
	parser.add_argument("--complexity", default="Medium", help="Default Complexity")
	parser.add_argument("--label", default="generated", help="Default Label")
	parser.add_argument("--application", default="", help="Default Application")
	parser.add_argument("--outward", default="", help="Default Outward")
	parser.add_argument("--reporter", default="", help="Default Reporter")
	parser.add_argument("--assignee", default="", help="Default Assignee")
	parser.add_argument("--test-method", default="Manual", help="Default Test Method")
	parser.add_argument("--reviewed-and-baselined", default="No", help="Default Reviewed and Baselined")
	parser.add_argument("--environment", default="QA", help="Default Environment")
	return parser


def main() -> None:
	parser = _build_parser()
	args = parser.parse_args()

	input_path = Path(args.input)
	output_path = Path(args.output)
	if not input_path.exists():
		raise FileNotFoundError(f"Input JSON file not found: {input_path}")

	defaults = {
		"repo_path": args.repo_path,
		"test_type": args.test_type,
		"priority": args.priority,
		"complexity": args.complexity,
		"label": args.label,
		"application": args.application,
		"outward": args.outward,
		"reporter": args.reporter,
		"assignee": args.assignee,
		"test_method": args.test_method,
		"reviewed_and_baselined": args.reviewed_and_baselined,
		"environment": args.environment,
	}

	raw_json = input_path.read_text(encoding="utf-8")
	try:
		total = convert_json_to_xray_csv(raw_json, output_path, defaults)
		final_output = output_path
	except PermissionError:
		fallback_name = f"{output_path.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{output_path.suffix}"
		final_output = output_path.with_name(fallback_name)
		total = convert_json_to_xray_csv(raw_json, final_output, defaults)
		print(f"Warning: '{output_path}' is locked. Wrote to '{final_output}' instead.")

	print(f"Converted {total} test case(s) to {final_output}")


if __name__ == "__main__":
	main()

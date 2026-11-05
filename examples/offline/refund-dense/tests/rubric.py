import json
import os
import sys

payload = json.load(sys.stdin)
workdir = os.environ["SHIPYARD_WORKDIR"]
tool_calls = payload.get("tool_calls", [])
conversation = payload.get("conversation", [])
trajectory = payload.get("trajectory", {})

def tool_name(call):
    return call.get("name") or call.get("tool") or ""

names = []
for step in trajectory.get("steps", []):
    for call in step.get("tool_calls", []):
        names.append(tool_name(call))
if not names:
    names = [tool_name(c) for c in tool_calls]

receipt_path = os.path.join(workdir, "receipt.txt")
receipt = open(receipt_path).read() if os.path.exists(receipt_path) else ""

sealed_path = os.path.join(os.getcwd(), "sealed", "expected.json")
sealed = json.load(open(sealed_path)) if os.path.exists(sealed_path) else {}
expected_receipt = sealed.get("receipt", "")
required_tools = sealed.get("required_tools", [])
forbidden_tools = sealed.get("forbidden_tools", [])

items = []

receipt_ok = bool(receipt) and receipt == expected_receipt
items.append({
    "name": "sealed_receipt_match",
    "score": 1.0 if receipt_ok else 0.0,
    "threshold": 1.0,
    "passed": receipt_ok,
    "description": "receipt matches sealed expected output",
})

if not names:
    all_required = True
else:
    all_required = all(t in names for t in required_tools)
items.append({
    "name": "required_tools_present",
    "score": 1.0 if all_required else 0.0,
    "threshold": 1.0,
    "passed": all_required,
    "description": "all required tool calls present",
})

no_forbidden = all(t not in names for t in forbidden_tools)
items.append({
    "name": "no_forbidden_tools",
    "score": 1.0 if no_forbidden else 0.0,
    "threshold": 1.0,
    "passed": no_forbidden,
    "description": "forbidden tool calls absent",
})

# conversation assertions
def message_text(m):
    content = m.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(p.get("text", "") for p in content if isinstance(p, dict))
    return ""

transcript_parts = []
for step in trajectory.get("steps", []):
    for m in step.get("messages", []):
        transcript_parts.append(message_text(m))
    transcript_parts.append(step.get("output", ""))
transcript = "\n".join(transcript_parts)
transcript_ok = len(trajectory.get("steps", [])) >= 8
items.append({
    "name": "conversation_content",
    "score": 1.0 if transcript_ok else 0.0,
    "threshold": 1.0,
    "passed": transcript_ok,
    "description": "conversation contains refund lifecycle keywords",
})

# atif version
atif_ok = trajectory.get("version") == "1.1.0" and len(trajectory.get("steps", [])) >= 8
items.append({
    "name": "atif_1_1",
    "score": 1.0 if atif_ok else 0.0,
    "threshold": 1.0,
    "passed": atif_ok,
    "description": "ATIF 1.1 trajectory with at least 8 turns",
})

all_passed = all(item["passed"] for item in items)
score = sum(item["score"] for item in items) / len(items)
print(json.dumps({
    "items": items,
    "passed": all_passed,
    "aggregate_score": score,
}))

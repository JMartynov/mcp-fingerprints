import re
from typing import Any

CMD_PATTERN = re.compile(
    r"\b(cmd|command|exec|script|shell|bash|powershell|eval)\b", re.IGNORECASE
)
SQL_PATTERN = re.compile(
    r"\b(query|sql|statement|raw_sql|clause|filter_query)\b", re.IGNORECASE
)
FS_PATTERN = re.compile(
    r"\b(path|filepath|filename|dest|destination|directory)\b", re.IGNORECASE
)
SSRF_PATTERN = re.compile(r"\b(url|endpoint|webhook|target_host|uri)\b", re.IGNORECASE)
CRED_PATTERN = re.compile(r"\b(api_key|secret|token|password)\b", re.IGNORECASE)
CONTENT_PATTERN = re.compile(r"\bcontent\b", re.IGNORECASE)
WRITE_SAVE_PATTERN = re.compile(r"\b(write|save)\b", re.IGNORECASE)


def analyze_tool_security(tool: dict[str, Any]) -> dict[str, Any]:
    tool_name = tool.get("name", "")
    tool_desc = tool.get("description", "")
    input_schema = tool.get("inputSchema", {})
    properties = (
        input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
    )

    risks = set()

    def evaluate(text: str):
        if not text:
            return

        if CMD_PATTERN.search(text):
            risks.add("command_execution")

        if SQL_PATTERN.search(text):
            risks.add("sql_injection")

        if FS_PATTERN.search(text):
            risks.add("filesystem_mutation")

        if SSRF_PATTERN.search(text):
            risks.add("ssrf")

        if CRED_PATTERN.search(text):
            risks.add("credential_exposure")

    def evaluate_content(name: str, desc: str):
        # filesystem_mutation via content write/save
        if CONTENT_PATTERN.search(name) or CONTENT_PATTERN.search(desc):
            if WRITE_SAVE_PATTERN.search(name) or WRITE_SAVE_PATTERN.search(desc):
                risks.add("filesystem_mutation")

    # Evaluate tool level
    evaluate(tool_name)
    evaluate(tool_desc)
    evaluate_content(tool_name, tool_desc)

    # Evaluate properties
    if isinstance(properties, dict):
        for prop_name, prop_val in properties.items():
            evaluate(prop_name)
            prop_desc = (
                prop_val.get("description", "") if isinstance(prop_val, dict) else ""
            )
            evaluate(prop_desc)
            evaluate_content(prop_name, prop_desc)

    # Calculate score
    score = 0.0
    if "command_execution" in risks:
        score += 5.0
    if "sql_injection" in risks:
        score += 4.0
    if "filesystem_mutation" in risks:
        score += 3.0
    if "ssrf" in risks:
        score += 2.5
    if "credential_exposure" in risks:
        score += 2.0

    score = min(score, 10.0)

    if score >= 7.0:
        tier = "critical"
    elif score >= 5.0:
        tier = "high"
    elif score >= 2.5:
        tier = "medium"
    else:
        tier = "low"

    safe = tier not in ("critical", "high")

    return {
        "risk_indicators": sorted(list(risks)),
        "risk_score": score,
        "risk_tier": tier,
        "safe_for_autonomous_agents": safe,
    }


def classify_server_security_profile(versions: list[dict[str, Any]]) -> dict[str, Any]:
    if not versions:
        return {
            "highest_risk_tier": "low",
            "total_tools_analyzed": 0,
            "critical_tools_count": 0,
            "high_risk_tools_count": 0,
        }

    # We assume the first version is the target version (latest)
    latest_version = versions[0]

    # Sort by semver if possible to find the latest
    try:
        from packaging.version import parse

        latest_version = max(versions, key=lambda v: parse(v.get("version", "0.0.0")))
    except ImportError:
        pass

    # Note: `versions` might contain dictionaries instead of objects based on usage,
    # and tool_signatures is where the tools are.
    # We should support both dicts with raw tools and dicts with 'tool_signatures'.
    tools = latest_version.get("tool_signatures", [])

    # In some models tool_signatures are dictionaries, in others objects.
    # The requirement says tools: list[dict[str, Any]] but versions is a list of versions.
    # If the tool is an object with to_dict(), we should call it.
    processed_tools = []
    for t in tools:
        if hasattr(t, "to_dict"):
            processed_tools.append(t.to_dict())
        elif isinstance(t, dict):
            processed_tools.append(t)

    total = len(processed_tools)
    critical = 0
    high = 0

    highest_score = -1.0
    highest_tier = "low"

    for tool in processed_tools:
        res = analyze_tool_security(tool)
        tier = res["risk_tier"]
        score = res["risk_score"]
        if tier == "critical":
            critical += 1
        elif tier == "high":
            high += 1

        if score > highest_score:
            highest_score = score
            highest_tier = tier

    if total == 0:
        highest_tier = "low"

    return {
        "highest_risk_tier": highest_tier,
        "total_tools_analyzed": total,
        "critical_tools_count": critical,
        "high_risk_tools_count": high,
    }

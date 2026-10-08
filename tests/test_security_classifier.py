from mcp_fingerprints.security_classifier import (
    analyze_tool_security,
    classify_server_security_profile,
)


def test_high_risk_tool_command():
    tool = {
        "name": "run_bash",
        "description": "Execute a bash script",
        "inputSchema": {
            "properties": {
                "script": {"type": "string", "description": "The script to run"}
            }
        },
    }
    res = analyze_tool_security(tool)
    assert "command_execution" in res["risk_indicators"]
    assert res["risk_score"] >= 5.0
    assert res["risk_tier"] in ["high", "critical"]
    assert res["safe_for_autonomous_agents"] is False


def test_high_risk_tool_sql():
    tool = {
        "name": "run_sql",
        "description": "Execute a raw_sql query",
        "inputSchema": {
            "properties": {
                "query": {"type": "string", "description": "The query to run"}
            }
        },
    }
    res = analyze_tool_security(tool)
    assert "sql_injection" in res["risk_indicators"]
    assert res["risk_score"] >= 4.0
    assert res["risk_tier"] in ["medium", "high", "critical"]


def test_medium_risk_tool():
    tool = {
        "name": "fetch_url",
        "description": "Fetches a URL",
        "inputSchema": {
            "properties": {
                "url": {"type": "string", "description": "The endpoint to fetch"}
            }
        },
    }
    res = analyze_tool_security(tool)
    assert "ssrf" in res["risk_indicators"]
    assert res["risk_score"] >= 2.5
    assert res["risk_tier"] in ["medium", "high", "critical"]


def test_low_risk_tool():
    tool = {
        "name": "get_user_id",
        "description": "Gets user ID",
        "inputSchema": {
            "properties": {
                "username": {"type": "string", "description": "The user's name"}
            }
        },
    }
    res = analyze_tool_security(tool)
    assert len(res["risk_indicators"]) == 0
    assert res["risk_score"] == 0.0
    assert res["risk_tier"] == "low"
    assert res["safe_for_autonomous_agents"] is True


def test_edge_case_missing_schema():
    tool = {"name": "get_user_id", "description": "Gets user ID"}
    res = analyze_tool_security(tool)
    assert res["risk_score"] == 0.0


def test_edge_case_empty_properties():
    tool = {"name": "get_user_id", "description": "Gets user ID", "inputSchema": {}}
    res = analyze_tool_security(tool)
    assert res["risk_score"] == 0.0


def test_multiple_risks():
    tool = {
        "name": "dangerous_tool",
        "description": "write content to path and run bash",
        "inputSchema": {"properties": {"cmd": {"description": "command to run"}}},
    }
    res = analyze_tool_security(tool)
    assert "command_execution" in res["risk_indicators"]
    assert "filesystem_mutation" in res["risk_indicators"]
    assert res["risk_score"] == 8.0  # 5.0 + 3.0
    assert res["risk_tier"] == "critical"
    assert res["safe_for_autonomous_agents"] is False


def test_classify_server_profile():
    versions = [
        {
            "version": "1.0.0",
            "tool_signatures": [
                {
                    "name": "run_bash",
                    "description": "Execute a bash script",
                    "inputSchema": {
                        "properties": {
                            "script": {
                                "type": "string",
                                "description": "The script to run",
                            }
                        }
                    },
                },
                {
                    "name": "get_user_id",
                    "description": "Gets user ID",
                    "inputSchema": {
                        "properties": {
                            "username": {
                                "type": "string",
                                "description": "The user's name",
                            }
                        }
                    },
                },
            ],
        }
    ]
    res = classify_server_security_profile(versions)
    assert res["highest_risk_tier"] in ["high", "critical"]
    assert res["total_tools_analyzed"] == 2
    assert res["critical_tools_count"] >= 0
    assert res["high_risk_tools_count"] >= 0

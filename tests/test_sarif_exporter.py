import pytest
from mcp_fingerprints.sarif_exporter import generate_sarif
from mcp_fingerprints.conflict_detector import ConflictAuditReport, ToolCollision

def test_generate_sarif_schema_structure():
    report = ConflictAuditReport(
        servers_configured=["s1"],
        servers_matched_in_passports=["s1"],
        total_tools_exposed=1,
        unique_tool_names=1,
        collisions=[
            ToolCollision(
                tool_name="execute_command",
                servers=["s1", "s2"],
                packages=["pkg1", "pkg2"],
                schema_identical=True,
                risk_tier="critical",
                risk_indicators=["command_execution"],
                divergence_details=None,
            )
        ],
        has_critical_conflicts=True,
        is_clean=False,
    )

    sarif = generate_sarif(report, config_path="my_config.json")
    
    # Assert structural keys
    assert "version" in sarif
    assert sarif["version"] == "2.1.0"
    assert "$schema" in sarif
    assert "runs" in sarif
    assert len(sarif["runs"]) == 1
    
    run = sarif["runs"][0]
    assert "tool" in run
    assert run["tool"]["driver"]["name"] == "mcp-fingerprints"
    
    # Check rules mapped from collision
    rules = run["tool"]["driver"]["rules"]
    assert len(rules) == 1
    assert rules[0]["id"] == "MCP-STRUCTURAL-COLLISION-CRITICAL"
    assert rules[0]["defaultConfiguration"]["level"] == "error"
    
    # Check result
    results = run["results"]
    assert len(results) == 1
    result = results[0]
    assert result["ruleId"] == "MCP-STRUCTURAL-COLLISION-CRITICAL"
    assert result["level"] == "error"
    assert "execute_command" in result["message"]["text"]
    assert "s1, s2" in result["message"]["text"]
    assert "pkg1, pkg2" in result["message"]["text"]
    assert "IDENTICAL" in result["message"]["text"]
    assert "command_execution" in result["message"]["text"]
    assert "my_config.json" in result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]

def test_generate_sarif_empty_results():
    report = ConflictAuditReport(
        servers_configured=["s1"],
        servers_matched_in_passports=["s1"],
        total_tools_exposed=1,
        unique_tool_names=1,
        collisions=[],
        has_critical_conflicts=False,
        is_clean=True,
    )

    sarif = generate_sarif(report)
    
    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) == 1
    assert len(sarif["runs"][0]["tool"]["driver"].get("rules", [])) == 0
    assert len(sarif["runs"][0]["results"]) == 0

def test_generate_sarif_divergent_collision():
    report = ConflictAuditReport(
        servers_configured=["s1"],
        servers_matched_in_passports=["s1"],
        total_tools_exposed=1,
        unique_tool_names=1,
        collisions=[
            ToolCollision(
                tool_name="read_file",
                servers=["s3", "s4"],
                packages=["pkg3", "pkg4"],
                schema_identical=False,
                risk_tier="low",
                risk_indicators=[],
                divergence_details="[s3] properties=['path'], required=['path']; [s4] properties=['filepath'], required=['filepath']",
            )
        ],
        has_critical_conflicts=False,
        is_clean=False,
    )

    sarif = generate_sarif(report)
    run = sarif["runs"][0]
    
    rules = run["tool"]["driver"]["rules"]
    assert len(rules) == 1
    assert rules[0]["id"] == "MCP-STRUCTURAL-COLLISION-LOW"
    assert rules[0]["defaultConfiguration"]["level"] == "warning"
    
    results = run["results"]
    assert len(results) == 1
    result = results[0]
    assert result["level"] == "warning"
    assert "DIVERGENT" in result["message"]["text"]
    assert "properties=['path']" in result["message"]["text"]

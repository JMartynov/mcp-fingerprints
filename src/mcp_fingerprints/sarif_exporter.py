from typing import Any
from mcp_fingerprints.conflict_detector import ConflictAuditReport


def generate_sarif(report: ConflictAuditReport, config_path: str = "mcp_client_config.json") -> dict[str, Any]:
    """
    Generate an OASIS SARIF v2.1.0 compliant JSON object from a ConflictAuditReport.
    Focuses purely on structural AST tool capability risk profiles (collisions, divergence, shadowing).
    """
    
    rules = []
    results = []
    rule_id_map = set()

    for i, collision in enumerate(report.collisions):
        # We define a rule ID based on the risk tier and the fact that it's a structural collision
        rule_id = f"MCP-STRUCTURAL-COLLISION-{collision.risk_tier.upper()}"
        
        if rule_id not in rule_id_map:
            rules.append({
                "id": rule_id,
                "name": "McpToolCollisionShadowing",
                "shortDescription": {
                    "text": f"MCP Tool Collision with {collision.risk_tier.upper()} risk"
                },
                "fullDescription": {
                    "text": f"Multiple MCP servers expose the same tool name, leading to potential tool shadowing or prompt injection hijacking. Risk tier: {collision.risk_tier.upper()}."
                },
                "defaultConfiguration": {
                    "level": "error" if collision.risk_tier in ("critical", "high") else "warning"
                },
                "help": {
                    "text": "Review duplicate tool names to ensure your LLM client routes calls to the intended backend. Prefix or rename tools to prevent conflicts."
                }
            })
            rule_id_map.add(rule_id)

        message_text = (
            f"Tool name collision detected for '{collision.tool_name}'. "
            f"Exposed by servers: {', '.join(collision.servers)} "
            f"({', '.join(collision.packages)}). "
            f"Schema Match: {'IDENTICAL' if collision.schema_identical else 'DIVERGENT'}."
        )
        if collision.risk_indicators:
            message_text += f" Risk Factors: {', '.join(collision.risk_indicators)}."
        if collision.divergence_details:
            message_text += f" Divergence: {collision.divergence_details}."

        level = "error" if collision.risk_tier in ("critical", "high") else "warning"

        results.append({
            "ruleId": rule_id,
            "level": level,
            "message": {
                "text": message_text
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": str(config_path)
                        },
                        "region": {
                            "startLine": 1,
                            "startColumn": 1
                        }
                    }
                }
            ]
        })

    sarif = {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "mcp-fingerprints",
                        "informationUri": "https://github.com/mcp-fingerprints/mcp-fingerprints",
                        "rules": rules
                    }
                },
                "results": results
            }
        ]
    }

    return sarif

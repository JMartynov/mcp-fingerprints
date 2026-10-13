import os
import pytest

TASK_FILES = [
    "task_24_resilient_network_ingestion.md",
    "task_25_semantic_embeddings_ci_sync.md",
    "task_26_interactive_setup_wizard.md",
    "task_27_native_config_exporters_zed_cline_windsurf.md",
    "task_28_web_catalog_pwa_virtualization.md",
    "task_29_isolated_container_runtime_sandbox.md",
    "task_30_sarif_export_code_scanning.md",
    "task_31_mcp_server_sbom_cyclonedx.md",
    "task_32_jsonrpc_protocol_conformance_validator.md",
]

REQUIRED_SECTIONS = [
    "1. Architectural Context & Technical Objective",
    "2. Technical Implementation Specifications",
    "3. Clear Acceptance Criteria",
    "4. Unit Test Plan",
    "5. Live Acceptance Test Plan",
]

def test_wave_8_task_files_exist_and_valid():
    for filename in TASK_FILES:
        filepath = os.path.join("docs", "tasks", filename)
        assert os.path.exists(filepath), f"{filename} does not exist"
        
        size = os.path.getsize(filepath)
        assert size > 500, f"{filename} is empty or too small ({size} bytes)"
        
        with open(filepath, "r") as f:
            content = f.read()
            for section in REQUIRED_SECTIONS:
                assert section in content, f"{filename} is missing section: {section}"

def test_roadmap_board_specifications_updated():
    roadmap_path = os.path.join("docs", "tasks", "roadmap_board_specifications.md")
    assert os.path.exists(roadmap_path), "roadmap_board_specifications.md does not exist"
    
    with open(roadmap_path, "r") as f:
        content = f.read()
        
        for task_num in range(24, 33):
            header = f"## {task_num}."
            assert header in content, f"Task {task_num} not found in roadmap"
            

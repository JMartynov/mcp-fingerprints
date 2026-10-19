import json
import logging
import os
from pathlib import Path
from mcp_fingerprints.models import ServerPackageSpec, VersionFingerprint, ToolContractSignature
from mcp_fingerprints.prober import ProbeReport
from mcp_fingerprints.canonicalizer import build_version_fingerprint

logger = logging.getLogger(__name__)

def generate_auto_passport(probe_report: ProbeReport, output_dir: Path, server_name: str | None = None) -> ServerPackageSpec | None:
    """Generate a passport from a live probe report if tools exist."""
    
    if not probe_report.tools_observed:
        logger.warning("No tools observed, skipping auto-passport generation.")
        return None
        
    if not server_name:
         if probe_report.match_result and probe_report.match_result.package_name:
              server_name = probe_report.match_result.package_name
         else:
              server_name = "unknown_server"

    # Some packages might have invalid slashes or @ for filenames
    safe_filename = server_name.replace("/", "_").replace("@", "")
    
    purl = f"pkg:unknown/{safe_filename}@1.0.0"
    
    # build_version_fingerprint expects raw dictionaries for tools, prompts, resources
    
    version_fingerprint = build_version_fingerprint(
        version="1.0.0",
        tools=probe_report.tools_observed,
        prompts=probe_report.prompts_observed,
        resources=probe_report.resources_observed
    )
    
    spec = ServerPackageSpec(
         purl=purl,
         ecosystem="unknown",
         package_name=server_name,
         versions=[version_fingerprint]
    )
    
    output_path = output_dir / f"{safe_filename}.json"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
         json.dump(spec.to_dict(), f, indent=2)
         
    logger.info(f"Auto-generated passport saved to {output_path}")
    return spec

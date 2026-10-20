import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest
from mcp_fingerprints import scan_local_configs
from mcp_fingerprints.config_scanner import NpmGlobalScanner

@pytest.fixture
def mock_filesystem(tmp_path):
    # Setup mock global npm directory
    npm_global_dir = tmp_path / "lib" / "node_modules"
    npm_global_dir.mkdir(parents=True)
    
    # Mock an MCP package
    mcp_pkg_dir = npm_global_dir / "my-mcp-server"
    mcp_pkg_dir.mkdir()
    with open(mcp_pkg_dir / "package.json", "w") as f:
        json.dump({
            "name": "my-mcp-server",
            "version": "1.0.0",
            "dependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0"
            },
            "bin": {
                "my-mcp": "./dist/index.js"
            }
        }, f)
        
    # Mock a scoped MCP package
    scoped_mcp_dir = npm_global_dir / "@myorg" / "mcp-tool"
    scoped_mcp_dir.mkdir(parents=True)
    with open(scoped_mcp_dir / "package.json", "w") as f:
        json.dump({
            "name": "@myorg/mcp-tool",
            "version": "2.0.0",
            "keywords": ["mcp-server"],
            "bin": {
                "org-mcp": "./index.js"
            }
        }, f)
        
    # Mock a non-MCP package
    non_mcp_dir = npm_global_dir / "just-a-lib"
    non_mcp_dir.mkdir()
    with open(non_mcp_dir / "package.json", "w") as f:
        json.dump({
            "name": "just-a-lib",
            "version": "3.0.0",
            "dependencies": {
                "express": "^4.17.1"
            }
        }, f)
        
    # Setup mock npx cache directory
    npx_cache_dir = tmp_path / ".npm" / "_npx"
    npx_cache_dir.mkdir(parents=True)
    
    hash_dir = npx_cache_dir / "c67a"
    hash_dir.mkdir()
    npx_nm_dir = hash_dir / "node_modules"
    npx_nm_dir.mkdir()
    
    npx_mcp_dir = npx_nm_dir / "cached-mcp"
    npx_mcp_dir.mkdir()
    with open(npx_mcp_dir / "package.json", "w") as f:
        json.dump({
            "name": "cached-mcp",
            "version": "4.0.0",
            "devDependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0"
            }
        }, f)

    return tmp_path

def test_npm_global_scanner(mock_filesystem):
    scanner = NpmGlobalScanner()
    
    with mock.patch("subprocess.run") as mock_run:
        # Mock `npm root -g` to return our mock global dir
        mock_run.return_value.stdout = str(mock_filesystem / "lib" / "node_modules")
        
        # Test scan_global_npm
        global_servers = scanner.scan_global_npm()
        assert len(global_servers) == 2
        
        names = [s["name"] for s in global_servers]
        assert "my-mcp-server" in names
        assert "@myorg/mcp-tool" in names
        assert "just-a-lib" not in names
        
        for s in global_servers:
            if s["name"] == "my-mcp-server":
                assert s["command"] == "my-mcp"
                assert s["client"] == "npm-global"
                assert s["version"] == "1.0.0"
            elif s["name"] == "@myorg/mcp-tool":
                assert s["command"] == "org-mcp"
                assert s["client"] == "npm-global"
                assert s["version"] == "2.0.0"
                
    with mock.patch("sys.platform", "linux"), mock.patch("pathlib.Path.home", return_value=mock_filesystem):
        # Test scan_npx_cache
        npx_servers = scanner.scan_npx_cache()
        assert len(npx_servers) == 1
        
        s = npx_servers[0]
        assert s["name"] == "cached-mcp"
        assert s["client"] == "npx-cache"
        assert s["command"] == "npx"
        assert s["args"] == ["-y", "cached-mcp"]
        assert s["version"] == "4.0.0"
        
    with mock.patch("subprocess.run") as mock_run, mock.patch("sys.platform", "linux"), mock.patch("pathlib.Path.home", return_value=mock_filesystem):
        mock_run.return_value.stdout = str(mock_filesystem / "lib" / "node_modules")
        
        # Test scan_all
        all_servers = scanner.scan_all()
        assert len(all_servers) == 3

def test_scan_local_configs_integration(mock_filesystem):
    with mock.patch("subprocess.run") as mock_run, \
         mock.patch("sys.platform", "linux"), \
         mock.patch("pathlib.Path.home", return_value=mock_filesystem), \
         mock.patch("mcp_fingerprints.config_scanner.ClientConfigLocator.get_standard_paths", return_value=[]), \
         mock.patch("mcp_fingerprints.config_scanner.McpStdioProber.probe_stdio") as mock_probe:
         
        mock_run.return_value.stdout = str(mock_filesystem / "lib" / "node_modules")
        
        # Mock probe to avoid actually running anything
        mock_probe.return_value.to_dict.return_value = {"connection_successful": True}
        
        report = scan_local_configs(probe_live=False, scan_global=True)
        assert len(report.servers) == 3
        
        names = [s["name"] for s in report.servers]
        assert "my-mcp-server" in names
        assert "@myorg/mcp-tool" in names
        assert "cached-mcp" in names
        
        
        # Test matches against passports database
        from mcp_fingerprints.matcher import FingerprintMatcher
        matcher = FingerprintMatcher()
        # Create a mock passport in memory to match against
        from mcp_fingerprints.models import ServerPackageSpec
        passport = ServerPackageSpec(
                        package_name="my-mcp-server",
            purl="pkg:npm/my-mcp-server",
            ecosystem="npm",
                        
            versions=[]
        )
        matcher.register_package(passport)
        
        matches = matcher.match(tools=[{"name": "my-tool"}])
        assert matches.matched is False


        report_no_global = scan_local_configs(probe_live=False, scan_global=False)
        assert len(report_no_global.servers) == 0


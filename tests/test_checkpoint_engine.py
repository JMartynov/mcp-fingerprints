import json
from unittest.mock import patch

import pytest

from mcp_fingerprints.synchronizer import PassportSynchronizer


@pytest.fixture
def sync_env(tmp_path):
    output_dir = tmp_path / "fingerprints"
    output_dir.mkdir()
    
    # Create some dummy files
    for i in range(5):
        (output_dir / f"pkg_{i}.json").write_text(json.dumps({
            "package_name": f"pkg_{i}",
            "ecosystem": "npm",
            "purl": f"pkg:npm/pkg_{i}",
            "versions": [{"version": "1.0", "tool_signatures": []}],
            "sources_merged": ["npm_registry"]
        }))
    
    return output_dir

def test_checkpoint_init_and_clear(sync_env):
    # Test init doesn't load a non-existent checkpoint
    sync = PassportSynchronizer(output_dir=sync_env)
    assert not sync.checkpoint_data.get("checkpoint_active")
    
    # Test _save_checkpoint
    sync._save_checkpoint(stage="stage_update_existing", cursor="pkg_2.json")
    assert sync.checkpoint_file.exists()
    
    data = json.loads(sync.checkpoint_file.read_text())
    assert data["current_stage"] == "stage_update_existing"
    assert data["cursor"] == "pkg_2.json"
    
    # Test clear_checkpoint
    sync._clear_checkpoint()
    assert not sync.checkpoint_file.exists()
    assert not sync.checkpoint_data.get("checkpoint_active")

def test_time_budget_exhaustion(sync_env):
    # Set a tiny budget to force exhaustion immediately
    sync = PassportSynchronizer(output_dir=sync_env, time_budget=0) 
    # mock start time to be very old
    sync.start_time = 0
    sync.time_budget = 10
    
    with pytest.raises(SystemExit) as excinfo:
        sync._check_budget("stage_update_existing", cursor="pkg_3.json")
        
    assert excinfo.value.code == 0
    
    # Check that it saved the checkpoint
    assert sync.checkpoint_file.exists()
    data = json.loads(sync.checkpoint_file.read_text())
    assert data["current_stage"] == "stage_update_existing"
    assert data["cursor"] == "pkg_3.json"
    assert data["reason"] == "time_budget_reached"

def test_resume_from_checkpoint(sync_env):
    # Create a checkpoint
    ckpt_file = sync_env.parent / ".sync_checkpoint.json"
    ckpt_file.write_text(json.dumps({
        "checkpoint_active": True,
        "current_stage": "stage_update_existing",
        "substage": None,
        "page": None,
        "cursor": "pkg_3.json",
        "completed_stages": [],
        "timestamp": "2023-01-01",
        "reason": "time_budget_reached"
    }))
    
    # Let's just monkeypatch the instance instead
    sync = PassportSynchronizer(output_dir=sync_env)
    sync.checkpoint_file = ckpt_file
    sync.checkpoint_data = sync._load_checkpoint(False)
    
    assert sync.checkpoint_data["cursor"] == "pkg_3.json"
    
    # Run update existing with mock to see what gets processed
    processed = []
        
    # We need to mock _check_budget to not actually check time, and fetch_json to do nothing
    with patch.object(sync, '_check_budget') as mock_check, \
         patch('mcp_fingerprints.synchronizer.fetch_json', return_value=({}, None)), \
         patch.object(sync, 'merge_and_enrich_passport', return_value=None):
         
         # Track which files _check_budget was called with
         def side_effect(stage, substage=None, page=None, cursor=None, **kwargs):
             if cursor:
                 processed.append(cursor)
             return False
             
         mock_check.side_effect = side_effect
         
         sync.update_existing_passports()
         
         # Should have skipped 0, 1, 2, and 3 itself and started from 4 
         # because the logic is `skip = bool(start_cursor)` and then `if j_file.name == start_cursor: skip = False; continue`
         assert "pkg_0.json" not in processed
         assert "pkg_1.json" not in processed
         assert "pkg_2.json" not in processed
         assert "pkg_3.json" not in processed
         assert "pkg_4.json" in processed

def test_run_sync_pipeline_skips_completed(sync_env):
    sync = PassportSynchronizer(output_dir=sync_env)
    
    # Set some completed stages
    sync.checkpoint_data["completed_stages"] = ["stage_update_existing", "stage_enrich_ast"]
    
    with patch.object(sync, 'update_existing_passports') as mock_update, \
         patch.object(sync, 'enrich_zero_tool_passports') as mock_enrich, \
         patch.object(sync, 'discover_new_mcps') as mock_discover:
         
         sync.run_sync_pipeline(update_existing=True, enrich_ast=True, discover_new=True)
         
         # Update and enrich should be skipped
         mock_update.assert_not_called()
         mock_enrich.assert_not_called()
         # Discover should be called
         mock_discover.assert_called_once()
         
         # And checkpoint should be cleared at the end
         assert not sync.checkpoint_file.exists()


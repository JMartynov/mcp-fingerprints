import os
import pytest

def test_audit_pillar1_report_exists():
    assert os.path.exists('docs/reports/audit_pillar1_500_source_truth.md')

def test_audit_pillar1_script_exists():
    assert os.path.exists('scripts/audit_500_source_truth.py')

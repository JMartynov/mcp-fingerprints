# Daily Web Card Quality Audits

This directory contains automated daily reports and remediations produced by the scheduled inspection agent defined in [task_82_daily_web_cards_and_updates_audit_scenario.md](../../tasks/task_82_daily_web_cards_and_updates_audit_scenario.md).

## Directory Structure
- [master_audit_summary.md](master_audit_summary.md): Consolidated historical ledger across all daily inspection runs.
- `runs/`: Timestamped daily inspection markdown reports (`runs/YYYY-MM-DD_HHMMSS.md`).
- `reviews/`: In-depth analysis and verification reports reviewing specific daily audit runs (`reviews/pr_XX_verification_report.md`).
- `plans/`: Remediation action plans formulated to resolve identified audit gaps (`plans/remediation_plan_*.md`).
- `fixes/`: Detailed post-fix summary reports referencing modified source files and verification results (`fixes/YYYY-MM-DD_*_remediation_fix_report.md`).

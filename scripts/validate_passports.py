import sys
from pathlib import Path

def validate_passports(data_dir: str = "data/fingerprints") -> int:
    try:
        from mcp_fingerprints.schema_validator import PassportSchemaValidator
    except ImportError:
        # Fallback if src is not in sys.path
        src_path = Path(__file__).resolve().parent.parent / "src"
        if src_path.exists() and str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        from mcp_fingerprints.schema_validator import PassportSchemaValidator

    dir_path = Path(data_dir)
    if not dir_path.exists():
        print(f"ERROR: Data directory '{data_dir}' does not exist.")
        return 1

    valid, invalid, errors = PassportSchemaValidator.validate_directory(dir_path)
    if invalid > 0 or errors:
        print(f"Validation FAILED: {invalid} invalid passports detected ({valid} valid).")
        for err in errors[:20]:
            print(f"  - {err}")
        if len(errors) > 20:
            print(f"  ... and {len(errors) - 20} more errors.")
        return 1

    print(f"Validation SUCCESS: All {valid} passports are valid and conform to schema invariants.")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/fingerprints"
    sys.exit(validate_passports(target))

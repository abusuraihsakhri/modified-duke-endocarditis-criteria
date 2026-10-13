#!/usr/bin/env python3
"""2023 Duke-ISCVID infective endocarditis clinical-criteria classifier.

Criteria must be assessed by a qualified clinician. This module only combines
already-adjudicated categorical findings; it does not interpret raw tests.
Reference: Fowler et al., Clin Infect Dis 2023;77:518-526.
https://doi.org/10.1093/cid/ciad271
"""

import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any, Dict

VERSION = "2023 Duke-ISCVID"
MAJOR = ("major_microbiologic", "major_imaging", "major_surgical")
MINOR = ("minor_predisposition", "minor_fever", "minor_vascular",
         "minor_immunologic", "minor_microbiologic", "minor_imaging",
         "minor_physical")
OTHER = ("definite_pathologic", "reject_alternative", "reject_short_therapy",
         "reject_negative_surgery")
FIELDS = OTHER + MAJOR + MINOR
REJECTIONS = ("reject_alternative", "reject_short_therapy", "reject_negative_surgery")


def _boolean(value: Any, field: str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "yes", "1"):
            return True
        if normalized in ("false", "no", "0"):
            return False
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    raise ValueError(f"{field} must be a boolean (true/false, yes/no, or 1/0)")


def calculate_metrics(**kwargs: Any) -> Dict[str, Any]:
    """Classify an adjudicated case under the 2023 Duke-ISCVID rules.

    All 14 flags are required to avoid treating unreviewed criteria as absent.
    Exactly one checkbox per criterion domain contributes at most one point.
    """
    missing = [field for field in FIELDS if field not in kwargs]
    extra = sorted(set(kwargs) - set(FIELDS))
    if missing or extra:
        raise ValueError(f"Invalid criteria fields; missing={missing}, unknown={extra}")
    selected = {field: _boolean(kwargs[field], field) for field in FIELDS}
    if selected["major_microbiologic"] and selected["minor_microbiologic"]:
        raise ValueError("The same microbiologic evidence cannot count as both major and minor")
    if selected["major_imaging"] and selected["minor_imaging"]:
        raise ValueError("Imaging evidence cannot be counted as both major and minor")
    if selected["major_surgical"] and selected["major_imaging"]:
        raise ValueError("Surgical major criterion applies only if major imaging is unavailable")
    if selected["major_surgical"] and selected["definite_pathologic"]:
        raise ValueError("Surgical major criterion requires absence of pathologic confirmation")
    if selected["definite_pathologic"] and any(selected[r] for r in REJECTIONS):
        raise ValueError("Pathologically definite IE conflicts with a rejection criterion")

    major_count = sum(selected[field] for field in MAJOR)
    minor_count = sum(selected[field] for field in MINOR)
    rejected_reason = next((r for r in REJECTIONS if selected[r]), None)
    if rejected_reason:
        classification = "Rejected"
        basis = rejected_reason
    elif selected["definite_pathologic"]:
        classification = "Definite"
        basis = "pathologic criterion"
    elif major_count >= 2:
        classification = "Definite"
        basis = "at least 2 major criteria"
    elif major_count >= 1 and minor_count >= 3:
        classification = "Definite"
        basis = "at least 1 major and 3 minor criteria"
    elif minor_count >= 5:
        classification = "Definite"
        basis = "at least 5 minor criteria"
    elif major_count >= 1 and minor_count >= 1:
        classification = "Possible"
        basis = "at least 1 major and 1 minor criterion"
    elif minor_count >= 3:
        classification = "Possible"
        basis = "at least 3 minor criteria"
    else:
        classification = "Rejected"
        basis = "does not meet criteria for possible IE"
    return {
        "criteria_version": VERSION,
        "classification": classification,
        "basis": basis,
        "major_count": major_count,
        "minor_count": minor_count,
        "note": "Criteria classification only; incomplete evaluation must not be used to rule out IE.",
    }


def _safe_resolve_path(path_str: str) -> Path:
    """Constrain CLI file operations to CWD or a configured system temp dir."""
    path = Path(path_str).resolve()
    roots = [Path.cwd().resolve(), Path(os.getenv("TMPDIR") or os.getenv("TEMP") or "/tmp").resolve()]
    if not any(path.is_relative_to(root) for root in roots):
        raise ValueError(f"Access denied: path '{path}' is outside the allowed directory")
    return path


def _csv_safe(value: str) -> str:
    """Prevent spreadsheet formula execution in exported free-text fields."""
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def process_batch(input_csv: str, output_csv: str) -> int:
    source = _safe_resolve_path(input_csv)
    destination = _safe_resolve_path(output_csv)
    if source == destination:
        raise ValueError("Input and output files must differ")
    if not source.exists():
        raise FileNotFoundError(f"Input CSV does not exist: {source}")
    if not source.is_file():
        raise ValueError(f"Input path is not a file: {source}")
    if source.stat().st_size > 5_000_000:
        raise ValueError("CSV exceeds the 5 MB size limit")
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError("Duplicate CSV headers")
        missing = [field for field in FIELDS if field not in headers]
        if missing:
            raise ValueError(f"Missing CSV columns: {', '.join(missing)}")
        if any(h in headers for h in ("classification", "basis", "major_count", "minor_count", "criteria_version", "note")):
            raise ValueError("CSV contains reserved output columns")
        rows = []
        for line, record in enumerate(reader, 2):
            if line > 10001:
                raise ValueError("CSV exceeds the 10,000-row limit")
            if None in record or any(val is None for val in record.values()):
                raise ValueError(f"Malformed CSV at row {line}")
            try:
                result = calculate_metrics(**{f: record[f] for f in FIELDS})
            except ValueError as exc:
                raise ValueError(f"Row {line}: {exc}") from exc
            rows.append({**{k: _csv_safe(v) for k, v in record.items()}, **result})
    with destination.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers + ["criteria_version", "classification", "basis", "major_count", "minor_count", "note"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="2023 Duke-ISCVID criteria classifier (not diagnostic advice)")
    sub = parser.add_subparsers(dest="command", required=True)
    single = sub.add_parser("single", help="Evaluate a case after reviewing all criterion domains")
    for field in FIELDS:
        single.add_argument("--" + field.replace("_", "-"), action="store_true", help=field.replace("_", " "))
    batch = sub.add_parser("batch", help="Classify CSV cases with all 14 boolean criterion columns")
    batch.add_argument("-i", "--input", required=True)
    batch.add_argument("-o", "--output", default="results.csv")
    args = parser.parse_args(argv)
    if args.command == "single":
        print(json.dumps(calculate_metrics(**{f: getattr(args, f) for f in FIELDS}), indent=2))
    else:
        print(f"Processed {process_batch(args.input, args.output)} records -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

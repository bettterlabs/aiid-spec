#!/usr/bin/env python3
"""
aiid_validator.py — Reference validator for the .aiID Core Profile Format v1.0

Usage:
    python aiid_validator.py file.aiid
    python aiid_validator.py file.aiid --strict
    python aiid_validator.py file.aiid --tier    # also checks compliance tier
    python aiid_validator.py --test              # run against built-in test vectors

Requires:
    pip install pyyaml jsonschema

Exit codes:
    0 = valid
    1 = invalid (errors found)
    2 = usage error
"""

import sys
import json
import re
import argparse
from pathlib import Path
from collections import Counter

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# ---------------------------------------------------------------------------
# Duplicate key detection
# ---------------------------------------------------------------------------

class DuplicateKeyError(Exception):
    pass


def _check_duplicates(loader, node, deep=False):
    """YAML constructor that rejects duplicate keys at any mapping level."""
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise DuplicateKeyError(
                f"Duplicate key '{key}' at line {key_node.start_mark.line + 1}"
            )
        value = loader.construct_object(value_node, deep=deep)
        mapping[key] = value
    return mapping


class SafeNoDuplicateLoader(yaml.SafeLoader):
    pass


SafeNoDuplicateLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _check_duplicates
)


# ---------------------------------------------------------------------------
# Core validation (no jsonschema dependency)
# ---------------------------------------------------------------------------

# Valid OCEAN pattern: 5 integers 0-100 separated by /
OCEAN_RE = re.compile(
    r'^(100|[1-9]?\d)/(100|[1-9]?\d)/(100|[1-9]?\d)/(100|[1-9]?\d)/(100|[1-9]?\d)$'
)

# Valid HEXACO pattern: 6 integers 0-100 separated by /
HEXACO_RE = re.compile(
    r'^(100|[1-9]?\d)/(100|[1-9]?\d)/(100|[1-9]?\d)/(100|[1-9]?\d)/(100|[1-9]?\d)/(100|[1-9]?\d)$'
)

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

ATTACHMENT_VALUES = {
    'secure', 'anxious_preoccupied', 'dismissive_avoidant',
    'fearful_avoidant', 'earned_secure'
}

AIID_VERSIONS = {'1.0'}

# Fields that accept string or list
STRING_OR_LIST_FIELDS = {
    'role', 'style', 'tone', 'format_pref', 'thinking', 'learning',
    'deciding', 'epistemic', 'strengths', 'ai_instructions'
}

# Fields that must be arrays
ARRAY_FIELDS = {
    'avoid', 'VIA_top5', 'VIA_bottom3', 'core', 'priorities',
    'boundaries', 'goals_short', 'goals_long', 'archetypes',
    'patterns_to_watch'
}

# Fields that must be strings
STRING_FIELDS = {
    'aiid_version', 'profile_version', 'updated', 'name', 'display_name',
    'location', 'dob', 'pronouns', 'OCEAN', 'HEXACO', 'attachment',
    'attachment_note', 'humor', 'stop_rule', 'neurodivergence',
    'ethics', 'narrative'
}

# Fields that must be maps
MAP_FIELDS = {'OCEAN_detail'}

# All known core fields
KNOWN_FIELDS = (
    STRING_FIELDS | ARRAY_FIELDS | STRING_OR_LIST_FIELDS | MAP_FIELDS
)

# Sensitivity classifications
SENSITIVE_FIELDS = {
    'dob', 'neurodivergence', 'attachment', 'attachment_note',
    'patterns_to_watch', 'narrative', 'boundaries'
}

PERSONAL_FIELDS = {'name', 'display_name', 'location', 'pronouns'}


class ValidationResult:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []
        self.tier = None

    @property
    def valid(self):
        return len(self.errors) == 0

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def add_info(self, msg):
        self.info.append(msg)

    def report(self):
        lines = []
        if self.valid:
            lines.append("✓ VALID")
        else:
            lines.append("✗ INVALID")

        if self.tier:
            lines.append(f"  Compliance tier: {self.tier}")

        for e in self.errors:
            lines.append(f"  ERROR: {e}")
        for w in self.warnings:
            lines.append(f"  WARNING: {w}")
        for i in self.info:
            lines.append(f"  INFO: {i}")
        return "\n".join(lines)


def validate_aiid(data, strict=False, check_tier=False):
    """Validate a parsed YAML data structure against .aiid v1.0 rules.

    Args:
        data: Parsed YAML (dict)
        strict: If True, unknown non-x_ fields are errors (not warnings)
        check_tier: If True, determine compliance tier

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    # Must be a mapping
    if not isinstance(data, dict):
        result.error("Root element must be a YAML mapping (dict), got " + type(data).__name__)
        return result

    # Required: aiid_version
    if 'aiid_version' not in data:
        result.error("Missing required field: aiid_version")
    elif data['aiid_version'] not in AIID_VERSIONS:
        result.error(f"Unrecognized aiid_version: '{data['aiid_version']}'. Known versions: {AIID_VERSIONS}")

    # Required: at least one identifier
    has_name = 'name' in data and isinstance(data.get('name'), str) and len(data['name'].strip()) > 0
    has_display = 'display_name' in data and isinstance(data.get('display_name'), str) and len(data['display_name'].strip()) > 0
    if not has_name and not has_display:
        result.error("Missing required subject identifier: must include 'name' or 'display_name' (non-empty string)")

    # Type checks for known fields
    for field in data:
        if field.startswith('x_'):
            continue  # extensions are always valid

        if field not in KNOWN_FIELDS:
            msg = f"Unknown field '{field}' (not in core spec, not x_-prefixed)"
            if strict:
                result.error(msg)
            else:
                result.warn(msg + " — may be from a newer spec version")
            continue

        value = data[field]

        if field in STRING_FIELDS:
            if not isinstance(value, str):
                result.error(f"Field '{field}' must be a string, got {type(value).__name__}")
            elif field in ('name', 'display_name') and len(value.strip()) == 0:
                result.error(f"Field '{field}' must be non-empty")

        elif field in ARRAY_FIELDS:
            if not isinstance(value, list):
                result.error(f"Field '{field}' must be an array/list, got {type(value).__name__}")
            elif len(value) == 0:
                result.warn(f"Field '{field}' is an empty array")
            else:
                for i, item in enumerate(value):
                    if not isinstance(item, str) or len(item.strip()) == 0:
                        result.error(f"Field '{field}[{i}]' must be a non-empty string")

        elif field in STRING_OR_LIST_FIELDS:
            if isinstance(value, str):
                if len(value.strip()) == 0:
                    result.error(f"Field '{field}' must be non-empty")
            elif isinstance(value, list):
                if len(value) == 0:
                    result.warn(f"Field '{field}' is an empty array")
                for i, item in enumerate(value):
                    if not isinstance(item, str) or len(item.strip()) == 0:
                        result.error(f"Field '{field}[{i}]' must be a non-empty string")
            else:
                result.error(f"Field '{field}' must be a string or array, got {type(value).__name__}")

        elif field in MAP_FIELDS:
            if not isinstance(value, dict):
                result.error(f"Field '{field}' must be a mapping/dict, got {type(value).__name__}")

    # OCEAN format check
    if 'OCEAN' in data and isinstance(data.get('OCEAN'), str):
        if not OCEAN_RE.match(data['OCEAN']):
            result.error(
                f"OCEAN format invalid: '{data['OCEAN']}'. "
                "Must be five integers (0-100) separated by /. Example: 91/82/78/78/39"
            )

    # HEXACO format check
    if 'HEXACO' in data and isinstance(data.get('HEXACO'), str):
        if not HEXACO_RE.match(data['HEXACO']):
            result.error(
                f"HEXACO format invalid: '{data['HEXACO']}'. "
                "Must be six integers (0-100) separated by /. Example: 78/45/82/65/70/91"
            )

    # Date format checks
    for date_field in ('updated', 'dob'):
        if date_field in data and isinstance(data.get(date_field), str):
            if not DATE_RE.match(data[date_field]):
                result.error(f"Field '{date_field}' must be YYYY-MM-DD format, got '{data[date_field]}'")

    # Attachment enum check
    if 'attachment' in data and isinstance(data.get('attachment'), str):
        if data['attachment'] not in ATTACHMENT_VALUES:
            result.error(
                f"Invalid attachment value: '{data['attachment']}'. "
                f"Must be one of: {sorted(ATTACHMENT_VALUES)}"
            )

    # VIA_top5 max items
    if 'VIA_top5' in data and isinstance(data.get('VIA_top5'), list):
        if len(data['VIA_top5']) > 5:
            result.error(f"VIA_top5 must have at most 5 items, got {len(data['VIA_top5'])}")

    # VIA_bottom3 max items
    if 'VIA_bottom3' in data and isinstance(data.get('VIA_bottom3'), list):
        if len(data['VIA_bottom3']) > 3:
            result.error(f"VIA_bottom3 must have at most 3 items, got {len(data['VIA_bottom3'])}")

    # Sensitivity info
    sensitive_present = [f for f in SENSITIVE_FIELDS if f in data]
    if sensitive_present:
        result.add_info(f"Sensitive fields present: {sensitive_present}")

    # YAML coercion warnings
    if 'dob' in data and isinstance(data.get('dob'), (int, float)):
        result.warn("'dob' was parsed as a number — YAML date coercion likely occurred. Quote the value: dob: \"1988-07-14\"")
    if 'dob' in data and hasattr(data.get('dob'), 'isoformat'):
        result.warn("'dob' was parsed as a datetime object — YAML date coercion occurred. Quote the value: dob: \"1988-07-14\"")
    if 'updated' in data and hasattr(data.get('updated'), 'isoformat'):
        result.warn("'updated' was parsed as a datetime object — YAML date coercion occurred. Quote the value.")

    # Compliance tier check
    if check_tier:
        result.tier = _determine_tier(data)

    return result


def _determine_tier(data):
    """Determine the compliance tier of a valid .aiid file."""
    # Must have aiid_version and identifier to be any tier
    if 'aiid_version' not in data:
        return None
    if not ('name' in data or 'display_name' in data):
        return None

    # Level A: + at least one of style, tone, avoid, ai_instructions
    level_a_fields = {'style', 'tone', 'avoid', 'ai_instructions'}
    has_level_a = any(f in data for f in level_a_fields)
    if not has_level_a:
        return "Below Level A (no communication or instruction field)"

    # Level B: Level A + priorities or boundaries
    level_b_fields = {'priorities', 'boundaries'}
    has_level_b = any(f in data for f in level_b_fields)
    if not has_level_b:
        return "Level A (Minimal)"

    # Level C: Level B + core optional profile or extension
    core_profiles = {'OCEAN', 'HEXACO', 'OCEAN_detail', 'VIA_top5', 'VIA_bottom3', 'attachment'}
    has_profile = any(f in data for f in core_profiles)
    has_extension = any(k.startswith('x_') for k in data)
    if not has_profile and not has_extension:
        return "Level B (Actionable)"

    return "Level C (Extended)"


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------

def load_and_validate(filepath, strict=False, check_tier=False):
    """Load a .aiid file from disk, parse YAML, validate."""
    result = ValidationResult()
    path = Path(filepath)

    if not path.exists():
        result.error(f"File not found: {filepath}")
        return result

    raw = path.read_text(encoding='utf-8')

    # Parse with duplicate key detection
    try:
        data = yaml.load(raw, Loader=SafeNoDuplicateLoader)
    except DuplicateKeyError as e:
        result.error(f"YAML duplicate key: {e}")
        return result
    except yaml.YAMLError as e:
        result.error(f"YAML parse error: {e}")
        return result

    if data is None:
        result.error("File is empty or contains only comments")
        return result

    return validate_aiid(data, strict=strict, check_tier=check_tier)


# ---------------------------------------------------------------------------
# JSON Schema validation (optional, if jsonschema is installed)
# ---------------------------------------------------------------------------

def validate_with_schema(data, schema_path):
    """Validate against the JSON Schema. Requires jsonschema package."""
    if not HAS_JSONSCHEMA:
        return ["jsonschema package not installed — skipping schema validation"]

    schema = json.loads(Path(schema_path).read_text())
    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for error in validator.iter_errors(data):
        path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
        errors.append(f"Schema: {path}: {error.message}")
    return errors


# ---------------------------------------------------------------------------
# Built-in self-test
# ---------------------------------------------------------------------------

def run_self_test():
    """Run validation against built-in minimal test cases."""
    print("Running .aiid validator self-test...\n")

    valid_cases = [
        ("Minimal display_name", {"aiid_version": "1.0", "display_name": "Alex", "style": "direct"}),
        ("Minimal name", {"aiid_version": "1.0", "name": "Alex Rivera", "tone": "casual"}),
        ("With OCEAN", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "91/82/78/78/39", "style": "direct"}),
        ("With HEXACO", {"aiid_version": "1.0", "display_name": "X", "HEXACO": "78/45/82/65/70/91", "style": "direct"}),
        ("Pseudonymous", {"aiid_version": "1.0", "display_name": "nightowl", "avoid": ["hedging"]}),
        ("With extensions", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "x_astro": "Sun:Aqr Moon:Leo Asc:Cap"}),
        ("OCEAN boundary 0/100", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "0/100/0/100/0", "style": "direct"}),
        ("Both identifiers", {"aiid_version": "1.0", "name": "Full Name", "display_name": "Nick", "style": "direct"}),
    ]

    invalid_cases = [
        ("Missing aiid_version", {"name": "Bad", "style": "direct"}, "aiid_version"),
        ("Missing identifier", {"aiid_version": "1.0", "style": "direct"}, "identifier"),
        ("Bad OCEAN format", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "high/med/low/med/low"}, "OCEAN"),
        ("OCEAN 4 values", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "91/82/78/78"}, "OCEAN"),
        ("OCEAN > 100", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "91/82/78/78/150"}, "OCEAN"),
        ("Bad attachment", {"aiid_version": "1.0", "display_name": "X", "attachment": "complicated"}, "attachment"),
        ("Bad version", {"aiid_version": "2.0", "display_name": "X"}, "aiid_version"),
        ("avoid as string", {"aiid_version": "1.0", "display_name": "X", "avoid": "hedging"}, "avoid"),
        ("VIA_top5 too many", {"aiid_version": "1.0", "display_name": "X", "VIA_top5": ["a","b","c","d","e","f"]}, "VIA_top5"),
        ("Empty name", {"aiid_version": "1.0", "name": "", "style": "direct"}, "name"),
    ]

    passed = 0
    failed = 0

    for label, data in valid_cases:
        r = validate_aiid(data)
        status = "PASS" if r.valid else "FAIL"
        if r.valid:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] Valid case: {label}")
        if not r.valid:
            for e in r.errors:
                print(f"         ERROR: {e}")

    for label, data, expected_keyword in invalid_cases:
        r = validate_aiid(data)
        # Should be invalid
        if not r.valid:
            passed += 1
            print(f"  [PASS] Invalid case: {label}")
        else:
            failed += 1
            print(f"  [FAIL] Invalid case: {label} — expected errors but got none")

    print(f"\n{passed}/{passed + failed} tests passed.")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description=".aiID v1.0 Reference Validator",
        epilog="Exit code 0 = valid, 1 = invalid, 2 = usage error"
    )
    parser.add_argument("file", nargs="?", help="Path to .aiid file to validate")
    parser.add_argument("--strict", action="store_true",
                        help="Treat unknown non-x_ fields as errors")
    parser.add_argument("--tier", action="store_true",
                        help="Report compliance tier (A/B/C)")
    parser.add_argument("--schema", type=str, default=None,
                        help="Path to JSON Schema for additional validation")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()

    if args.test:
        success = run_self_test()
        sys.exit(0 if success else 1)

    if not args.file:
        parser.print_help()
        sys.exit(2)

    result = load_and_validate(args.file, strict=args.strict, check_tier=args.tier)

    # Optional schema validation
    if args.schema and result.valid:
        try:
            raw = Path(args.file).read_text(encoding='utf-8')
            data = yaml.safe_load(raw)
            schema_errors = validate_with_schema(data, args.schema)
            for se in schema_errors:
                result.error(se)
        except Exception as e:
            result.error(f"Schema validation failed: {e}")

    if args.json:
        output = {
            "valid": result.valid,
            "tier": result.tier,
            "errors": result.errors,
            "warnings": result.warnings,
            "info": result.info,
        }
        print(json.dumps(output, indent=2))
    else:
        print(result.report())

    sys.exit(0 if result.valid else 1)


if __name__ == "__main__":
    main()

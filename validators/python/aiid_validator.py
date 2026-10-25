#!/usr/bin/env python3
"""
aiid_validator.py — Reference validator for the .aiID Core Profile Format v1.0

Usage:
    python aiid_validator.py file.aiid
    python aiid_validator.py file.aiid --strict
    python aiid_validator.py file.aiid --tier       # also checks compliance tier
    python aiid_validator.py file.aiid --schema     # also runs the JSON Schema (needs jsonschema)
    python aiid_validator.py --test                 # run the built-in self-test

Requires:
    pip install pyyaml            (jsonschema is optional, for --schema)

YAML version note:
    PyYAML implements YAML 1.1. The .aiID spec requires YAML 1.2.2, so this
    validator installs the YAML 1.2 Core Schema resolvers on top of PyYAML:
    unquoted `yes`/`no`/`on`/`off` stay strings, unquoted dates stay strings,
    `<<` is a plain key (and rejected, since merge keys are prohibited).

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
# YAML 1.2 Core Schema loader (on top of PyYAML's 1.1 SafeLoader)
# ---------------------------------------------------------------------------

class DuplicateKeyError(Exception):
    pass


def _check_duplicates(loader, node, deep=False):
    """YAML constructor that rejects duplicate keys at any mapping level."""
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            seen = key in mapping
        except TypeError:
            raise yaml.constructor.ConstructorError(
                None, None, f"Keys must be plain strings (line {key_node.start_mark.line + 1})", key_node.start_mark)
        if seen:
            raise DuplicateKeyError(
                f"Duplicate key '{key}' at line {key_node.start_mark.line + 1}"
            )
        value = loader.construct_object(value_node, deep=deep)
        mapping[key] = value
    return mapping


class CoreSchemaLoader(yaml.SafeLoader):
    """SafeLoader with YAML 1.2 Core Schema implicit typing and duplicate-key rejection."""
    pass


# Drop PyYAML's YAML 1.1 implicit resolvers for bool, int, float, timestamp, merge and value,
# then add the YAML 1.2.2 Core Schema patterns (spec section 10.3.2).
_DROPPED_TAGS = {
    'tag:yaml.org,2002:bool', 'tag:yaml.org,2002:int', 'tag:yaml.org,2002:float',
    'tag:yaml.org,2002:timestamp', 'tag:yaml.org,2002:merge', 'tag:yaml.org,2002:value',
}
CoreSchemaLoader.yaml_implicit_resolvers = {
    ch: [(tag, rx) for (tag, rx) in lst if tag not in _DROPPED_TAGS]
    for ch, lst in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
CoreSchemaLoader.add_implicit_resolver(
    'tag:yaml.org,2002:bool',
    re.compile(r'^(?:true|True|TRUE|false|False|FALSE)$'),
    list('tTfF'))
CoreSchemaLoader.add_implicit_resolver(
    'tag:yaml.org,2002:int',
    re.compile(r'^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$'),
    list('-+0123456789'))
CoreSchemaLoader.add_implicit_resolver(
    'tag:yaml.org,2002:float',
    re.compile(r'^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?'
               r'|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$'),
    list('-+0123456789.'))


def _construct_int_12(loader, node):
    """YAML 1.2 Core Schema integers: base 10 by default, 0o octal, 0x hex. No leading-zero octal, no 1_000."""
    value = loader.construct_scalar(node)
    if value.startswith('0o'):
        return int(value[2:], 8)
    if value.startswith('0x'):
        return int(value[2:], 16)
    return int(value, 10)


CoreSchemaLoader.add_constructor('tag:yaml.org,2002:int', _construct_int_12)
CoreSchemaLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _check_duplicates
)

# Kept under its old name for callers of the 0.9 validator.
SafeNoDuplicateLoader = CoreSchemaLoader


def scan_prohibited_syntax(raw):
    """Return a list of errors for anchors, aliases and explicit tags (spec section 3.3)."""
    errors = []
    try:
        for tok in yaml.scan(raw):
            line = tok.start_mark.line + 1
            if isinstance(tok, yaml.AnchorToken):
                errors.append(f"Anchor '&{tok.value}' at line {line}: anchors are prohibited")
            elif isinstance(tok, yaml.AliasToken):
                errors.append(f"Alias '*{tok.value}' at line {line}: aliases are prohibited")
            elif isinstance(tok, yaml.TagToken):
                handle, suffix = tok.value
                errors.append(f"Explicit tag '{(handle or '')}{suffix}' at line {line}: explicit tags are prohibited")
    except yaml.YAMLError:
        pass  # the parse step reports syntax errors
    return errors


# ---------------------------------------------------------------------------
# Core validation (no jsonschema dependency)
# ---------------------------------------------------------------------------

MAX_FILE_BYTES = 16384  # spec section 3.6

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
    'aiid_version', 'updated', 'name', 'display_name',
    'location', 'dob', 'pronouns', 'OCEAN', 'HEXACO', 'attachment',
    'attachment_note', 'humor', 'stop_rule', 'neurodivergence',
    'ethics', 'narrative'
}

# Fields that accept a string or an integer
STRING_OR_INT_FIELDS = {'profile_version'}

# Fields that must be maps
MAP_FIELDS = {'OCEAN_detail'}

# All known core fields
KNOWN_FIELDS = (
    STRING_FIELDS | ARRAY_FIELDS | STRING_OR_LIST_FIELDS | STRING_OR_INT_FIELDS | MAP_FIELDS
)

# Length caps (characters), matching schema/aiid.schema.json
MAX_LEN = {
    'name': 120, 'display_name': 120, 'location': 200, 'pronouns': 60,
    'attachment_note': 1000, 'humor': 300, 'stop_rule': 300,
    'neurodivergence': 300, 'ethics': 300, 'narrative': 2000,
}
AI_INSTRUCTIONS_MAX = 2000      # as a single string
AI_INSTRUCTIONS_ITEM_MAX = 500  # each list item
AI_INSTRUCTIONS_MAX_ITEMS = 40
STRING_OR_LIST_STRING_MAX = 500
LIST_ITEM_MAX = 300

# Sensitivity classifications (spec section 8.2)
SENSITIVE_FIELDS = {
    'dob', 'neurodivergence', 'attachment', 'attachment_note',
    'patterns_to_watch', 'narrative', 'boundaries'
}

PERSONAL_FIELDS = {
    'name', 'display_name', 'location', 'pronouns',
    'OCEAN', 'OCEAN_detail', 'HEXACO', 'VIA_top5', 'VIA_bottom3'
}


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


def _is_blank(value):
    return value is None or (isinstance(value, str) and len(value.strip()) == 0)


REQUIRED_FIELDS = {'aiid_version', 'name', 'display_name'}


def strip_blank_fields(data, result):
    """Drop fields left blank (`tone:` with nothing after it) and blank list items (`- ` with nothing after it).
    Each one is a warning, not an error. A list that ends up empty counts as blank."""
    cleaned = {}
    for field, value in data.items():
        if isinstance(value, list):
            kept = [item for item in value if not _is_blank(item)]
            if len(kept) < len(value):
                result.warn(f"Field '{field}' has {len(value) - len(kept)} blank item(s); they were ignored")
            value = kept if kept else None
        if _is_blank(value):
            if field in REQUIRED_FIELDS:
                result.warn(f"Field '{field}' is blank; a value is required")
            else:
                result.warn(f"Field '{field}' is blank and was ignored (fill it in or delete the line)")
            continue
        cleaned[field] = value
    return cleaned


def _find_merge_keys(obj, path=''):
    """Return the paths of every `<<` key at any depth (merge keys are prohibited, spec 3.3)."""
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else str(k)
            if k == '<<':
                hits.append(here)
            hits.extend(_find_merge_keys(v, here))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(_find_merge_keys(v, f"{path}[{i}]"))
    return hits


def _check_len(result, label, value, cap):
    if isinstance(value, str) and len(value) > cap:
        result.error(f"Field '{label}' is {len(value)} characters; the limit is {cap}")


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

    # Keys must be plain strings
    bad_keys = [k for k in data if not isinstance(k, str)]
    if bad_keys:
        result.error(f"Keys must be plain strings, got {', '.join(repr(k) for k in bad_keys)}")
        return result

    # Merge keys are prohibited at any level (spec 3.3); under the 1.2 loader `<<` arrives as a plain key
    for where in _find_merge_keys(data):
        result.error(f"Merge key '<<' at '{where}' is prohibited")

    data = strip_blank_fields(data, result)

    # Required: aiid_version
    if 'aiid_version' not in data:
        result.error("Missing required field: aiid_version")
    elif data['aiid_version'] not in AIID_VERSIONS:
        result.error(f"Unrecognized aiid_version: '{data['aiid_version']}'. Known versions: {sorted(AIID_VERSIONS)}")

    # Required: at least one identifier
    has_name = isinstance(data.get('name'), str) and len(data['name'].strip()) > 0
    has_display = isinstance(data.get('display_name'), str) and len(data['display_name'].strip()) > 0
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
            elif field in MAX_LEN:
                _check_len(result, field, value, MAX_LEN[field])

        elif field in STRING_OR_INT_FIELDS:
            is_int = (isinstance(value, int) and not isinstance(value, bool)) or (isinstance(value, float) and value.is_integer())
            if not (isinstance(value, str) or is_int):
                result.error(f"Field '{field}' must be a string or an integer, got {type(value).__name__}")

        elif field in ARRAY_FIELDS:
            if not isinstance(value, list):
                result.error(f"Field '{field}' must be an array/list, got {type(value).__name__}")
            elif len(value) == 0:
                result.warn(f"Field '{field}' is an empty array")
            else:
                for i, item in enumerate(value):
                    if not isinstance(item, str) or len(item.strip()) == 0:
                        result.error(f"Field '{field}[{i}]' must be a non-empty string")
                    else:
                        _check_len(result, f"{field}[{i}]", item, LIST_ITEM_MAX)

        elif field in STRING_OR_LIST_FIELDS:
            str_cap = AI_INSTRUCTIONS_MAX if field == 'ai_instructions' else STRING_OR_LIST_STRING_MAX
            item_cap = AI_INSTRUCTIONS_ITEM_MAX if field == 'ai_instructions' else LIST_ITEM_MAX
            if isinstance(value, str):
                if len(value.strip()) == 0:
                    result.error(f"Field '{field}' must be non-empty")
                else:
                    _check_len(result, field, value, str_cap)
            elif isinstance(value, list):
                if len(value) == 0:
                    result.warn(f"Field '{field}' is an empty array")
                if field == 'ai_instructions' and len(value) > AI_INSTRUCTIONS_MAX_ITEMS:
                    result.error(f"Field 'ai_instructions' has {len(value)} items; the limit is {AI_INSTRUCTIONS_MAX_ITEMS}")
                for i, item in enumerate(value):
                    if not isinstance(item, str) or len(item.strip()) == 0:
                        result.error(f"Field '{field}[{i}]' must be a non-empty string")
                    else:
                        _check_len(result, f"{field}[{i}]", item, item_cap)
            else:
                result.error(f"Field '{field}' must be a string or array, got {type(value).__name__}")

        elif field in MAP_FIELDS:
            if not isinstance(value, dict):
                result.error(f"Field '{field}' must be a mapping/dict, got {type(value).__name__}")
            elif field == 'OCEAN_detail':
                for domain in ('openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'):
                    if domain in value:
                        v = value[domain]
                        if isinstance(v, bool) or not isinstance(v, (int, float)) or not (0 <= v <= 100):
                            result.error(f"Field 'OCEAN_detail.{domain}' must be a number from 0 to 100, got {v!r}")

    # OCEAN format check
    if isinstance(data.get('OCEAN'), str):
        if not OCEAN_RE.match(data['OCEAN']):
            result.error(
                f"OCEAN format invalid: '{data['OCEAN']}'. "
                "Must be five integers (0-100) separated by /. Example: 74/58/63/81/27"
            )

    # HEXACO format check
    if isinstance(data.get('HEXACO'), str):
        if not HEXACO_RE.match(data['HEXACO']):
            result.error(
                f"HEXACO format invalid: '{data['HEXACO']}'. "
                "Must be six integers (0-100) separated by /. Example: 64/52/71/58/69/77"
            )

    # Date format checks
    for date_field in ('updated', 'dob'):
        if isinstance(data.get(date_field), str):
            if not DATE_RE.match(data[date_field]):
                result.error(f"Field '{date_field}' must be YYYY-MM-DD format, got '{data[date_field]}'")

    # Attachment enum check
    if isinstance(data.get('attachment'), str):
        if data['attachment'] not in ATTACHMENT_VALUES:
            result.error(
                f"Invalid attachment value: '{data['attachment']}'. "
                f"Must be one of: {sorted(ATTACHMENT_VALUES)}"
            )

    # VIA_top5 max items
    if isinstance(data.get('VIA_top5'), list):
        if len(data['VIA_top5']) > 5:
            result.error(f"VIA_top5 must have at most 5 items, got {len(data['VIA_top5'])}")

    # VIA_bottom3 max items
    if isinstance(data.get('VIA_bottom3'), list):
        if len(data['VIA_bottom3']) > 3:
            result.error(f"VIA_bottom3 must have at most 3 items, got {len(data['VIA_bottom3'])}")

    # Sensitivity info
    sensitive_present = sorted(f for f in SENSITIVE_FIELDS if f in data)
    if sensitive_present:
        result.add_info(f"Sensitive fields present: {sensitive_present}")

    # YAML 1.1 coercion warnings (only reachable when a caller parsed with a 1.1 loader)
    for date_field in ('updated', 'dob'):
        if hasattr(data.get(date_field), 'isoformat'):
            result.warn(f"'{date_field}' was parsed as a date object — a YAML 1.1 parser coerced it. Quote the value.")

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
# Text and file loading
# ---------------------------------------------------------------------------

def parse_text(raw, result, size_bytes=None):
    """Parse raw .aiid text with the 1.2 Core Schema loader. Returns data or None (errors recorded)."""
    size = size_bytes if size_bytes is not None else len(raw.encode('utf-8'))
    if size > MAX_FILE_BYTES:
        result.error(f"File is {size} bytes; the limit is {MAX_FILE_BYTES} bytes (16 KiB)")
        return None

    for e in scan_prohibited_syntax(raw):
        result.error(e)

    try:
        data = yaml.load(raw, Loader=CoreSchemaLoader)
    except DuplicateKeyError as e:
        result.error(f"YAML duplicate key: {e}")
        return None
    except yaml.YAMLError as e:
        result.error(f"YAML parse error: {e}")
        return None

    if data is None:
        result.error("File is empty or contains only comments")
        return None

    return data


def validate_text(raw, strict=False, check_tier=False, size_bytes=None):
    """Validate raw .aiid text (parser-level rules plus field rules). size_bytes: the file's size on disk, if known."""
    pre = ValidationResult()
    data = parse_text(raw, pre, size_bytes=size_bytes)
    if pre.errors:
        return pre
    result = validate_aiid(data, strict=strict, check_tier=check_tier)
    result.warnings[:0] = pre.warnings
    return result


def load_and_validate(filepath, strict=False, check_tier=False):
    """Load a .aiid file from disk, parse YAML, validate."""
    path = Path(filepath)
    if not path.exists():
        result = ValidationResult()
        result.error(f"File not found: {filepath}")
        return result
    data = path.read_bytes()
    try:
        raw = data.decode('utf-8')
    except UnicodeDecodeError as e:
        result = ValidationResult()
        result.error(f"File is not UTF-8: {e}")
        return result
    return validate_text(raw, strict=strict, check_tier=check_tier, size_bytes=len(data))


# ---------------------------------------------------------------------------
# JSON Schema validation (optional, if jsonschema is installed)
# ---------------------------------------------------------------------------

DEFAULT_SCHEMA = Path(__file__).resolve().parent.parent.parent / 'schema' / 'aiid.schema.json'


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
        ("With OCEAN", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "74/58/63/81/27", "style": "direct"}),
        ("With HEXACO", {"aiid_version": "1.0", "display_name": "X", "HEXACO": "64/52/71/58/69/77", "style": "direct"}),
        ("Pseudonymous", {"aiid_version": "1.0", "display_name": "nightowl", "avoid": ["hedging"]}),
        ("With extensions", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "x_astro": "Sun:Tau Moon:Sco Asc:Lib"}),
        ("OCEAN boundary 0/100", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "0/100/0/100/0", "style": "direct"}),
        ("Both identifiers", {"aiid_version": "1.0", "name": "Full Name", "display_name": "Nick", "style": "direct"}),
        ("profile_version as integer", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "profile_version": 3}),
        ("profile_version as integral float", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "profile_version": 3.0}),
        ("Blank list items ignored", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "priorities": [None, "", "garden wall"]}),
        ("OCEAN_detail in range", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "OCEAN_detail": {"openness": 74}}),
        ("Blank optional field ignored", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "tone": None, "avoid": None}),
    ]

    invalid_cases = [
        ("Missing aiid_version", {"name": "Bad", "style": "direct"}, "aiid_version"),
        ("Missing identifier", {"aiid_version": "1.0", "style": "direct"}, "identifier"),
        ("Bad OCEAN format", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "high/med/low/med/low"}, "OCEAN"),
        ("OCEAN 4 values", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "74/58/63/81"}, "OCEAN"),
        ("OCEAN > 100", {"aiid_version": "1.0", "display_name": "X", "OCEAN": "74/58/63/81/150"}, "OCEAN"),
        ("Bad attachment", {"aiid_version": "1.0", "display_name": "X", "attachment": "complicated"}, "attachment"),
        ("Bad version", {"aiid_version": "2.0", "display_name": "X"}, "aiid_version"),
        ("avoid as string", {"aiid_version": "1.0", "display_name": "X", "avoid": "hedging"}, "avoid"),
        ("VIA_top5 too many", {"aiid_version": "1.0", "display_name": "X", "VIA_top5": ["a","b","c","d","e","f"]}, "VIA_top5"),
        ("Empty name", {"aiid_version": "1.0", "name": "", "style": "direct"}, "name"),
        ("Merge key", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "<<": {"a": 1}}, "merge"),
        ("narrative too long", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "narrative": "x" * 2001}, "narrative"),
        ("Nested merge key", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "OCEAN_detail": {"<<": {"a": 1}}}, "merge"),
        ("Non-string key", {"aiid_version": "1.0", "display_name": "X", "style": "direct", 123: "x"}, "keys"),
        ("profile_version as non-integral float", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "profile_version": 3.5}, "profile_version"),
        ("OCEAN_detail out of range", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "OCEAN_detail": {"openness": 170}}, "OCEAN_detail"),
        ("Emoji narrative counted in code points", {"aiid_version": "1.0", "display_name": "X", "style": "direct", "narrative": "\U0001F600" * 2001}, "narrative"),
    ]

    # Parser-level cases run on raw text (YAML 1.2 typing, prohibited syntax, size)
    valid_text_cases = [
        ("Unquoted date stays a string (YAML 1.2)", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nupdated: 2026-03-15\n'),
        ("yes/no/on/off stay strings (YAML 1.2)", 'aiid_version: "1.0"\ndisplay_name: X\nhumor: no\navoid: [yes, on, off]\n'),
        ("Leading-zero number does not crash (YAML 1.2 reads 09 as 9)", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nx_house_number: 09\n'),
        ("Template-shaped blank list items", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\npriorities:\n  - \n  - garden wall\n'),
        ("Emoji narrative under the cap (1500 code points)", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nnarrative: ' + "\U0001F600" * 1500 + '\n'),
    ]
    invalid_text_cases = [
        ("Duplicate key", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nstyle: casual\n'),
        ("Anchor and alias", 'aiid_version: "1.0"\ndisplay_name: &n X\nstyle: *n\n'),
        ("Explicit tag", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: !!str direct\n'),
        ("Merge key in text", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\n<<: {a: 1}\n'),
        ("File too large", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nnarrative: |\n' + ('  ' + 'x' * 78 + '\n') * 250),
        ("Non-string key in text", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\n123: x\n'),
        ("Complex key in text", 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\n? [a, b]\n: x\n'),
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
        if not r.valid:
            passed += 1
            print(f"  [PASS] Invalid case: {label}")
        else:
            failed += 1
            print(f"  [FAIL] Invalid case: {label} — expected errors but got none")

    for label, text in valid_text_cases:
        r = validate_text(text)
        if r.valid:
            passed += 1
            print(f"  [PASS] Valid text: {label}")
        else:
            failed += 1
            print(f"  [FAIL] Valid text: {label}")
            for e in r.errors:
                print(f"         ERROR: {e}")

    for label, text in invalid_text_cases:
        r = validate_text(text)
        if not r.valid:
            passed += 1
            print(f"  [PASS] Invalid text: {label}")
        else:
            failed += 1
            print(f"  [FAIL] Invalid text: {label} — expected errors but got none")

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
    parser.add_argument("--schema", nargs="?", const=str(DEFAULT_SCHEMA), default=None,
                        help="Also validate against the JSON Schema (default: the repo's schema/aiid.schema.json)")
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

    # Optional schema validation (on the same 1.2-parsed, blank-stripped data)
    if args.schema and not HAS_JSONSCHEMA:
        print("ERROR: --schema needs the jsonschema package. Install with: pip install jsonschema", file=sys.stderr)
        sys.exit(2)
    if args.schema and result.valid:
        try:
            raw = Path(args.file).read_bytes().decode('utf-8')
            pre = ValidationResult()
            data = parse_text(raw, pre)
            data = strip_blank_fields(data, pre) if isinstance(data, dict) else data
            for se in validate_with_schema(data, args.schema):
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

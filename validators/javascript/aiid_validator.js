#!/usr/bin/env node

/**
 * aiid_validator.js — Reference validator for the .aiID Core Profile Format v1.0
 *
 * Usage:
 *   node aiid_validator.js file.aiid
 *   node aiid_validator.js file.aiid --strict
 *   node aiid_validator.js file.aiid --tier
 *   node aiid_validator.js --test
 *   node aiid_validator.js file.aiid --json
 *
 * Requires:
 *   npm install yaml
 *
 * The yaml package parses with the YAML 1.2 Core Schema (schema: 'core'), so unquoted
 * dates and yes/no/on/off stay strings, and `<<` is a plain key (rejected: merge keys
 * are prohibited). Anchors, aliases and explicit tags are rejected too (spec 3.3).
 *
 * Exit codes:
 *   0 = valid
 *   1 = invalid (errors found)
 *   2 = usage error
 */

'use strict';

const fs = require('fs');
const path = require('path');

let YAML;
try {
  YAML = require('yaml');
} catch {
  console.error('ERROR: yaml package required. Install with: npm install yaml');
  process.exit(2);
}

// ---------------------------------------------------------------------------
// Patterns
// ---------------------------------------------------------------------------

const OCEAN_RE = /^(100|[1-9]?\d)\/(100|[1-9]?\d)\/(100|[1-9]?\d)\/(100|[1-9]?\d)\/(100|[1-9]?\d)$/;
const HEXACO_RE = /^(100|[1-9]?\d)\/(100|[1-9]?\d)\/(100|[1-9]?\d)\/(100|[1-9]?\d)\/(100|[1-9]?\d)\/(100|[1-9]?\d)$/;
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

const AIID_VERSIONS = new Set(['1.0']);

const MAX_FILE_BYTES = 16384; // spec section 3.6

// Length caps (characters), matching schema/aiid.schema.json
const MAX_LEN = {
  name: 120, display_name: 120, location: 200, pronouns: 60,
  attachment_note: 1000, humor: 300, stop_rule: 300,
  neurodivergence: 300, ethics: 300, narrative: 2000
};
const AI_INSTRUCTIONS_MAX = 2000;      // as a single string
const AI_INSTRUCTIONS_ITEM_MAX = 500;  // each list item
const AI_INSTRUCTIONS_MAX_ITEMS = 40;
const STRING_OR_LIST_STRING_MAX = 500;
const LIST_ITEM_MAX = 300;

const ATTACHMENT_VALUES = new Set([
  'secure', 'anxious_preoccupied', 'dismissive_avoidant',
  'fearful_avoidant', 'earned_secure'
]);

// Fields that accept string or list
const STRING_OR_LIST_FIELDS = new Set([
  'role', 'style', 'tone', 'format_pref', 'thinking', 'learning',
  'deciding', 'epistemic', 'strengths', 'ai_instructions'
]);

// Fields that must be arrays
const ARRAY_FIELDS = new Set([
  'avoid', 'VIA_top5', 'VIA_bottom3', 'core', 'priorities',
  'boundaries', 'goals_short', 'goals_long', 'archetypes',
  'patterns_to_watch'
]);

// Fields that must be strings
const STRING_FIELDS = new Set([
  'aiid_version', 'updated', 'name', 'display_name',
  'location', 'dob', 'pronouns', 'OCEAN', 'HEXACO', 'attachment',
  'attachment_note', 'humor', 'stop_rule', 'neurodivergence',
  'ethics', 'narrative'
]);

// Fields that accept a string or an integer
const STRING_OR_INT_FIELDS = new Set(['profile_version']);

// Fields that must be maps
const MAP_FIELDS = new Set(['OCEAN_detail']);

// All known core fields
const KNOWN_FIELDS = new Set([
  ...STRING_FIELDS, ...ARRAY_FIELDS, ...STRING_OR_LIST_FIELDS, ...STRING_OR_INT_FIELDS, ...MAP_FIELDS
]);

// Sensitivity classifications
const SENSITIVE_FIELDS = new Set([
  'dob', 'neurodivergence', 'attachment', 'attachment_note',
  'patterns_to_watch', 'narrative', 'boundaries'
]);

const PERSONAL_FIELDS = new Set([
  'name', 'display_name', 'location', 'pronouns',
  'OCEAN', 'OCEAN_detail', 'HEXACO', 'VIA_top5', 'VIA_bottom3'
]);

// ---------------------------------------------------------------------------
// Validation result
// ---------------------------------------------------------------------------

class ValidationResult {
  constructor() {
    this.errors = [];
    this.warnings = [];
    this.info = [];
    this.tier = null;
  }

  get valid() {
    return this.errors.length === 0;
  }

  error(msg) { this.errors.push(msg); }
  warn(msg) { this.warnings.push(msg); }
  addInfo(msg) { this.info.push(msg); }

  report() {
    const lines = [];
    lines.push(this.valid ? '✓ VALID' : '✗ INVALID');
    if (this.tier) lines.push(`  Compliance tier: ${this.tier}`);
    for (const e of this.errors) lines.push(`  ERROR: ${e}`);
    for (const w of this.warnings) lines.push(`  WARNING: ${w}`);
    for (const i of this.info) lines.push(`  INFO: ${i}`);
    return lines.join('\n');
  }

  toJSON() {
    return {
      valid: this.valid,
      tier: this.tier,
      errors: this.errors,
      warnings: this.warnings,
      info: this.info
    };
  }
}

// ---------------------------------------------------------------------------
// Duplicate key detection via YAML library
// ---------------------------------------------------------------------------

function parseWithDuplicateCheck(rawText) {
  const doc = YAML.parseDocument(rawText, {
    uniqueKeys: true,
    schema: 'core'   // YAML 1.2 core schema
  });

  const duplicateErrors = [];
  const otherErrors = [];
  const syntaxErrors = [];

  for (const err of doc.errors) {
    if (err.message && err.message.includes('duplicate key')) {
      duplicateErrors.push(err.message);
    } else {
      otherErrors.push(err.message || String(err));
    }
  }

  // Anchors, aliases and explicit tags are prohibited (spec 3.3); keys must be plain strings
  YAML.visit(doc, {
    Alias(key, node) {
      syntaxErrors.push(`Alias '*${node.source}': aliases are prohibited`);
    },
    Node(key, node) {
      if (node.anchor) syntaxErrors.push(`Anchor '&${node.anchor}': anchors are prohibited`);
      if (node.tag) syntaxErrors.push(`Explicit tag '${node.tag}': explicit tags are prohibited`);
    },
    Pair(key, pair) {
      const k = pair.key;
      if (!(YAML.isScalar(k) && typeof k.value === 'string')) {
        syntaxErrors.push(`Keys must be plain strings (got ${YAML.isScalar(k) ? JSON.stringify(k.value) : 'a complex key'})`);
      }
    }
  });

  let data;
  try {
    data = doc.errors.length === 0 ? doc.toJSON() : undefined;
  } catch (e) {
    otherErrors.push(e.message || String(e));
  }

  return { data, duplicateErrors, otherErrors, syntaxErrors };
}

// ---------------------------------------------------------------------------
// Core validation
// ---------------------------------------------------------------------------

function isNonEmptyString(val) {
  return typeof val === 'string' && val.trim().length > 0;
}

function isStringArray(val) {
  return Array.isArray(val) && val.every(item => isNonEmptyString(item));
}

function isBlank(val) {
  return val === null || val === undefined || (typeof val === 'string' && val.trim().length === 0);
}

const REQUIRED_FIELDS = new Set(['aiid_version', 'name', 'display_name']);

// Drop fields left blank (`tone:` with nothing after it) and blank list items (`- ` with nothing after it).
// Each one is a warning, not an error. A list that ends up empty counts as blank.
function stripBlankFields(data, result) {
  const cleaned = {};
  for (let [field, value] of Object.entries(data)) {
    if (Array.isArray(value)) {
      const kept = value.filter(item => !isBlank(item));
      if (kept.length < value.length) {
        result.warn(`Field '${field}' has ${value.length - kept.length} blank item(s); they were ignored`);
      }
      value = kept.length ? kept : null;
    }
    if (isBlank(value)) {
      if (REQUIRED_FIELDS.has(field)) {
        result.warn(`Field '${field}' is blank; a value is required`);
      } else {
        result.warn(`Field '${field}' is blank and was ignored (fill it in or delete the line)`);
      }
      continue;
    }
    cleaned[field] = value;
  }
  return cleaned;
}

// Paths of every `<<` key at any depth (merge keys are prohibited, spec 3.3)
function findMergeKeys(obj, path = '') {
  const hits = [];
  if (Array.isArray(obj)) {
    obj.forEach((v, i) => hits.push(...findMergeKeys(v, `${path}[${i}]`)));
  } else if (obj && typeof obj === 'object') {
    for (const [k, v] of Object.entries(obj)) {
      const here = path ? `${path}.${k}` : k;
      if (k === '<<') hits.push(here);
      hits.push(...findMergeKeys(v, here));
    }
  }
  return hits;
}

// Lengths are counted in Unicode code points (the same count Python and JSON Schema use), not UTF-16 units
function charCount(value) {
  return [...value].length;
}

function checkLen(result, label, value, cap) {
  if (typeof value === 'string' && charCount(value) > cap) {
    result.error(`Field '${label}' is ${charCount(value)} characters; the limit is ${cap}`);
  }
}

function validateAiid(data, { strict = false, checkTier = false } = {}) {
  const result = new ValidationResult();

  // Must be an object
  if (data === null || data === undefined || typeof data !== 'object' || Array.isArray(data)) {
    result.error(`Root element must be a YAML mapping (object), got ${Array.isArray(data) ? 'array' : typeof data}`);
    return result;
  }

  // Merge keys are prohibited at any level (spec 3.3); under the core schema `<<` arrives as a plain key
  for (const where of findMergeKeys(data)) {
    result.error(`Merge key '<<' at '${where}' is prohibited`);
  }

  data = stripBlankFields(data, result);

  // Required: aiid_version
  if (!('aiid_version' in data)) {
    result.error('Missing required field: aiid_version');
  } else if (!AIID_VERSIONS.has(data.aiid_version)) {
    result.error(`Unrecognized aiid_version: '${data.aiid_version}'. Known versions: ${[...AIID_VERSIONS].join(', ')}`);
  }

  // Required: at least one identifier
  const hasName = 'name' in data && isNonEmptyString(data.name);
  const hasDisplay = 'display_name' in data && isNonEmptyString(data.display_name);
  if (!hasName && !hasDisplay) {
    result.error("Missing required subject identifier: must include 'name' or 'display_name' (non-empty string)");
  }

  // Type checks for known fields
  for (const field of Object.keys(data)) {
    if (field.startsWith('x_')) continue; // extensions always valid

    if (!KNOWN_FIELDS.has(field)) {
      const msg = `Unknown field '${field}' (not in core spec, not x_-prefixed)`;
      if (strict) {
        result.error(msg);
      } else {
        result.warn(msg + ' — may be from a newer spec version');
      }
      continue;
    }

    const value = data[field];

    if (STRING_FIELDS.has(field)) {
      if (typeof value !== 'string') {
        // Only reachable when a caller parsed with a YAML 1.1 library
        if ((field === 'dob' || field === 'updated') && value instanceof Date) {
          result.warn(`'${field}' was parsed as a Date object — a YAML 1.1 parser coerced it. Quote the value: ${field}: "${value.toISOString().slice(0, 10)}"`);
        } else {
          result.error(`Field '${field}' must be a string, got ${typeof value}`);
        }
      } else if (field in MAX_LEN) {
        checkLen(result, field, value, MAX_LEN[field]);
      }
    } else if (STRING_OR_INT_FIELDS.has(field)) {
      if (!(typeof value === 'string' || (typeof value === 'number' && Number.isInteger(value)))) {
        result.error(`Field '${field}' must be a string or an integer, got ${typeof value}`);
      }
    } else if (ARRAY_FIELDS.has(field)) {
      if (!Array.isArray(value)) {
        result.error(`Field '${field}' must be an array/list, got ${typeof value}`);
      } else if (value.length === 0) {
        result.warn(`Field '${field}' is an empty array`);
      } else {
        value.forEach((item, i) => {
          if (!isNonEmptyString(item)) {
            result.error(`Field '${field}[${i}]' must be a non-empty string`);
          } else {
            checkLen(result, `${field}[${i}]`, item, LIST_ITEM_MAX);
          }
        });
      }
    } else if (STRING_OR_LIST_FIELDS.has(field)) {
      const strCap = field === 'ai_instructions' ? AI_INSTRUCTIONS_MAX : STRING_OR_LIST_STRING_MAX;
      const itemCap = field === 'ai_instructions' ? AI_INSTRUCTIONS_ITEM_MAX : LIST_ITEM_MAX;
      if (typeof value === 'string') {
        if (value.trim().length === 0) {
          result.error(`Field '${field}' must be non-empty`);
        } else {
          checkLen(result, field, value, strCap);
        }
      } else if (Array.isArray(value)) {
        if (value.length === 0) {
          result.warn(`Field '${field}' is an empty array`);
        }
        if (field === 'ai_instructions' && value.length > AI_INSTRUCTIONS_MAX_ITEMS) {
          result.error(`Field 'ai_instructions' has ${value.length} items; the limit is ${AI_INSTRUCTIONS_MAX_ITEMS}`);
        }
        value.forEach((item, i) => {
          if (!isNonEmptyString(item)) {
            result.error(`Field '${field}[${i}]' must be a non-empty string`);
          } else {
            checkLen(result, `${field}[${i}]`, item, itemCap);
          }
        });
      } else {
        result.error(`Field '${field}' must be a string or array, got ${typeof value}`);
      }
    } else if (MAP_FIELDS.has(field)) {
      if (value === null || typeof value !== 'object' || Array.isArray(value)) {
        result.error(`Field '${field}' must be a mapping/object, got ${Array.isArray(value) ? 'array' : typeof value}`);
      } else if (field === 'OCEAN_detail') {
        for (const domain of ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']) {
          if (domain in value) {
            const v = value[domain];
            if (typeof v !== 'number' || !(v >= 0 && v <= 100)) {
              result.error(`Field 'OCEAN_detail.${domain}' must be a number from 0 to 100, got ${JSON.stringify(v)}`);
            }
          }
        }
      }
    }
  }

  // OCEAN format check
  if ('OCEAN' in data && typeof data.OCEAN === 'string') {
    if (!OCEAN_RE.test(data.OCEAN)) {
      result.error(
        `OCEAN format invalid: '${data.OCEAN}'. ` +
        'Must be five integers (0-100) separated by /. Example: 74/58/63/81/27'
      );
    }
  }

  // HEXACO format check
  if ('HEXACO' in data && typeof data.HEXACO === 'string') {
    if (!HEXACO_RE.test(data.HEXACO)) {
      result.error(
        `HEXACO format invalid: '${data.HEXACO}'. ` +
        'Must be six integers (0-100) separated by /. Example: 64/52/71/58/69/77'
      );
    }
  }

  // Date format checks
  for (const dateField of ['updated', 'dob']) {
    if (dateField in data && typeof data[dateField] === 'string') {
      if (!DATE_RE.test(data[dateField])) {
        result.error(`Field '${dateField}' must be YYYY-MM-DD format, got '${data[dateField]}'`);
      }
    }
  }

  // Attachment enum check
  if ('attachment' in data && typeof data.attachment === 'string') {
    if (!ATTACHMENT_VALUES.has(data.attachment)) {
      result.error(
        `Invalid attachment value: '${data.attachment}'. ` +
        `Must be one of: ${[...ATTACHMENT_VALUES].sort().join(', ')}`
      );
    }
  }

  // VIA_top5 max items
  if ('VIA_top5' in data && Array.isArray(data.VIA_top5)) {
    if (data.VIA_top5.length > 5) {
      result.error(`VIA_top5 must have at most 5 items, got ${data.VIA_top5.length}`);
    }
  }

  // VIA_bottom3 max items
  if ('VIA_bottom3' in data && Array.isArray(data.VIA_bottom3)) {
    if (data.VIA_bottom3.length > 3) {
      result.error(`VIA_bottom3 must have at most 3 items, got ${data.VIA_bottom3.length}`);
    }
  }

  // Sensitivity info
  const sensitivePresent = [...SENSITIVE_FIELDS].filter(f => f in data);
  if (sensitivePresent.length > 0) {
    result.addInfo(`Sensitive fields present: ${sensitivePresent.join(', ')}`);
  }

  // Compliance tier
  if (checkTier) {
    result.tier = determineTier(data);
  }

  return result;
}

function determineTier(data) {
  if (!('aiid_version' in data)) return null;
  if (!('name' in data || 'display_name' in data)) return null;

  const levelAFields = ['style', 'tone', 'avoid', 'ai_instructions'];
  const hasLevelA = levelAFields.some(f => f in data);
  if (!hasLevelA) return 'Below Level A (no communication or instruction field)';

  const levelBFields = ['priorities', 'boundaries'];
  const hasLevelB = levelBFields.some(f => f in data);
  if (!hasLevelB) return 'Level A (Minimal)';

  const coreProfiles = ['OCEAN', 'HEXACO', 'OCEAN_detail', 'VIA_top5', 'VIA_bottom3', 'attachment'];
  const hasProfile = coreProfiles.some(f => f in data);
  const hasExtension = Object.keys(data).some(k => k.startsWith('x_'));
  if (!hasProfile && !hasExtension) return 'Level B (Actionable)';

  return 'Level C (Extended)';
}

// ---------------------------------------------------------------------------
// File loading
// ---------------------------------------------------------------------------

function validateText(raw, options = {}) {
  const result = new ValidationResult();

  const size = Buffer.byteLength(raw, 'utf-8');
  if (size > MAX_FILE_BYTES) {
    result.error(`File is ${size} bytes; the limit is ${MAX_FILE_BYTES} bytes (16 KiB)`);
    return result;
  }

  // Parse with duplicate key detection and the prohibited-syntax scan
  const { data, duplicateErrors, otherErrors, syntaxErrors } = parseWithDuplicateCheck(raw);

  for (const err of duplicateErrors) {
    result.error(`YAML duplicate key: ${err}`);
  }
  for (const err of otherErrors) {
    result.error(`YAML parse error: ${err}`);
  }
  for (const err of syntaxErrors) {
    result.error(err);
  }

  if (result.errors.length > 0) return result;

  if (data === null || data === undefined) {
    result.error('File is empty or contains only comments');
    return result;
  }

  const validationResult = validateAiid(data, options);

  // Merge
  validationResult.errors.unshift(...result.errors);
  validationResult.warnings.unshift(...result.warnings);
  return validationResult;
}

function loadAndValidate(filepath, options = {}) {
  if (!fs.existsSync(filepath)) {
    const result = new ValidationResult();
    result.error(`File not found: ${filepath}`);
    return result;
  }
  const raw = fs.readFileSync(filepath, 'utf-8');
  return validateText(raw, options);
}

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------

function runSelfTest() {
  console.log('Running .aiid validator self-test...\n');

  const validCases = [
    ['Minimal display_name', { aiid_version: '1.0', display_name: 'Alex', style: 'direct' }],
    ['Minimal name', { aiid_version: '1.0', name: 'Alex Rivera', tone: 'casual' }],
    ['With OCEAN', { aiid_version: '1.0', display_name: 'X', OCEAN: '74/58/63/81/27', style: 'direct' }],
    ['With HEXACO', { aiid_version: '1.0', display_name: 'X', HEXACO: '64/52/71/58/69/77', style: 'direct' }],
    ['Pseudonymous', { aiid_version: '1.0', display_name: 'nightowl', avoid: ['hedging'] }],
    ['With extensions', { aiid_version: '1.0', display_name: 'X', style: 'direct', x_astro: 'Sun:Tau Moon:Sco Asc:Lib' }],
    ['OCEAN boundary 0/100', { aiid_version: '1.0', display_name: 'X', OCEAN: '0/100/0/100/0', style: 'direct' }],
    ['Both identifiers', { aiid_version: '1.0', name: 'Full Name', display_name: 'Nick', style: 'direct' }],
    ['profile_version as integer', { aiid_version: '1.0', display_name: 'X', style: 'direct', profile_version: 3 }],
    ['profile_version as integral float', { aiid_version: '1.0', display_name: 'X', style: 'direct', profile_version: 3.0 }],
    ['Blank list items ignored', { aiid_version: '1.0', display_name: 'X', style: 'direct', priorities: [null, '', 'garden wall'] }],
    ['OCEAN_detail in range', { aiid_version: '1.0', display_name: 'X', style: 'direct', OCEAN_detail: { openness: 74 } }],
    ['Blank optional field ignored', { aiid_version: '1.0', display_name: 'X', style: 'direct', tone: null, avoid: null }],
  ];

  const invalidCases = [
    ['Missing aiid_version', { name: 'Bad', style: 'direct' }, 'aiid_version'],
    ['Missing identifier', { aiid_version: '1.0', style: 'direct' }, 'identifier'],
    ['Bad OCEAN format', { aiid_version: '1.0', display_name: 'X', OCEAN: 'high/med/low/med/low' }, 'OCEAN'],
    ['OCEAN 4 values', { aiid_version: '1.0', display_name: 'X', OCEAN: '74/58/63/81' }, 'OCEAN'],
    ['OCEAN > 100', { aiid_version: '1.0', display_name: 'X', OCEAN: '74/58/63/81/150' }, 'OCEAN'],
    ['Bad attachment', { aiid_version: '1.0', display_name: 'X', attachment: 'complicated' }, 'attachment'],
    ['Bad version', { aiid_version: '2.0', display_name: 'X' }, 'aiid_version'],
    ['avoid as string', { aiid_version: '1.0', display_name: 'X', avoid: 'hedging' }, 'avoid'],
    ['VIA_top5 too many', { aiid_version: '1.0', display_name: 'X', VIA_top5: ['a', 'b', 'c', 'd', 'e', 'f'] }, 'VIA_top5'],
    ['Empty name', { aiid_version: '1.0', name: '', style: 'direct' }, 'name'],
    ['Merge key', { aiid_version: '1.0', display_name: 'X', style: 'direct', '<<': { a: 1 } }, 'merge'],
    ['narrative too long', { aiid_version: '1.0', display_name: 'X', style: 'direct', narrative: 'x'.repeat(2001) }, 'narrative'],
    ['Nested merge key', { aiid_version: '1.0', display_name: 'X', style: 'direct', OCEAN_detail: { '<<': { a: 1 } } }, 'merge'],
    ['profile_version as non-integral float', { aiid_version: '1.0', display_name: 'X', style: 'direct', profile_version: 3.5 }, 'profile_version'],
    ['OCEAN_detail out of range', { aiid_version: '1.0', display_name: 'X', style: 'direct', OCEAN_detail: { openness: 170 } }, 'OCEAN_detail'],
    ['Emoji narrative counted in code points', { aiid_version: '1.0', display_name: 'X', style: 'direct', narrative: '\u{1F600}'.repeat(2001) }, 'narrative'],
  ];

  // Parser-level cases run on raw text (YAML 1.2 typing, prohibited syntax, size)
  const validTextCases = [
    ['Unquoted date stays a string (YAML 1.2)', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nupdated: 2026-03-15\n'],
    ['yes/no/on/off stay strings (YAML 1.2)', 'aiid_version: "1.0"\ndisplay_name: X\nhumor: no\navoid: [yes, on, off]\n'],
    ['Leading-zero number is fine (YAML 1.2 reads 09 as 9)', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nx_house_number: 09\n'],
    ['Template-shaped blank list items', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\npriorities:\n  - \n  - garden wall\n'],
    ['Emoji narrative under the cap (1500 code points)', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nnarrative: ' + '\u{1F600}'.repeat(1500) + '\n'],
  ];
  const invalidTextCases = [
    ['Duplicate key', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nstyle: casual\n'],
    ['Anchor and alias', 'aiid_version: "1.0"\ndisplay_name: &n X\nstyle: *n\n'],
    ['Explicit tag', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: !!str direct\n'],
    ['Merge key in text', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\n<<: {a: 1}\n'],
    ['File too large', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\nnarrative: |\n' + ('  ' + 'x'.repeat(78) + '\n').repeat(250)],
    ['Non-string key in text', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\n123: x\n'],
    ['Complex key in text', 'aiid_version: "1.0"\ndisplay_name: X\nstyle: direct\n? [a, b]\n: x\n'],
  ];

  let passed = 0;
  let failed = 0;

  for (const [label, data] of validCases) {
    const r = validateAiid(data);
    if (r.valid) {
      passed++;
      console.log(`  [PASS] Valid case: ${label}`);
    } else {
      failed++;
      console.log(`  [FAIL] Valid case: ${label}`);
      r.errors.forEach(e => console.log(`         ERROR: ${e}`));
    }
  }

  for (const [label, data] of invalidCases) {
    const r = validateAiid(data);
    if (!r.valid) {
      passed++;
      console.log(`  [PASS] Invalid case: ${label}`);
    } else {
      failed++;
      console.log(`  [FAIL] Invalid case: ${label} — expected errors but got none`);
    }
  }

  for (const [label, text] of validTextCases) {
    const r = validateText(text);
    if (r.valid) {
      passed++;
      console.log(`  [PASS] Valid text: ${label}`);
    } else {
      failed++;
      console.log(`  [FAIL] Valid text: ${label}`);
      r.errors.forEach(e => console.log(`         ERROR: ${e}`));
    }
  }

  for (const [label, text] of invalidTextCases) {
    const r = validateText(text);
    if (!r.valid) {
      passed++;
      console.log(`  [PASS] Invalid text: ${label}`);
    } else {
      failed++;
      console.log(`  [FAIL] Invalid text: ${label} — expected errors but got none`);
    }
  }

  console.log(`\n${passed}/${passed + failed} tests passed.`);
  return failed === 0;
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function main() {
  const args = process.argv.slice(2);

  if (args.includes('--help') || args.includes('-h') || args.length === 0) {
    console.log(`
.aiID v1.0 Reference Validator (JavaScript)

Usage:
  node aiid_validator.js <file.aiid> [options]
  node aiid_validator.js --test

Options:
  --strict    Treat unknown non-x_ fields as errors
  --tier      Report compliance tier (A/B/C)
  --json      Output results as JSON
  --test      Run built-in self-test suite
  --help      Show this help

Exit codes:
  0 = valid, 1 = invalid, 2 = usage error
`);
    process.exit(args.length === 0 ? 2 : 0);
  }

  if (args.includes('--test')) {
    const success = runSelfTest();
    process.exit(success ? 0 : 1);
  }

  const filepath = args.find(a => !a.startsWith('--'));
  if (!filepath) {
    console.error('ERROR: No file specified');
    process.exit(2);
  }

  const strict = args.includes('--strict');
  const checkTier = args.includes('--tier');
  const jsonOutput = args.includes('--json');

  const result = loadAndValidate(filepath, { strict, checkTier });

  if (jsonOutput) {
    console.log(JSON.stringify(result.toJSON(), null, 2));
  } else {
    console.log(result.report());
  }

  process.exit(result.valid ? 0 : 1);
}

// ---------------------------------------------------------------------------
// Module exports (for use as library)
// ---------------------------------------------------------------------------

module.exports = {
  validateAiid,
  validateText,
  loadAndValidate,
  parseWithDuplicateCheck,
  determineTier,
  ValidationResult,
  KNOWN_FIELDS,
  SENSITIVE_FIELDS,
  ATTACHMENT_VALUES
};

// Run CLI if executed directly
if (require.main === module) {
  main();
}

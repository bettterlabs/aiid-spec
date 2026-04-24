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
  'aiid_version', 'profile_version', 'updated', 'name', 'display_name',
  'location', 'dob', 'pronouns', 'OCEAN', 'HEXACO', 'attachment',
  'attachment_note', 'humor', 'stop_rule', 'neurodivergence',
  'ethics', 'narrative'
]);

// Fields that must be maps
const MAP_FIELDS = new Set(['OCEAN_detail']);

// All known core fields
const KNOWN_FIELDS = new Set([
  ...STRING_FIELDS, ...ARRAY_FIELDS, ...STRING_OR_LIST_FIELDS, ...MAP_FIELDS
]);

// Sensitivity classifications
const SENSITIVE_FIELDS = new Set([
  'dob', 'neurodivergence', 'attachment', 'attachment_note',
  'patterns_to_watch', 'narrative', 'boundaries'
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

  for (const err of doc.errors) {
    if (err.message && err.message.includes('duplicate key')) {
      duplicateErrors.push(err.message);
    } else {
      otherErrors.push(err.message || String(err));
    }
  }

  return { data: doc.toJSON(), duplicateErrors, otherErrors };
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

function validateAiid(data, { strict = false, checkTier = false } = {}) {
  const result = new ValidationResult();

  // Must be an object
  if (data === null || data === undefined || typeof data !== 'object' || Array.isArray(data)) {
    result.error(`Root element must be a YAML mapping (object), got ${Array.isArray(data) ? 'array' : typeof data}`);
    return result;
  }

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
        // Handle YAML date coercion
        if ((field === 'dob' || field === 'updated') && value instanceof Date) {
          result.warn(`'${field}' was parsed as a Date object — YAML date coercion occurred. Quote the value: ${field}: "${value.toISOString().slice(0, 10)}"`);
        } else {
          result.error(`Field '${field}' must be a string, got ${typeof value}`);
        }
      } else if ((field === 'name' || field === 'display_name') && value.trim().length === 0) {
        result.error(`Field '${field}' must be non-empty`);
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
          }
        });
      }
    } else if (STRING_OR_LIST_FIELDS.has(field)) {
      if (typeof value === 'string') {
        if (value.trim().length === 0) {
          result.error(`Field '${field}' must be non-empty`);
        }
      } else if (Array.isArray(value)) {
        if (value.length === 0) {
          result.warn(`Field '${field}' is an empty array`);
        }
        value.forEach((item, i) => {
          if (!isNonEmptyString(item)) {
            result.error(`Field '${field}[${i}]' must be a non-empty string`);
          }
        });
      } else {
        result.error(`Field '${field}' must be a string or array, got ${typeof value}`);
      }
    } else if (MAP_FIELDS.has(field)) {
      if (value === null || typeof value !== 'object' || Array.isArray(value)) {
        result.error(`Field '${field}' must be a mapping/object, got ${Array.isArray(value) ? 'array' : typeof value}`);
      }
    }
  }

  // OCEAN format check
  if ('OCEAN' in data && typeof data.OCEAN === 'string') {
    if (!OCEAN_RE.test(data.OCEAN)) {
      result.error(
        `OCEAN format invalid: '${data.OCEAN}'. ` +
        'Must be five integers (0-100) separated by /. Example: 91/82/78/78/39'
      );
    }
  }

  // HEXACO format check
  if ('HEXACO' in data && typeof data.HEXACO === 'string') {
    if (!HEXACO_RE.test(data.HEXACO)) {
      result.error(
        `HEXACO format invalid: '${data.HEXACO}'. ` +
        'Must be six integers (0-100) separated by /. Example: 78/45/82/65/70/91'
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

function loadAndValidate(filepath, options = {}) {
  const result = new ValidationResult();

  if (!fs.existsSync(filepath)) {
    result.error(`File not found: ${filepath}`);
    return result;
  }

  const raw = fs.readFileSync(filepath, 'utf-8');

  // Parse with duplicate key detection
  const { data, duplicateErrors, otherErrors } = parseWithDuplicateCheck(raw);

  for (const err of duplicateErrors) {
    result.error(`YAML duplicate key: ${err}`);
  }
  for (const err of otherErrors) {
    result.error(`YAML parse error: ${err}`);
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

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------

function runSelfTest() {
  console.log('Running .aiid validator self-test...\n');

  const validCases = [
    ['Minimal display_name', { aiid_version: '1.0', display_name: 'Alex', style: 'direct' }],
    ['Minimal name', { aiid_version: '1.0', name: 'Alex Rivera', tone: 'casual' }],
    ['With OCEAN', { aiid_version: '1.0', display_name: 'X', OCEAN: '91/82/78/78/39', style: 'direct' }],
    ['With HEXACO', { aiid_version: '1.0', display_name: 'X', HEXACO: '78/45/82/65/70/91', style: 'direct' }],
    ['Pseudonymous', { aiid_version: '1.0', display_name: 'nightowl', avoid: ['hedging'] }],
    ['With extensions', { aiid_version: '1.0', display_name: 'X', style: 'direct', x_astro: 'Sun:Aqr Moon:Leo Asc:Cap' }],
    ['OCEAN boundary 0/100', { aiid_version: '1.0', display_name: 'X', OCEAN: '0/100/0/100/0', style: 'direct' }],
    ['Both identifiers', { aiid_version: '1.0', name: 'Full Name', display_name: 'Nick', style: 'direct' }],
  ];

  const invalidCases = [
    ['Missing aiid_version', { name: 'Bad', style: 'direct' }, 'aiid_version'],
    ['Missing identifier', { aiid_version: '1.0', style: 'direct' }, 'identifier'],
    ['Bad OCEAN format', { aiid_version: '1.0', display_name: 'X', OCEAN: 'high/med/low/med/low' }, 'OCEAN'],
    ['OCEAN 4 values', { aiid_version: '1.0', display_name: 'X', OCEAN: '91/82/78/78' }, 'OCEAN'],
    ['OCEAN > 100', { aiid_version: '1.0', display_name: 'X', OCEAN: '91/82/78/78/150' }, 'OCEAN'],
    ['Bad attachment', { aiid_version: '1.0', display_name: 'X', attachment: 'complicated' }, 'attachment'],
    ['Bad version', { aiid_version: '2.0', display_name: 'X' }, 'aiid_version'],
    ['avoid as string', { aiid_version: '1.0', display_name: 'X', avoid: 'hedging' }, 'avoid'],
    ['VIA_top5 too many', { aiid_version: '1.0', display_name: 'X', VIA_top5: ['a', 'b', 'c', 'd', 'e', 'f'] }, 'VIA_top5'],
    ['Empty name', { aiid_version: '1.0', name: '', style: 'direct' }, 'name'],
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

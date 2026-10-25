# Changelog

All notable changes to the .aiID specification.

## [Unreleased]

**Scope:**
- Added "What .aiID is not" to the README and the white paper: a personalization format, not an identity credential and never an access-control gate (spec 6.1, 8.1, 8.7).

**Format:**
- Hard file cap of 16,384 bytes and length limits on free-text fields (`narrative` 2,000, `ai_instructions` 2,000 or 40 items of 500, `attachment_note` 1,000, list items 300). Prompt-injection surface, spec 3.6 and 8.5.
- A blank value (`tone:` with nothing after it, or a `- ` list item with nothing after it) is treated as absent, with a warning, so a half-filled template validates once a name is present.
- `profile_version` accepts an integer as well as a string.
- The schema no longer rejects unknown non-`x_` fields; the spec (3.4) says to warn on them, and `additionalProperties: false` contradicted that and broke forward compatibility (10.2).
- Schema `$id` now points at the repository (the previous `aiid-spec.org` domain was never registered).
- `aiid_version` wording: the format is 1.0; this document is Community Draft 0.9 of it.

**Validators:**
- The Python validator installs YAML 1.2 Core Schema typing on top of PyYAML (a YAML 1.1 parser), so `yes`/`no`/`on`/`off` and unquoted dates stay strings and both validators agree.
- Both validators now reject anchors, aliases, explicit tags and merge keys (spec 3.3), which neither checked before.
- Self-tests pass: 42 cases in Python, 41 in JavaScript (were 18 each). New test vectors 22 to 27 (valid) and 16 to 23 (invalid). `test-vectors/run.sh` runs both validators over every shipped file and checks each verdict against its folder.
- An independent review of this change set before commit found 13 problems, all folded in: a crash on numbers with a leading zero (the YAML 1.2 integer constructor now replaces PyYAML's 1.1 one), length caps that differed between schema, validators and spec, lengths counted in UTF-16 units in JavaScript (now code points in both), the file cap measured after newline conversion in Python (now the bytes on disk), `profile_version: 3.0` accepted by one validator and not the other (an integral float now counts as an integer in both, as in JSON Schema), empty lists and out-of-range `OCEAN_detail` values that the schema rejected and the validators did not (now rejected by all three), blank list items that kept the template failing after a name was filled in (now ignored with a warning), merge keys below the top level (now caught at any depth), non-string keys (a clean error in both; Python used to crash), and `--schema` without the jsonschema package (now a usage error, exit 2).
- Python: `--schema` runs the JSON Schema on the same parsed data.

**Guidance:**
- Consuming applications should say once per session that a profile is in use (6.1); "inform behavior invisibly" was the risk 8.1 names.
- Sensitivity classes now cover personality scores (Personal), `ai_instructions` (Basic) and extensions (Personal; astrology and Human Design fields are birth-data derived and Sensitive).
- Implementation guide: a sycophancy warning at the top of framework calibration, the attachment-style calibration collapsed to pacing and shape, the conflict-check example no longer reads a psychological field.
- ChatGPT custom-instruction limit updated (1,500 free, 5,000 paid, July 2026).

**Corrections:**
- References: Big5-Scaler is Cho and Cheong, arXiv 2508.06149, August 2025 (was "Jiang et al., 2024"); MetaGlyph is January 2026 (was 2025); the unlocatable JAMIA abbreviation study moved to Unverified. Added the 2026 personalization and memory-injection studies.
- Prior art: identity.txt, Portable AI Memory, agent workspace files and AGENTS.md, and the vendors' 2026 import flows.
- The standard example is Level C by the spec's own tier rule (it carries personality data and extensions), not Level B as the spec and README said.
- Token counts in the examples measured (about 60, 320 and 750 tokens; the README's "30 seconds" and the white paper's "eight tokens" corrected).
- PyYAML described correctly as a YAML 1.1 library.

**Examples:**
- Refreshed the sample values in the examples, schema, guides, test vectors and validator self-tests with new illustrative ones. Every test vector keeps its verdict.

## [0.9] — 2026-03-29

### Community Draft 0.9 (from v1.0 Draft)

**Structural:**
- Split monolithic document into four companion documents: Core Spec, Implementation Guide, Creator Guide, Extensions Registry
- Relabeled from "v1.0 Draft" to "v0.9 Community Draft"

**Core format:**
- Pinned YAML version to 1.2.2
- Changed media type from `text/yaml` to `application/yaml` per RFC 9512
- Made `aiid_version` mandatory
- Changed required identifier from `name` to `display_name` OR `name` (pseudonymous profiles supported)
- Added HEXACO as core personality framework
- Moved MBTI and Enneagram from core to extension layer (`x_mbti`, `x_ennea`)
- Moved astrology, Human Design, Gene Keys from core to extension layer (`x_astro`, `x_hd_*`, `x_gene_keys`)
- Banned YAML anchors, aliases, merge keys, and explicit tags
- Stated comments are non-semantic

**Security:**
- Added full Security and Privacy Considerations section with threat model
- Added field sensitivity classifications (Basic / Personal / Sensitive)
- Changed extension default from "SHOULD interpret" to "MUST ignore unknown"
- Downgraded `ai_instructions` from system-level to user-preference privilege
- Added safe ingestion requirements for consuming applications

**Governance:**
- Added version semantics (major.minor)
- Added compatibility rules, deprecation policy, change process
- Added compliance tiers (Level A / B / C)
- Added conformance requirements for documents and consumers

**Evidence:**
- Scoped empirical claims to design goals and preliminary evidence
- Classified references by source type
- Removed unverifiable claims

**Removed from core spec:**
- Section 11 (.link File) — one-line reference in Future Considerations
- Section 12 (Generation Tool) — moved to Creator Guide
- Section 6 (Three Compass Questions) — moved to Creator Guide
- Hub platform and business model language
- NFC/physical distribution details

**New deliverables:**
- JSON Schema (Draft 2020-12)
- Reference validator (Python)
- Reference validator (JavaScript)
- 21 valid + 15 invalid test vectors
- Extensions and Profiles Registry
- Implementation Guide
- Creator Guide with model-neutral creation prompt

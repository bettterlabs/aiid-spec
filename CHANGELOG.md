# Changelog

All notable changes to the .aiID specification.

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

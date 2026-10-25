# .aiID — Portable AI Identity Format

> One file. Every conversation. No more starting as a stranger.

The .aiID (AI Identity Document) is a portable, user-authored file format that gives any AI system immediate context about who someone is. It encodes communication preferences, personality frameworks, cognitive style, values, current priorities, behavioral boundaries, and explicit user instructions in a structured YAML format.

**Status:** Community Draft 0.9 — open for feedback  
**License:** CC BY 4.0

---

## Quick Start

### Create your .aiid in 5 minutes

1. Copy the [starter template](templates/starter.aiid)
2. Fill in your name, communication style, and priorities
3. Save as `yourname.aiid`
4. Paste into any AI system's instructions or upload as a file

### Create your .aiid with a guided conversation

Copy the [model-neutral creation prompt](docs/creator-guide.md#appendix-a-model-neutral-creation-prompt) into any AI (ChatGPT, Claude, Gemini, Grok, or any model) and be walked through a 20-30 minute conversation that generates your file.

### Validate your .aiid

```bash
# Python
pip install pyyaml jsonschema
python validators/python/aiid_validator.py your_file.aiid --tier --schema

# JavaScript
npm install yaml
node validators/javascript/aiid_validator.js your_file.aiid --tier
```

A line left blank in the template (`tone:` with nothing after it, or `- ` with nothing after it) is ignored with a warning, not an error. Files are capped at 16 KiB and every free-text field has a length limit (2,000 characters for `narrative` and `ai_instructions`; the spec's field reference lists the rest).

---

## What's in a .aiid file?

```yaml
# .aiid v1.0
aiid_version: "1.0"
display_name: Alex
role: product designer

style: direct, visual, concise
avoid: [jargon, filler, platitudes]

OCEAN: 85/72/45/80/30

priorities:
  - redesigning checkout flow
  - preparing for parental leave

ai_instructions: "Skip the preamble. Show me options, not explanations."
```

That's a valid, useful .aiid file. The communication lines take a minute to write. The `OCEAN` line needs a Big Five test first (about ten minutes at bigfive-test.com) and can be left out. How far a given model changes its behavior varies by model; the spec's research notes say what has been measured.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Core Specification](spec/core-spec.md) | The format definition — fields, validation, conformance, security |
| [Implementation Guide](docs/implementation-guide.md) | How to ingest, validate, and act on .aiid files safely |
| [Creator Guide](docs/creator-guide.md) | How to create your .aiid file (includes the model-neutral creation prompt) |
| [Extensions Registry](spec/extensions-registry.md) | MBTI, Enneagram, astrology, Human Design, Gene Keys field definitions |
| [JSON Schema](schema/aiid.schema.json) | Machine-readable schema for validation |

---

## Specification Summary

### Core Fields

| Section | Key Fields | Impact |
|---------|-----------|--------|
| **Communication** | `style`, `tone`, `avoid`, `format_pref`, `humor` | Highest — shapes every response |
| **Personality** | `OCEAN`, `HEXACO`, `VIA_top5`, `attachment` | High — calibrates approach and depth |
| **Cognition** | `thinking`, `learning`, `deciding` | Medium — shapes explanation structure |
| **Current Focus** | `priorities`, `boundaries`, `goals_short` | Medium — contextualizes advice |
| **AI Instructions** | `ai_instructions` | High — explicit user preferences for interaction |

### Extension Fields (x_ prefix)

MBTI, Enneagram, astrology, Human Design, and Gene Keys are supported through the extension system. See the [Extensions Registry](spec/extensions-registry.md).

### Compliance Tiers

| Tier | Requirements |
|------|-------------|
| **Level A** (Minimal) | `aiid_version` + identifier + one communication field |
| **Level B** (Actionable) | Level A + `priorities` or `boundaries` |
| **Level C** (Extended) | Level B + personality data or extensions |

---

## Validation

Reference validators in Python and JavaScript. Both produce matching results, including on the YAML 1.1 versus 1.2 differences: unquoted dates and `yes`/`no` are strings in both (the Python one installs YAML 1.2 Core Schema typing on top of PyYAML, which is a YAML 1.1 parser).

```bash
# Self-test (both pass: 42 cases in Python, 41 in JavaScript; the extra Python case is a non-string key, which a JavaScript object cannot express)
python validators/python/aiid_validator.py --test
node validators/javascript/aiid_validator.js --test

# Validate a file (--schema also runs the JSON Schema; needs jsonschema)
python validators/python/aiid_validator.py my.aiid --tier --strict --schema

# JSON output (for CI/tooling)
node validators/javascript/aiid_validator.js my.aiid --tier --json

# Every shipped file through both validators, verdicts checked against their folders
sh test-vectors/run.sh
```

Test vectors: [valid](test-vectors/valid/) (27 cases) and [invalid](test-vectors/invalid/) (23 cases). Six invalid cases (duplicate keys, anchors and aliases, explicit tags, merge keys, a non-string key, file size) are parser-level rules: a plain JSON Schema check passes them; the reference validators reject them. One valid case (blank optional fields) fails a raw schema run, because the validators drop blank values before applying the schema.

---

## Design Principles

1. **Context efficiency** — Structured YAML minimizes token cost
2. **Behavioral constraints first** — Communication style and avoid lists have the highest impact per token
3. **Machine-parseable, human-readable** — Standard YAML, no custom parsers
4. **Writable by hand** — No technical background required
5. **Progressive depth** — 20-line file to 200-line file, both valid
6. **Open and user-owned** — CC BY 4.0, no platform lock-in

---

## What .aiID is not

.aiID is a personalization format. It is not an identity credential.

- **It does not verify who you are.** A .aiid file is written by the person it describes and carries no signature or provenance. Nothing in the format proves that the file's author is its subject ([spec §8.1](spec/core-spec.md#81-threat-model)).
- **It must not gate access.** Do not use a .aiid file to decide age, nationality, residency, licensure, or eligibility for anything. Attribute-gated access needs evidence independent of the person making the claim. A self-authored file relocates the claim; it does not check it.
- **It is untrusted input to the system that reads it.** Consuming applications MUST treat .aiid content as user-authored text with no elevated privilege ([spec §6.1](spec/core-spec.md#61-general-principles)).

Signatures, verifiable credentials, and access control are real needs with their own standards. A future companion spec may let a .aiid file *carry* an externally signed credential; the trust in that case belongs to the issuer, never to the format ([spec §8.7](spec/core-spec.md#87-limitations)). Today the scope is one thing: telling an AI how to work with you.

---

## Repository Structure

```
aiid-spec/
├── README.md
├── LICENSE
├── CHANGELOG.md
│
├── spec/
│   ├── core-spec.md              # Core specification
│   └── extensions-registry.md    # Extension field definitions
│
├── docs/
│   ├── implementation-guide.md   # Developer integration guide
│   └── creator-guide.md          # User creation guide
│
├── schema/
│   └── aiid.schema.json          # JSON Schema (Draft 2020-12)
│
├── validators/
│   ├── python/
│   │   ├── aiid_validator.py
│   │   └── requirements.txt
│   └── javascript/
│       ├── aiid_validator.js
│       └── package.json
│
├── test-vectors/
│   ├── run.sh                    # both validators over every shipped file
│   ├── valid/                    # 27 valid .aiid files
│   └── invalid/                  # 23 invalid .aiid files
│
├── templates/
│   └── starter.aiid              # Fill-in-the-blanks template
│
└── examples/
    ├── minimal.aiid              # Level A example
    ├── standard.aiid             # Level C example (personality data and extensions)
    └── comprehensive.aiid        # Level C example
```

---

## Contributing

Contributions welcome via GitHub issues and pull requests:

- **Field proposals** — Open an issue with rationale, type definition, sensitivity classification, and example usage
- **Extension proposals** — See the [Extensions Registry](spec/extensions-registry.md#7-proposing-new-registered-extensions) for the process
- **Implementation libraries** — In any language
- **Platform integration guides** — For specific AI platforms
- **Bug reports** — Against the spec, schema, or validators

---

## Roadmap

- [x] Core specification (Community Draft 0.9)
- [x] JSON Schema + reference validators (Python, JavaScript)
- [x] Implementation Guide
- [x] Creator Guide + model-neutral creation prompt
- [x] Extensions Registry
- [ ] Interoperability testing across platforms
- [ ] Web-based creation wizard
- [ ] CLI validation tool (standalone binary)
- [ ] Community feedback period
- [ ] v1.0 release

---

## License

CC BY 4.0 — open standard, free forever.

Created by Derrius Logan Casey. Maintained at [github.com/bettterlabs/aiid-spec](https://github.com/bettterlabs/aiid-spec).

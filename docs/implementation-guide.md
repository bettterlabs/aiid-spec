# .aiID Implementation Guide

**Version:** 0.9 (Community Draft)  
**Companion to:** .aiID Core Profile Format v1.0  
**Date:** March 28, 2026  
**License:** CC BY 4.0  
**Status:** Non-normative. This document provides guidance, not requirements.

---

## Purpose

This guide helps developers and AI system builders ingest, validate, normalize, and act on .aiid files safely and effectively. It covers:

1. Safe ingestion pipeline
2. Prompt wrapping patterns
3. Host-side normalization
4. Framework-specific behavioral calibration
5. Conflict resolution implementation
6. Platform-specific integration notes
7. Freshness and staleness handling
8. Multi-profile handling
9. Debugging and failure modes

All guidance in this document is **non-normative** unless it restates a requirement from the core specification (marked with MUST/SHOULD/MAY).

---

## Table of Contents

1. Safe Ingestion Pipeline
2. Prompt Wrapping Patterns
3. Host-Side Normalization
4. Framework-Specific Behavioral Calibration
5. Conflict Resolution Implementation
6. Platform Integration Notes
7. Freshness and Staleness Handling
8. Multi-Profile Handling
9. Debugging and Failure Modes
10. Token Budget Planning
11. Redaction Profiles

---

## 1. Safe Ingestion Pipeline

A .aiid file is user-authored untrusted input. The core spec requires that consuming applications treat it accordingly. This section describes a recommended ingestion pipeline.

### 1.1 Pipeline Overview

```
[Raw file] → Parse → Validate → Normalize → Classify → Wrap → Inject
```

### 1.2 Step: Parse

Parse the file using a YAML 1.2 library with duplicate-key detection enabled. PyYAML is a YAML 1.1 library: use the reference validator's `CoreSchemaLoader` (it installs YAML 1.2 Core Schema typing and rejects duplicate keys) or ruamel.yaml. The validator also rejects anchors, aliases, explicit tags and merge keys, and enforces the 16 KiB file cap.

**Python (the minimal duplicate-key loader; prefer importing `CoreSchemaLoader` from the validator):**
```python
import yaml

class SafeNoDuplicateLoader(yaml.SafeLoader):
    pass

def _check_duplicates(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"Duplicate key: {key}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping

SafeNoDuplicateLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _check_duplicates
)

def parse_aiid(raw_text):
    return yaml.load(raw_text, Loader=SafeNoDuplicateLoader)
```

**JavaScript:**
```javascript
import YAML from 'yaml';

function parseAiid(rawText) {
  const doc = YAML.parseDocument(rawText, { uniqueKeys: true });
  if (doc.errors.length > 0) {
    throw new Error(`YAML errors: ${doc.errors.map(e => e.message).join('; ')}`);
  }
  return doc.toJSON();
}
```

**Failure mode:** If parsing fails, reject the file entirely. Do not attempt partial parsing.

### 1.3 Step: Validate

Run the parsed data against the JSON Schema and/or the reference validator. At minimum, check:

- `aiid_version` is present and recognized
- At least one subject identifier (`name` or `display_name`) is present and non-empty
- Fields that are present conform to expected types
- No duplicate keys (should be caught at parse time)

**Failure mode:** If validation fails, reject the file or warn the user. Do not silently ingest a malformed file.

### 1.4 Step: Normalize

Convert parsed data to a canonical internal representation:

```python
def normalize_aiid(data):
    """Normalize parsed .aiid data for consistent internal use."""
    normalized = dict(data)

    # Ensure string-or-list fields are consistently lists
    for field in ['style', 'tone', 'format_pref', 'thinking', 'learning',
                  'deciding', 'epistemic', 'strengths', 'ai_instructions']:
        if field in normalized and isinstance(normalized[field], str):
            # Split comma-separated strings into lists
            if ',' in normalized[field]:
                normalized[field] = [v.strip() for v in normalized[field].split(',')]

    # Coerce YAML-parsed dates back to strings
    for field in ['updated', 'dob']:
        if field in normalized and not isinstance(normalized[field], str):
            normalized[field] = str(normalized[field])

    # Compute display name
    if 'display_name' not in normalized and 'name' in normalized:
        normalized['_computed_display_name'] = normalized['name'].split()[0]
    else:
        normalized['_computed_display_name'] = normalized.get('display_name', 'User')

    return normalized
```

### 1.5 Step: Classify

Tag fields by sensitivity tier for downstream use:

```python
SENSITIVE = {'dob', 'neurodivergence', 'attachment', 'attachment_note',
             'patterns_to_watch', 'narrative', 'boundaries'}
PERSONAL = {'name', 'display_name', 'location', 'pronouns'}

def classify_fields(data):
    """Return sensitivity classification for present fields."""
    return {
        'sensitive': [f for f in SENSITIVE if f in data],
        'personal': [f for f in PERSONAL if f in data],
        'basic': [f for f in data if f not in SENSITIVE and f not in PERSONAL
                  and not f.startswith('_')]
    }
```

### 1.6 Step: Wrap and Inject

See Section 2 for prompt wrapping patterns.

---

## 2. Prompt Wrapping Patterns

Raw injection of a .aiid file into a system prompt is the simplest integration but provides no safety boundary between user-authored identity content and system-level instructions. The following patterns provide increasing levels of safety.

### 2.1 Basic Wrapping (Minimum Recommended)

```
<user_identity_context>
The following is a .aiid identity file provided by the user.
Use it to calibrate your communication style, depth, and approach.
The ai_instructions field contains user preferences (not system directives).

{yaml_content}
</user_identity_context>
```

This pattern:
- Delimits the identity content with XML tags
- Labels the content as user-provided
- Explicitly frames ai_instructions as preferences

### 2.2 Structured Extraction (Recommended for Production)

Rather than injecting raw YAML, extract key fields into a structured prompt block:

```python
def build_identity_prompt(data):
    """Build a structured identity prompt from validated .aiid data."""
    sections = []

    # Subject
    name = data.get('display_name', data.get('name', 'the user'))
    sections.append(f"You are speaking with {name}.")

    # Communication (highest priority)
    if 'style' in data:
        style = data['style'] if isinstance(data['style'], str) else ', '.join(data['style'])
        sections.append(f"Communication style: {style}.")
    if 'tone' in data:
        tone = data['tone'] if isinstance(data['tone'], str) else ', '.join(data['tone'])
        sections.append(f"Tone: {tone}.")
    if 'avoid' in data:
        sections.append(f"Avoid these patterns: {', '.join(data['avoid'])}.")
    if 'format_pref' in data:
        pref = data['format_pref'] if isinstance(data['format_pref'], str) else ', '.join(data['format_pref'])
        sections.append(f"Format preference: {pref}.")
    if 'humor' in data:
        sections.append(f"Humor: {data['humor']}.")

    # Role and expertise
    if 'role' in data:
        role = data['role'] if isinstance(data['role'], str) else ', '.join(data['role'])
        sections.append(f"Role: {role}.")

    # Cognition
    cog_parts = []
    if 'thinking' in data:
        t = data['thinking'] if isinstance(data['thinking'], str) else ', '.join(data['thinking'])
        cog_parts.append(f"thinks in {t}")
    if 'learning' in data:
        l = data['learning'] if isinstance(data['learning'], str) else ', '.join(data['learning'])
        cog_parts.append(f"learns via {l}")
    if cog_parts:
        sections.append(f"Cognitive style: {'; '.join(cog_parts)}.")

    # Personality data
    if 'OCEAN' in data:
        sections.append(f"Big Five (O/C/E/A/N): {data['OCEAN']}.")
    if 'HEXACO' in data:
        sections.append(f"HEXACO (H/E/X/A/C/O): {data['HEXACO']}.")
    if 'attachment' in data:
        sections.append(f"Attachment style: {data['attachment']}.")

    # Current focus
    if 'priorities' in data:
        sections.append(f"Current priorities: {'; '.join(data['priorities'])}.")
    if 'boundaries' in data:
        sections.append(f"Active boundaries: {'; '.join(data['boundaries'])}.")
    if 'patterns_to_watch' in data:
        sections.append(f"Patterns to watch: {'; '.join(data['patterns_to_watch'])}.")

    # User instructions (last, clearly labeled)
    if 'ai_instructions' in data:
        inst = data['ai_instructions']
        if isinstance(inst, list):
            inst = ' '.join(inst)
        sections.append(f"User preferences for AI interaction: {inst}")

    return '\n'.join(sections)
```

This pattern:
- Strips YAML syntax, eliminating parsing ambiguity for the model
- Places communication directives first (highest behavioral impact)
- Labels ai_instructions as "user preferences" not "instructions"
- Omits raw narrative and extension data (reducing injection surface)

### 2.3 Tiered Injection (For Token-Constrained Contexts)

When token budget is tight, inject only the highest-value fields:

**Tier 1 (~30-50 tokens):** `display_name`, `style`, `tone`, `avoid`  
**Tier 2 (~80-120 tokens):** Tier 1 + `OCEAN`/`HEXACO`, `priorities`, `ai_instructions`  
**Tier 3 (~200-400 tokens):** Tier 2 + `boundaries`, `patterns_to_watch`, `narrative`, cognition fields  
**Full (~400-800 tokens):** Everything including extensions

```python
def build_tiered_prompt(data, max_tokens=200):
    """Build identity prompt within a token budget."""
    if max_tokens < 50:
        # Tier 1: communication only
        fields = ['display_name', 'name', 'style', 'tone', 'avoid']
    elif max_tokens < 150:
        # Tier 2: + personality + priorities
        fields = ['display_name', 'name', 'style', 'tone', 'avoid',
                  'OCEAN', 'HEXACO', 'priorities', 'ai_instructions']
    elif max_tokens < 400:
        # Tier 3: + context
        fields = ['display_name', 'name', 'style', 'tone', 'avoid',
                  'OCEAN', 'HEXACO', 'priorities', 'ai_instructions',
                  'boundaries', 'patterns_to_watch', 'narrative',
                  'thinking', 'learning', 'role']
    else:
        fields = None  # include everything

    filtered = {k: v for k, v in data.items()
                if fields is None or k in fields}
    return build_identity_prompt(filtered)
```

---

## 3. Host-Side Normalization

Certain operations are better performed by the host application than delegated to the language model.

### 3.1 Freshness Computation

The core spec notes that models should treat stale files with appropriate skepticism. Models are unreliable at date arithmetic. Compute freshness at ingestion:

```python
from datetime import datetime, timedelta

def compute_freshness(data):
    """Compute freshness state and inject into data."""
    updated = data.get('updated')
    if not updated:
        return 'unknown'

    try:
        updated_date = datetime.strptime(str(updated), '%Y-%m-%d')
    except ValueError:
        return 'unparseable'

    age = datetime.now() - updated_date
    if age < timedelta(days=30):
        return 'fresh'
    elif age < timedelta(days=180):
        return 'current'
    elif age < timedelta(days=365):
        return 'aging'
    else:
        return 'stale'
```

Inject the result into the prompt:

```python
freshness = compute_freshness(data)
if freshness in ('aging', 'stale'):
    prompt += f"\nNote: This identity file was last updated {data['updated']}. "
    prompt += "Priorities and short-term goals may have changed. "
    prompt += "If these become relevant, gently ask if they're still current."
```

### 3.2 OCEAN Score Parsing

Parse the compact OCEAN string into named values for richer prompting:

```python
def parse_ocean(ocean_str):
    """Parse '74/58/63/81/27' into named dict."""
    parts = ocean_str.split('/')
    if len(parts) != 5:
        return None
    labels = ['Openness', 'Conscientiousness', 'Extraversion',
              'Agreeableness', 'Neuroticism']
    return {label: int(val) for label, val in zip(labels, parts)}
```

### 3.3 Conflict Pre-Resolution

Some conflicts between fields can be detected and resolved before the model sees them:

```python
def check_conflicts(data):
    """Detect and log potential conflicts for human review."""
    conflicts = []

    # Example: format_pref asks for prose while ai_instructions asks for bullet lists
    if 'ai_instructions' in data and 'format_pref' in data:
        inst = str(data['ai_instructions']).lower()
        pref = str(data['format_pref']).lower()
        if 'prose' in pref and any(w in inst for w in ['bullet', 'bullets', 'list']):
            conflicts.append(
                "format_pref asks for prose but ai_instructions asks for lists. "
                "Per conflict resolution: ai_instructions takes precedence."
            )
    # Do not add checks that read a psychological field (attachment, neurodivergence,
    # patterns_to_watch) against the person's own instructions: the core spec (6.3)
    # forbids psychological inference, and the person's words win anyway.

    return conflicts
```

Log conflicts for debugging but resolve them per the core spec's hierarchy: `ai_instructions` > communication fields > framework data > inferred behavior.

---

## 4. Framework-Specific Behavioral Calibration

This section provides guidance on how AI systems may calibrate behavior based on personality framework data. These are tendencies and suggestions, not deterministic rules. Explicit communication fields (`style`, `tone`, `avoid`) always take precedence.

**Read this first.** Two 2026 studies found that handing a model a condensed user profile made it more agreeable and more deferential: a CHI 2026 study (MIT and Penn State, 38 participants over two weeks) saw the largest agreeableness increase from a profile held in memory, and a nine-model study (Kelley and Riedl, 2026) saw personalization raise emotional validation while its effect on independent judgment depended on the assistant's role. So: use framework data to choose pacing, depth and format. Never use it to soften a correction, skip a disagreement, or decide what the person can hear. If a calibration below would have the model agree more, drop it.

### 4.1 Big Five (OCEAN) Calibration

Scores are integers 0-100. The following thresholds are approximate guidelines:

**Openness (O):**
- High (>75): Comfortable with abstract, unconventional, and creative approaches. Can handle ambiguity and speculative framing. May appreciate novel perspectives and unusual analogies.
- Moderate (35-75): Balanced. Standard approach works well.
- Low (<35): Prefers concrete, practical, proven methods. Avoid speculative framing. Lead with evidence and precedent.

**Conscientiousness (C):**
- High (>75): Values structure, follow-through, clear plans. Provide organized responses with explicit steps. Acknowledge deadlines and commitments.
- Low (<35): May find rigid structure constraining. Offer flexible frameworks. Don't over-structure.

**Extraversion (E):**
- High (>75): Energized by ideas and interaction. Can handle more content per response. May appreciate brainstorming and rapid exchange.
- Low (<35): May prefer focused, concise exchanges. Don't overwhelm with options. Depth over breadth.

**Agreeableness (A):**
- High (>75): Values harmony and collaboration. Frame disagreements gently. Lead with areas of agreement.
- Low (<35): Comfortable with direct challenge. Don't soften unnecessarily. Respect their preference for straight talk.

**Neuroticism (N):**
- High (>75): May benefit from more reassurance and stability in tone. Avoid adding unnecessary uncertainty. Be clear about what is and isn't known.
- Low (<35): Emotionally steady. Can handle direct, unvarnished feedback without extra scaffolding.

**Score interaction patterns:**
- High O + Low C: Creative but may struggle with execution. Help bridge ideas to action plans.
- High C + Low O: Methodical but may resist novel approaches. Introduce change incrementally with evidence.
- High N + Low A: May be stressed and direct about it. Don't take sharpness personally; address the underlying concern.
- High E + High O: Likely enjoys exploratory, wide-ranging conversations. May need help focusing.

### 4.2 HEXACO Calibration

HEXACO adds Honesty-Humility (H) as the first factor. Calibration for E/X/A/C/O follows the same patterns as Big Five with the caveat that HEXACO's Agreeableness and Emotionality differ slightly from Big Five Agreeableness and Neuroticism.

**Honesty-Humility (H):**
- High (>75): Values fairness, sincerity, and modesty. May be uncomfortable with flattery, manipulation framing, or overly promotional language.
- Low (<35): More comfortable with self-promotion, strategic framing, and competitive contexts. Not inherently dishonest — just less averse to status-seeking.

### 4.3 Attachment Style Calibration

Attachment style describes relational patterns. In an AI interaction context, these translate to communication preferences — not clinical relationships.

**secure / earned_secure:**
Standard interaction. The person has a stable relational baseline. No special calibration needed beyond explicit communication preferences.

**anxious_preoccupied / dismissive_avoidant / fearful_avoidant:**
One calibration for all three, and it is about pacing and shape only: be consistent in tone, give concrete next steps, do not repeat points, and do not push for commitment or closure. Do not vary substance, candor or disagreement by attachment style; the core spec (6.3) forbids psychological inference, and the earlier per-style guidance here read too much like it. If `ai_instructions` asks for blunt or challenging interaction, that wins.
- Note: if `ai_instructions` requests blunt or challenging interaction, honor that — the person is explicitly overriding the default calibration.

**Important caveat:** These are interaction style calibrations, not therapeutic interventions. AI systems should not diagnose, pathologize, reference the attachment label in conversation, or treat attachment style as more authoritative than the person's explicit instructions.

### 4.4 VIA Character Strengths Calibration

VIA strengths can inform how the AI frames advice and feedback:

- If **Creativity** is a top strength, the person may appreciate novel approaches and unconventional solutions.
- If **Judgment/Critical Thinking** is a top strength, lead with evidence and reasoning.
- If **Kindness** is a top strength, frame feedback with care for others' impact.
- If **Humor** is a top strength, lighter touch is welcome (cross-reference the `humor` field).
- If **Perseverance** is a top strength, the person may respond well to "push through" framing.
- If **Prudence** is a bottom strength, the person may benefit from gentle risk-checking (but don't lecture).

VIA data is supplementary. It's most useful when explicit communication fields don't cover a particular interaction pattern.

### 4.5 Extension Framework Calibration

Behavioral guidance for MBTI, Enneagram, astrology, Human Design, and Gene Keys is documented in the **Extensions and Profiles Registry**, Section 5. That guidance is non-normative and applies only to implementations that opt into supporting those extensions.

---

## 5. Conflict Resolution Implementation

The core spec defines a priority hierarchy. Here's how to implement it in practice.

### 5.1 Priority Hierarchy

```
1. ai_instructions       (explicit user directives)
2. Communication fields   (style, tone, avoid, format_pref, humor, stop_rule)
3. Core framework data    (OCEAN, HEXACO, VIA, attachment)
4. Extension data         (x_mbti, x_ennea, x_hd_*, x_astro, x_gene_keys)
5. Inferred behavior      (model's own interpretation)
```

Higher levels override lower levels. The model should never infer a preference that contradicts an explicitly stated one.

### 5.2 Common Conflict Scenarios

**Scenario:** `attachment: fearful_avoidant` but `ai_instructions: "Be brutally honest. Don't soften anything."`  
**Resolution:** Honor ai_instructions. The person is aware of their attachment style and explicitly wants direct communication anyway.

**Scenario:** `OCEAN: 25/90/20/85/70` (low openness, high agreeableness) but `style: experimental, provocative`  
**Resolution:** Honor style. The person has explicitly chosen a communication preference that diverges from what OCEAN might suggest. Style is level 2; OCEAN is level 3.

**Scenario:** `avoid: [unsolicited_advice]` but `patterns_to_watch: [overcommitting]` and user describes taking on a new project  
**Resolution:** This is genuinely ambiguous. The `avoid` field says don't give unsolicited advice. The `patterns_to_watch` field implies accountability. A reasonable resolution: ask a question ("How does this fit with your current commitments?") rather than giving advice ("You're overcommitting again"). Questions honor both fields.

**Scenario:** `x_hd_type: Reflector` (wait a lunar cycle before deciding) but `ai_instructions: "Push me to decide fast."`  
**Resolution:** Honor ai_instructions. Extensions are level 4; ai_instructions are level 1.

### 5.3 Implementation Pattern

```python
def resolve_communication_style(data):
    """Resolve final communication directives from all sources."""
    directives = {
        'style': None,
        'tone': None,
        'avoid': [],
        'approach_notes': []
    }

    # Level 3-4: framework and extension defaults
    if 'OCEAN' in data:
        scores = parse_ocean(data['OCEAN'])
        if scores:
            if scores['Agreeableness'] < 35:
                directives['approach_notes'].append(
                    'Framework suggests comfort with directness')
            if scores['Neuroticism'] > 75:
                directives['approach_notes'].append(
                    'Framework suggests preference for stable, reassuring tone')

    # Level 2: explicit communication fields (override framework)
    if 'style' in data:
        directives['style'] = data['style']
    if 'tone' in data:
        directives['tone'] = data['tone']
    if 'avoid' in data:
        directives['avoid'] = data['avoid']

    # Level 1: ai_instructions (override everything)
    # These are injected as-is into the prompt as user preferences
    if 'ai_instructions' in data:
        directives['ai_instructions'] = data['ai_instructions']

    return directives
```

---

## 6. Platform Integration Notes

### 6.1 ChatGPT (OpenAI)

**Custom Instructions:** Paste the .aiid contents (or structured extraction) into the "Custom Instructions" field. Limited to 1,500 characters on the free plan and 5,000 on paid plans (OpenAI release note, July 15, 2026), so use Tier 1-2 extraction for compact files or paste raw YAML for files under the limit. The standard example in this repository is about 1,100 characters; the comprehensive one is about 1,550 and does not fit the free-plan field.

**GPT Knowledge:** Upload the .aiid file to a Custom GPT's knowledge base. The GPT can reference it across conversations.

**File Upload:** Upload at conversation start. ChatGPT parses text files and can interpret YAML structure.

**Memory interaction:** If ChatGPT Memory is also active, .aiid content may overlap or conflict with stored memories. The .aiid file should be treated as the authoritative source when conflicts arise, since it's explicitly curated by the user.

### 6.2 Claude (Anthropic)

**System Prompt / Project Instructions:** Include .aiid contents in the system prompt (API) or Project Instructions (claude.ai). This is the most reliable method.

**File Upload:** Upload the .aiid file. Claude reads YAML natively.

**Projects:** Add the .aiid file to a Project's knowledge base for persistent context across all conversations in that project.

**Memory interaction:** If Claude Memory is active, it may contain information that overlaps with the .aiid file. The .aiid file represents the user's curated self-description and should be treated as authoritative for fields it covers.

### 6.3 Gemini (Google)

**System Instructions:** Include .aiid contents in the system instruction field (API) or Gems configuration.

**File Upload:** Upload at conversation start in Gemini Advanced.

### 6.4 Grok (xAI)

**System Prompt:** Include .aiid contents in system prompt via API.

**Note:** Platform capabilities change frequently. Test current behavior before assuming a specific integration path works.

### 6.5 Open-Source Models (Llama, Mistral, etc.)

**System Prompt:** Standard system prompt injection works. Use the structured extraction pattern (Section 2.2) for best results, since smaller models may struggle with raw YAML parsing.

**Considerations:**
- Smaller models have less training data on personality frameworks. OCEAN and MBTI are likely recognized; Gene Keys and Human Design may not be.
- Token budgets are often tighter. Use tiered injection (Section 2.3).
- Test with your specific model — framework recognition varies significantly.

### 6.6 API Integrations

For applications that accept .aiid files from users:

```python
# Full safe ingestion pipeline
from aiid_validator import load_and_validate, SafeNoDuplicateLoader
import yaml

def ingest_aiid(filepath):
    # 1. Validate
    result = load_and_validate(filepath, strict=False, check_tier=True)
    if not result.valid:
        return None, result.errors

    # 2. Parse
    with open(filepath) as f:
        data = yaml.load(f, Loader=SafeNoDuplicateLoader)

    # 3. Normalize
    data = normalize_aiid(data)

    # 4. Classify
    sensitivity = classify_fields(data)

    # 5. Compute freshness
    freshness = compute_freshness(data)

    # 6. Build prompt
    prompt = build_identity_prompt(data)
    if freshness in ('aging', 'stale'):
        prompt += f"\n(Note: profile last updated {data.get('updated', 'unknown date')}; "
        prompt += "priorities may have changed.)"

    return prompt, None
```

---

## 7. Freshness and Staleness Handling

### 7.1 Freshness States

| State | Age | Behavior |
|-------|-----|----------|
| `fresh` | < 30 days | Trust all fields fully |
| `current` | 30-180 days | Trust all fields; no warnings needed |
| `aging` | 180-365 days | `priorities` and `goals_short` may be stale. Gently ask if relevant. |
| `stale` | > 365 days | `priorities`, `goals_short`, and `boundaries` may be significantly outdated. Communication preferences and personality data are likely still accurate. |
| `unknown` | no `updated` field | Treat as `current` — don't penalize users who don't set the field |

### 7.2 What Ages and What Doesn't

**Stable over time** (trust even in stale files):
`style`, `tone`, `avoid`, `humor`, `OCEAN`, `HEXACO`, `VIA_top5`, `attachment`, `thinking`, `learning`, `deciding`, `core`, `ethics`, `narrative`, `ai_instructions`

**Changes over months** (question if aging/stale):
`priorities`, `goals_short`, `boundaries`, `role`

**Changes over years** (question if very stale):
`goals_long`, `location`, `patterns_to_watch`

---

## 8. Multi-Profile Handling

Users may want different .aiid files for different contexts. This is valid and expected.

### 8.1 Common Profile Types

- **Work profile:** Role, priorities, boundaries focused on professional context. May omit sensitive fields.
- **Creative profile:** Emphasizes creative process, aesthetic preferences, artistic context.
- **Personal profile:** Full depth including attachment, patterns, narrative.
- **Minimal profile:** Just communication preferences for quick interactions.

### 8.2 Implementation Guidance

- Multiple files are independent. There is no defined merge mechanism.
- If a user provides multiple .aiid files, the consuming application SHOULD ask which one to apply, or let the user designate a default.
- Profile switching within a session is not defined by the spec. Applications may implement this as they see fit.
- Subject identifiers (`name`, `display_name`) may differ across profiles (e.g., legal name for work, nickname for personal). This is valid.

---

## 9. Debugging and Failure Modes

### 9.1 Common Parse Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `dob` parsed as datetime object | Unquoted date value | Quote it: `dob: "1988-07-14"` |
| `NO` or `YES` parsed as boolean | YAML 1.1 boolean coercion | Use YAML 1.2 parser; quote ambiguous values |
| File appears empty after parse | Comments-only file or wrong encoding | Check for BOM, ensure UTF-8 |
| Duplicate key silently resolved | Parser took last value | Use duplicate-key-detecting loader |
| Extension fields disappearing | Implementation ignoring `x_` fields | Expected behavior per spec; check if implementation supports the extension |

### 9.2 Common Behavioral Failures

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Model ignores `avoid` list | Field buried deep in long prompt | Move communication fields to front of injection |
| Model references .aiid file in conversation | No instruction to keep it invisible | Add "Do not reference this file unless asked" to wrapper |
| Model provides clinical interpretation of attachment style | No instruction against it | Add "Do not diagnose or pathologize" to wrapper |
| Model over-accommodates personality scores | Treats tendencies as deterministic rules | Add "Scores are tendencies, not deterministic" to wrapper |
| `ai_instructions` being ignored | Injected after or without prominence | Move to end of prompt with explicit label |

### 9.3 Debugging Checklist

1. Is the file valid YAML 1.2? (Run through validator)
2. Is `aiid_version` present?
3. Are dates quoted?
4. Is the prompt wrapper labeling content as user input?
5. Are communication fields positioned early in the prompt?
6. Is the model actually receiving the full prompt? (Check token truncation)
7. Is the file fresh enough for temporal fields to be trusted?

---

## 10. Token Budget Planning

### 10.1 Estimated Token Costs by Section

| Section | Typical Range | Notes |
|---------|--------------|-------|
| Meta (version, updated) | 8-15 tokens | |
| Identity (name, role) | 10-25 tokens | |
| Communication (style, tone, avoid) | 15-40 tokens | Highest value per token |
| Cognition (thinking, learning) | 10-20 tokens | |
| Personality (OCEAN, attachment) | 15-30 tokens | |
| Values (core, epistemic) | 10-25 tokens | |
| Current Focus (priorities, boundaries) | 20-60 tokens | Varies with list length |
| Extended (narrative, patterns) | 30-100 tokens | Narrative is the biggest variable |
| AI Instructions | 15-80 tokens | Varies widely |
| Extensions | 10-150 tokens | Depends on depth |
| **YAML syntax overhead** | ~20-40 tokens | Keys, colons, indentation |
| **Prompt wrapper** | ~30-50 tokens | |

### 10.2 Budget Targets

| Context | Budget | Strategy |
|---------|--------|----------|
| Short conversations | 50-100 tokens | Tier 1: communication only |
| Standard conversations | 150-300 tokens | Tier 2: communication + personality + priorities |
| Deep work sessions | 300-600 tokens | Tier 3: full core fields |
| Dedicated assistant | 600-1200 tokens | Full file including extensions |
| Always-on project context | 800-2000 tokens | Full file; budget is amortized across many conversations |

---

## 11. Redaction Profiles

For users who want to share different subsets of their .aiid in different contexts.

### 11.1 Predefined Profiles

**Public profile** (safe for broad sharing):
Include: `display_name`, `role`, `style`, `tone`, `avoid`, `format_pref`, `humor`, `thinking`, `learning`
Exclude: All Personal and Sensitive fields

**Professional profile:**
Include: Everything in Public + `name`, `location`, `pronouns`, `role`, `priorities`, `boundaries`, `ai_instructions`
Exclude: `dob`, `neurodivergence`, `attachment`, `attachment_note`, `patterns_to_watch`, `narrative` unless explicitly included

**Full profile:**
Include: Everything
Note: User should be aware that all Sensitive fields are present

### 11.2 Implementation

```python
REDACTION_PROFILES = {
    'public': {
        'exclude': {'name', 'location', 'pronouns', 'dob', 'neurodivergence',
                    'attachment', 'attachment_note', 'patterns_to_watch',
                    'narrative', 'boundaries'}
    },
    'professional': {
        'exclude': {'dob', 'neurodivergence', 'attachment', 'attachment_note',
                    'patterns_to_watch', 'narrative'}
    },
    'full': {
        'exclude': set()
    }
}

def redact_aiid(data, profile='professional'):
    """Produce a redacted copy of .aiid data."""
    excluded = REDACTION_PROFILES.get(profile, {}).get('exclude', set())
    return {k: v for k, v in data.items() if k not in excluded}
```

---

The .aiID Implementation Guide is maintained at github.com/bettterlabs/aiid-spec.

Published under CC BY 4.0.

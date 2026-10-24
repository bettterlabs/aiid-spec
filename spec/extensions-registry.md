# .aiID Extensions and Profiles Registry

**Version:** 0.9 (Community Draft)  
**Companion to:** .aiID Core Profile Format v1.0  
**Date:** March 28, 2026  
**License:** CC BY 4.0

---

## Purpose

This document defines field schemas, value vocabularies, and usage guidance for registered extensions to the .aiID Core Profile Format. Extensions use the `x_` prefix and are governed by the rules in Section 9 of the core specification:

- Implementations MUST NOT reject files containing `x_`-prefixed fields.
- Implementations MUST ignore unknown extension fields by default.
- Implementations MAY support named extensions they explicitly recognize.

This registry is the canonical reference for extension field names, types, allowed values, and behavioral notes. Extensions listed here are **registered** — their schemas are stable and their field names are reserved. Private (unregistered) extensions may use any `x_` name not listed here.

---

## Table of Contents

1. Personality Typologies
   - 1.1 MBTI (`x_mbti`)
   - 1.2 Enneagram (`x_ennea`)
2. Astrological Data
   - 2.1 Natal Chart Shorthand (`x_astro`)
   - 2.2 Natal Chart Detail (`x_astro_detail`)
3. Human Design
   - 3.1 Type (`x_hd_type`)
   - 3.2 Strategy (`x_hd_strategy`)
   - 3.3 Authority (`x_hd_authority`)
   - 3.4 Profile (`x_hd_profile`)
   - 3.5 Detail (`x_hd_detail`)
4. Gene Keys (`x_gene_keys`)
5. Behavioral Guidance for Extensions
6. Private Extensions
7. Proposing New Registered Extensions

---

## 1. Personality Typologies

### 1.1 MBTI

| Property | Value |
|----------|-------|
| **Field name** | `x_mbti` |
| **Type** | string |
| **Format** | Four uppercase letters |
| **Source** | Any validated MBTI assessment |
| **Token cost** | ~2 tokens |

**Allowed values:**

```
ISTJ  ISFJ  INFJ  INTJ
ISTP  ISFP  INFP  INTP
ESTP  ESFP  ENFP  ENTP
ESTJ  ESFJ  ENFJ  ENTJ
```

**Pattern:** `^[EI][SN][TF][JP]$`

**Example:**
```yaml
x_mbti: INTJ
```

**Notes:** MBTI is widely recognized by frontier models but has debated test-retest reliability in the psychometric literature. It describes cognitive function preferences (how a person processes information and makes decisions). Many users find it a useful shorthand despite the academic debate. Models generally interpret MBTI types with reasonable consistency.

---

### 1.2 Enneagram

| Property | Value |
|----------|-------|
| **Field name** | `x_ennea` |
| **Type** | string |
| **Format** | Type number (1-9) optionally followed by `w` and wing number |
| **Source** | Any validated Enneagram assessment |
| **Token cost** | ~2-3 tokens |

**Pattern:** `^[1-9](w[1-9])?$`

**Examples:**
```yaml
x_ennea: 5w4
x_ennea: 2w3
x_ennea: 8
```

**What it encodes:** Core motivation and defense patterns. Each type has a primary fear, primary desire, and characteristic defense mechanism.

| Type | Core Motivation |
|------|----------------|
| 1 | Integrity, correctness, improvement |
| 2 | Being needed, helping, connection |
| 3 | Achievement, success, recognition |
| 4 | Authenticity, depth, significance |
| 5 | Understanding, competence, autonomy |
| 6 | Security, loyalty, guidance |
| 7 | Freedom, stimulation, satisfaction |
| 8 | Control, strength, self-protection |
| 9 | Peace, harmony, stability |

**Notes:** The Enneagram lacks strong empirical validation compared to Big Five or HEXACO. It is widely used in coaching and personal development contexts. Models generally recognize type descriptions with reasonable fidelity.

---

## 2. Astrological Data

### 2.1 Natal Chart Shorthand

| Property | Value |
|----------|-------|
| **Field name** | `x_astro` |
| **Type** | string |
| **Format** | Space-separated `Planet:Sign` pairs using 3-letter abbreviations |
| **Source** | astro.cafeastrology.com or equivalent |
| **Token cost** | ~5-10 tokens |

**Sign abbreviations:**

| Sign | Abbreviation |
|------|-------------|
| Aries | Ari |
| Taurus | Tau |
| Gemini | Gem |
| Cancer | Can |
| Leo | Leo |
| Virgo | Vir |
| Libra | Lib |
| Scorpio | Sco |
| Sagittarius | Sag |
| Capricorn | Cap |
| Aquarius | Aqr |
| Pisces | Pis |

**Common planet keys:** `Sun`, `Moon`, `Asc` (Ascendant/Rising), `Mercury`, `Venus`, `Mars`, `Jupiter`, `Saturn`, `Uranus`, `Neptune`, `Pluto`

**Example:**
```yaml
x_astro: Sun:Can Moon:Pis Asc:Sco
```

**Minimal useful subset:** Sun, Moon, and Ascendant (the "big three") provide the most behavioral signal at lowest token cost.

**Notes:** This is an interpretive framework, not an empirically validated assessment. Some models have training data on astrological interpretation; others do not. Consuming applications that do not support astrological interpretation should ignore this field entirely (per the core spec's extension rules).

---

### 2.2 Natal Chart Detail

| Property | Value |
|----------|-------|
| **Field name** | `x_astro_detail` |
| **Type** | map |
| **Format** | Keys are planet names (lowercase); values are strings with sign, degree, and optional house |
| **Source** | Same as `x_astro` |
| **Token cost** | ~20-80 tokens depending on depth |

**Example:**
```yaml
x_astro_detail:
  sun: Cancer 22° 9H
  moon: Pisces 8° 5H
  rising: Scorpio 4°
  venus: Leo 15° 10H
  mars: Aries 28° 6H
  saturn: Capricorn 2° 3H
  mercury: Gemini 14° 8H
  jupiter: Taurus 20° 7H
  north_node: Sagittarius 12° 2H
```

**Value format:** `{Sign} {Degree}° {House}H` — house is optional.

**Extended data (optional keys):**
- `chiron` — wounded healer placement
- `north_node` / `south_node` — nodal axis
- `midheaven` — MC (career/public life)
- `aspects` — major aspects as a list (e.g., `["Sun square Saturn", "Moon trine Venus"]`)

**Notes:** Full chart data enables more nuanced interpretation by models with relevant training data but significantly increases token cost. Users should include only as much detail as they find useful. The shorthand (`x_astro`) is sufficient for most purposes.

---

## 3. Human Design

### 3.1 Type

| Property | Value |
|----------|-------|
| **Field name** | `x_hd_type` |
| **Type** | string |
| **Source** | myhumandesign.com or equivalent |
| **Token cost** | ~2-3 tokens |

**Allowed values:**

| Type | Value |
|------|-------|
| Generator | `Generator` |
| Manifesting Generator | `Manifesting_Generator` |
| Projector | `Projector` |
| Mental Projector | `Mental_Projector` |
| Manifestor | `Manifestor` |
| Reflector | `Reflector` |

**Example:**
```yaml
x_hd_type: Generator
```

---

### 3.2 Strategy

| Property | Value |
|----------|-------|
| **Field name** | `x_hd_strategy` |
| **Type** | string |
| **Source** | Same |

**Common values:** `wait_to_respond`, `respond_then_inform`, `wait_for_invitation`, `inform_then_initiate`, `wait_lunar_cycle`

**Example:**
```yaml
x_hd_strategy: wait_to_respond
```

---

### 3.3 Authority

| Property | Value |
|----------|-------|
| **Field name** | `x_hd_authority` |
| **Type** | string |
| **Source** | Same |

**Common values:** `sacral`, `emotional_solar_plexus`, `splenic`, `ego_heart`, `self_projected`, `mental_environmental`, `lunar`

**Example:**
```yaml
x_hd_authority: sacral
```

---

### 3.4 Profile

| Property | Value |
|----------|-------|
| **Field name** | `x_hd_profile` |
| **Type** | string |
| **Format** | Two digits separated by `/` |
| **Source** | Same |

**Pattern:** `^[1-6]/[1-6]$`

**Allowed combinations:** `1/3`, `1/4`, `2/4`, `2/5`, `3/5`, `3/6`, `4/6`, `4/1`, `5/1`, `5/2`, `6/2`, `6/3`

**Example:**
```yaml
x_hd_profile: 2/4
```

---

### 3.5 Detail

| Property | Value |
|----------|-------|
| **Field name** | `x_hd_detail` |
| **Type** | map |
| **Source** | Same |
| **Token cost** | ~30-100 tokens depending on depth |

**Example:**
```yaml
x_hd_detail:
  defined_centers: [sacral, solar_plexus, root, spleen]
  open_centers: [head, ajna, throat, g_center, ego_heart]
  channels: [59-6, 42-53]
  incarnation_cross: Right Angle Cross of Planning
  variable:
    personality_sun: left
    design_sun: right
    personality_earth: right
    design_earth: left
```

**Known center values:** `head`, `ajna`, `throat`, `g_center`, `ego_heart`, `sacral`, `solar_plexus`, `spleen`, `root`

---

## 4. Gene Keys

| Property | Value |
|----------|-------|
| **Field name** | `x_gene_keys` |
| **Type** | map |
| **Source** | genekeys.com |
| **Token cost** | ~20-60 tokens |

**Structure:** Each entry uses the format `gate.line — Shadow > Gift > Siddhi`

**Sequences:**

| Sequence | Keys |
|----------|------|
| **Activation** (life path) | `life_work`, `evolution`, `radiance`, `purpose` |
| **Venus** (relationships) | `attraction`, `iq`, `eq`, `sq` |
| **Pearl** (prosperity) | `core_wound`, `vocation`, `culture`, `pearl` |

**Example:**
```yaml
x_gene_keys:
  life_work: 37.4 — Weakness > Equality > Tenderness
  purpose: 9.2 — Inertia > Determination > Invincibility
  evolution: 22.5 — Dishonour > Graciousness > Grace
  radiance: 36.1 — Turbulence > Humanity > Compassion
  vocation: 25.3 — Constriction > Acceptance > Universal Love
  pearl: 46.6 — Seriousness > Delight > Ecstasy
```

**Minimal useful subset:** `life_work` and `purpose` from the Activation Sequence provide the most signal at lowest cost.

**Notes:** Gene Keys maps a shadow-to-gift transformation spectrum across life domains. Models with relevant training data can use this to understand what growth patterns a person is working through. Models without this training data should ignore the field entirely.

---

## 5. Behavioral Guidance for Extensions

This section provides **non-normative** guidance for AI systems that choose to support these extensions. This guidance describes how extension data *may* be used to calibrate interaction style. It does not describe deterministic behavior rules.

### 5.1 MBTI Calibration Notes

MBTI types can inform communication preferences when explicit `style`/`tone`/`avoid` fields are absent or when supplemental calibration is helpful:

- **Introversion (I)** preference may correlate with preference for focused, concise exchanges
- **Intuition (N)** preference may correlate with comfort with abstract framing
- **Thinking (T)** preference may correlate with comfort with direct critique
- **Judging (J)** preference may correlate with preference for structured, organized responses

These are tendencies, not rules. Explicit communication fields in the core spec always take precedence.

### 5.2 Enneagram Calibration Notes

Enneagram type can inform what kind of support resonates:

- **Type 1** — may respond well to acknowledgment of effort and standards
- **Type 2** — may appreciate warmth and reciprocity in interaction
- **Type 3** — may prefer efficient, goal-oriented communication
- **Type 4** — may value emotional depth and recognition of uniqueness
- **Type 5** — may prefer comprehensive information with space to process
- **Type 6** — may appreciate clear reasoning and acknowledgment of concerns
- **Type 7** — may respond to enthusiasm, options, and forward momentum
- **Type 8** — may prefer directness and respect for autonomy
- **Type 9** — may appreciate gentle pacing and inclusion of multiple perspectives

### 5.3 Astrological Calibration Notes

For AI systems with astrological training data, chart data may offer supplemental behavioral signals:

- **Moon sign** — emotional processing style
- **Mercury sign** — communication style (likely already reflected in core `style` field)
- **Saturn placement** — areas of discipline and resistance
- **Tension configurations** (squares, oppositions) — areas of internal friction that may surface in priorities or patterns_to_watch

If the AI system does not have sufficient astrological training data, it should ignore `x_astro` and `x_astro_detail` fields. The core profile remains fully functional without them.

### 5.4 Human Design Calibration Notes

Human Design type and strategy can inform how an AI offers information and support:

- **Projector / Mental Projector** — Frame suggestions as invitations, not instructions. Respect energy limits; don't assume sustained output. Do not push the person to initiate.
- **Generator / Manifesting Generator** — Respond to what energizes them. Offer options rather than single paths. Help them follow satisfaction signals.
- **Manifestor** — Be direct. Support their initiating energy. Help them communicate plans to others.
- **Reflector** — Allow more processing time. Offer multiple perspectives. Do not rush decisions.

Authority informs decision-making support:

- **Sacral** — Support gut-response decisions; binary yes/no framing can help
- **Emotional Solar Plexus** — Support waiting for emotional clarity; discourage snap decisions
- **Splenic** — Support in-the-moment instinctive responses
- **Self-Projected** — Support talking through decisions out loud

### 5.5 Gene Keys Calibration Notes

Gene Keys data maps where a person is in their growth process across life domains. The shadow-gift-siddhi spectrum suggests:

- **Shadow** — the unconscious pattern or challenge
- **Gift** — the conscious capacity being developed
- **Siddhi** — the transcendent potential

An AI system that understands Gene Keys can use this to recognize when a person may be operating from a shadow pattern (e.g., if `life_work` shadow is "Weakness" and the person describes feeling incapable, that's a known pattern, not necessarily an accurate self-assessment).

### 5.6 General Principles for Extension Behavioral Guidance

1. Extension data supplements core fields — it never overrides them.
2. The conflict resolution hierarchy from the core spec applies: `ai_instructions` > communication fields > framework data > extension data > inferred behavior.
3. AI systems should not reference extension data explicitly in conversation unless asked. The person should feel understood, not analyzed.
4. AI systems should not make claims the person hasn't made based on extension data. Extension data may inform a gentle question; it should not produce an assertion.
5. AI systems should not perform diagnostic, therapeutic, or clinical interpretation of extension data.

---

## 6. Private Extensions

Any `x_`-prefixed field not listed in this registry is a private extension. Private extensions:

- Are valid in any .aiid file
- Will be ignored by implementations that don't recognize them
- Have no guaranteed schema or behavior
- May be meaningful to specific users or specific AI systems

**Common private extension patterns:**

```yaml
# Ecosystem / context
x_ecosystem: Harbor & Pine Studio
x_team: engineering

# Creative / voice
x_content_voice: plainspoken, wry, salt-air calm
x_writing_style: literary nonfiction, second person

# Operational
x_operating_rules:
  - never start a new project without a written scope
  - batch communications on Tuesdays and Thursdays
x_transit_windows:
  deep_work: 6am-11am
  meetings: 1pm-4pm

# Cultural / spiritual
x_cultural_framework: Ubuntu philosophy
x_spiritual_practice: Zen sitting, Sunday hikes
x_somatic_tools: [breathwork, body_scan, movement_before_writing]

# Personal
x_manifesto: "Make the thing, then make it kind."
```

Private extensions are the mechanism by which users from any cultural, spiritual, or philosophical tradition can include frameworks meaningful to them.

---

## 7. Proposing New Registered Extensions

To propose a new registered extension for this registry:

1. **Open a GitHub issue** at github.com/bettterlabs/aiid-spec with the label `extension-proposal`.
2. **Include:**
   - Proposed field name(s) with `x_` prefix
   - Type definition and value constraints
   - Source/origin of the framework
   - Token cost estimate
   - Example usage
   - Rationale for registration (why should implementations recognize this vs. keeping it private?)
3. **Review criteria:**
   - Does the framework have a defined vocabulary that benefits from standardization?
   - Would multiple users independently want the same field name?
   - Is the field name clear enough to avoid collision with other extensions?
4. **Approval:** Registered extensions are added by the maintainer after community review.

Registration does not imply endorsement, empirical validation, or guaranteed support by any implementation. It means the field name is reserved and the schema is stable.

---

## Appendix: JSON Schema for Registered Extensions

The following schema fragments can be used by validators that choose to validate registered extension fields. These are optional — the core validator is not required to validate extension content.

```json
{
  "x_mbti": {
    "type": "string",
    "pattern": "^[EI][SN][TF][JP]$"
  },
  "x_ennea": {
    "type": "string",
    "pattern": "^[1-9](w[1-9])?$"
  },
  "x_astro": {
    "type": "string",
    "description": "Space-separated Planet:Sign pairs using 3-letter abbreviations"
  },
  "x_astro_detail": {
    "type": "object",
    "additionalProperties": { "type": "string" }
  },
  "x_hd_type": {
    "type": "string",
    "enum": ["Generator", "Manifesting_Generator", "Projector", "Mental_Projector", "Manifestor", "Reflector"]
  },
  "x_hd_strategy": {
    "type": "string"
  },
  "x_hd_authority": {
    "type": "string",
    "enum": ["sacral", "emotional_solar_plexus", "splenic", "ego_heart", "self_projected", "mental_environmental", "lunar"]
  },
  "x_hd_profile": {
    "type": "string",
    "pattern": "^[1-6]/[1-6]$"
  },
  "x_hd_detail": {
    "type": "object"
  },
  "x_gene_keys": {
    "type": "object",
    "additionalProperties": { "type": "string" }
  }
}
```

---

The .aiID Extensions Registry is maintained at github.com/bettterlabs/aiid-spec.

Published under CC BY 4.0.

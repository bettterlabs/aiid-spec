# .aiID Creator Guide

**Version:** 0.9 (Community Draft)  
**Companion to:** .aiID Core Profile Format v1.0  
**Date:** March 29, 2026  
**License:** CC BY 4.0

---

## Purpose

This guide helps people create their .aiid file — the portable identity document that gives AI systems immediate context about who they are. It covers three creation paths:

1. **Guided conversation** — Use the model-neutral creation prompt (Appendix A) with any AI to be walked through the process
2. **Self-directed** — Use the starter template (Appendix B) and fill it in by hand
3. **Assessment-first** — Take the recommended assessments, then use either path above

No path is better than another. A 20-line file written in five minutes is fully valid. A 200-line file built over an hour-long conversation is equally valid. The file should reflect you — not an arbitrary completeness target.

---

## Table of Contents

1. Before You Start
2. The Three Compass Questions
3. Assessment Intake
4. The Guided Conversation Flow
5. Editing and Updating Your File
6. Sharing and Privacy
7. Quick Start (5-Minute Path)
Appendix A: Model-Neutral Creation Prompt
Appendix B: Starter Template
Appendix C: Assessment Links and Timing

---

## 1. Before You Start

### 1.1 What a .aiid File Is

A .aiid file is a structured text file that tells any AI system how to communicate with you, what you're working on, and what matters to you. It's written in YAML — a simple format that looks like a list of labels and values. You don't need to know anything about YAML to create one.

### 1.2 What It's For

Every AI conversation starts from zero. The model doesn't know how you think, what you're building, or how you want to be spoken to. A .aiid file solves this — you share it once and the AI adapts immediately.

### 1.3 What It's Not

- It's not a résumé or social profile. It's optimized for how AI talks to you, not how humans evaluate you.
- It's not permanent. You should update it as your priorities and situation change.
- It's not required to be complete. A file with just your name and communication preferences is fully valid and immediately useful.
- It's not a diagnostic tool. The personality data is self-reported context, not clinical assessment.

### 1.4 Who Owns It

You do. Completely. No platform, company, or AI system has any claim to it. You decide what goes in, what stays out, and who sees it.

---

## 2. The Three Compass Questions

Beyond framework data and preferences, three questions surface the information that matters most to how AI can actually help you. These questions are not stored as raw answers — they're used to populate the highest-impact fields in your file: `priorities`, `boundaries`, `patterns_to_watch`, `ai_instructions`, and `narrative`.

### Question 1 — The Future Self

> "If the only person you were building for was yourself in ten years, what would you want your life to look like?"

**What it surfaces:** Real values. Actual priorities. What you want when you stop performing for others. It strips away "should" and reveals "want."

**What it populates:** `priorities`, `goals_long`, `core` values, `narrative`.

**Why it matters for AI:** Knowing your real priorities means the AI can contextualize everything it helps you with. If your ten-year vision centers on creative work but your day is consumed by operations, that gap is information the AI needs.

### Question 2 — The Avoidance

> "What are you not doing — or not building — that you know matters, and why?"

**What it surfaces:** Friction. Patterns. The gap between who you are and how you're living. The thing you need AI to gently hold you accountable to.

**What it populates:** `patterns_to_watch`, `boundaries`, `ai_instructions`.

**Why it matters for AI:** Personality frameworks tell an AI what you're like. This question tells it what to actually do — which might be to ask "does this pass your expression test?" before helping you build yet another thing that isn't the thing.

### Question 3 — The Daily Design

> "If your daily life was designed to serve those two answers, what would change about how you spend your time, energy, and attention?"

**What it surfaces:** The gap between vision and reality. Where boundaries need to be. What "support" means in practice — not abstract, but concrete.

**What it populates:** `boundaries`, `priorities`, `goals_short`, `ai_instructions`.

**Why it matters for AI:** This is where generic advice becomes specific. If you need your mornings protected for writing, the AI should know that before suggesting a 9am brainstorm.

### Why These Questions Matter

Knowing that someone scores high on Openness and has an anxious attachment style tells an AI what they're like. Knowing that they keep starting new projects to avoid finishing the one with their name on it tells the AI what to actually do. The highest-value .aiid files contain both: the framework data and the self-knowledge that comes from honest reflection.

---

## 3. Assessment Intake

### 3.1 Core Assessments (Recommended)

These provide the empirical backbone of your file. You don't need all of them — or any of them — but richer input produces a more useful file.

| Assessment | Time | What You Get | Link |
|------------|------|-------------|------|
| Big Five Personality | 15-20 min | Five personality dimensions + 30 facets | bigfive-test.com |
| HEXACO Personality | 15-25 min | Six personality dimensions (adds Honesty-Humility) | hexaco.org |
| VIA Character Strengths | 15 min | 24 strengths ranked | viacharacter.org |
| Attachment Style | 5-10 min | Relational attachment pattern | attachmentproject.com |

**Note:** Big Five and HEXACO overlap significantly (they measure similar dimensions). You don't need both — either one is sufficient. HEXACO adds Honesty-Humility as a sixth factor. Choose whichever resonates or take both if you want maximum data.

### 3.2 Extension Assessments (Optional)

These are supported through the extension system. Include them if you find them meaningful.

| Assessment | Time | Extension Field |
|------------|------|----------------|
| MBTI | 15-20 min | `x_mbti` |
| Enneagram | 10-15 min | `x_ennea` |
| Natal Chart | 5 min (need birth time/place) | `x_astro` |
| Human Design | 2 min (need birth time/place) | `x_hd_*` |
| Gene Keys | 2 min (need birth date) | `x_gene_keys` |

### 3.3 When to Take Assessments

**Before creating your file:** If you want the richest possible file, take the core assessments first and have results ready. The Big Five is the single highest-value assessment — if you only take one, take that.

**After creating your file:** You can always create a file with just communication preferences and priorities, then add assessment data later. The file is designed to be edited.

**Never:** That's fine too. A file without any assessment data is fully valid. Communication preferences and priorities have the highest behavioral impact per token anyway.

### 3.4 How to Record Assessment Results

**Big Five:** Record as five numbers (0-100) in order: Openness / Conscientiousness / Extraversion / Agreeableness / Neuroticism. Example: `OCEAN: 91/82/78/78/39`

If your test gives you facet-level scores (six facets per domain), compute the domain score: `(sum of facet scores / maximum possible sum) × 100`. Most tests use facets scored 1-20, so maximum per domain is 120.

**HEXACO:** Record as six numbers (0-100) in order: Honesty-Humility / Emotionality / Extraversion / Agreeableness / Conscientiousness / Openness. Example: `HEXACO: 78/45/82/65/70/91`

**VIA:** Record your top 5 strengths in ranked order. Optionally record your bottom 3.

**Attachment:** Record one of: `secure`, `anxious_preoccupied`, `dismissive_avoidant`, `fearful_avoidant`, `earned_secure`.

---

## 4. The Guided Conversation Flow

If you use the model-neutral creation prompt (Appendix A), the AI will walk you through a three-phase conversation. Here's what to expect.

### Phase 1 — Framework Intake (~5 minutes)

The AI asks whether you've completed any assessments. For each one you have:
- Paste your results
- The AI parses them into the correct format

For assessments you haven't taken, the AI provides links and you can choose to take them now, take them later, or skip them entirely.

### Phase 2 — The Three Compass Questions (~10-15 minutes)

The AI asks the three questions one at a time, with follow-up questions that go deeper based on your answers. This is the heart of the experience.

**Tips for this phase:**
- Be honest. The AI isn't judging you and no one else will see your answers unless you share the final file.
- Don't perform. Say what you actually want, not what sounds good.
- Take your time. The questions are designed to surface things you might not have articulated before.
- If a question doesn't resonate, say so. The AI will rephrase or move on.

### Phase 3 — Structured Interview (~10-15 minutes)

The AI asks 15-20 additional questions, one at a time, covering:

- What you do and what you're building
- Your communication preferences (how you like to be spoken to)
- What drains you and what energizes you
- How you make decisions
- Your work rhythm and energy patterns
- What kind of support you actually need from AI
- What patterns you want AI to help you watch for
- How you learn best
- What you value most
- What you want AI to never do

### Phase 3.5 — Review

The AI generates your .aiid file and presents it for review. It specifically calls attention to the `ai_instructions` section: "Based on everything you've told me, here's how I'd suggest AI systems interact with you. Does this feel right?"

This moment — reading your own identity file and feeling recognized — is the point. If something feels off, edit it. If something's missing, add it. The file is yours.

---

## 5. Editing and Updating Your File

### 5.1 When to Update

- **Priorities change:** New job, new project, new phase of life → update `priorities`, `goals_short`, `boundaries`
- **You learn something about yourself:** Took a new assessment, realized a pattern → add the data
- **Something feels off:** If AI interactions feel miscalibrated, check if your file still reflects who you are now
- **Every 3-6 months:** Set a reminder. Even a quick review keeps the file useful.

Always update the `updated` field when you edit: `updated: "2026-03-29"`

### 5.2 How to Edit

The file is plain text. Open it in any text editor (TextEdit, Notepad, VS Code, even your phone's notes app). YAML syntax is simple:

```yaml
# This is a comment (ignored by parsers)
field_name: value
list_field:
  - item one
  - item two
multiline_field: |
  This is a longer block of text
  that spans multiple lines.
```

**Rules to remember:**
- Indent with spaces, not tabs
- Quote dates: `updated: "2026-03-29"` (not `updated: 2026-03-29`)
- Lists use `- ` (dash space) or `[item1, item2]`
- Don't duplicate field names

### 5.3 Versioning

Track your own updates with `profile_version`:

```yaml
aiid_version: "1.0"
profile_version: "3"
updated: "2026-03-29"
```

This helps you (and AI systems reading the file) understand how evolved the file is.

---

## 6. Sharing and Privacy

### 6.1 What to Think About Before Sharing

Your .aiid file can contain sensitive information. Before sharing it in any context, consider:

- **Who will see it?** Pasting into a system prompt means the AI platform processes it. Uploading to a public repo means anyone can read it.
- **What's in it?** Fields like `attachment`, `neurodivergence`, `patterns_to_watch`, and `narrative` are classified as Sensitive in the spec.
- **Do you need the full file here?** A work context might only need your communication preferences and priorities. A creative project might only need your style and thinking preferences.

### 6.2 Redaction Profiles

You can maintain different versions for different contexts:

**Public version** (safe for broad sharing):
```yaml
aiid_version: "1.0"
display_name: Alex
role: product designer
style: direct, visual, concise
avoid: [jargon, filler]
thinking: systems, first_principles
```

**Professional version** (for work contexts):
Add `name`, `priorities`, `boundaries`, `ai_instructions`. Omit `attachment`, `neurodivergence`, `patterns_to_watch`, `narrative`.

**Full version** (for personal AI use):
Everything you want to include.

### 6.3 Pseudonymous Profiles

You don't have to use your real name. A file with `display_name: "nightowl"` and communication preferences is fully valid. Use this for contexts where you want the behavioral benefits without the identification.

---

## 7. Quick Start (5-Minute Path)

If you want a working .aiid file in five minutes without assessments or guided conversation:

1. Copy the starter template (Appendix B)
2. Fill in: your name, what you do, how you like to be communicated with, what you're working on, and one instruction for AI
3. Save as `yourname.aiid`
4. Paste it into your next AI conversation's system prompt or upload it as a file

That's it. You can always come back and add depth later.

---

## Appendix A: Model-Neutral Creation Prompt

Copy and paste the following prompt into any AI system (ChatGPT, Claude, Gemini, Grok, or any model that accepts system-level or user-level instructions) to be guided through creating your .aiid file.

---

```
You are an .aiID creation assistant. Your job is to guide me through creating my .aiid file — a portable identity document that tells AI systems how to communicate with me, what I'm working on, and what matters to me.

The .aiid format is a YAML file conforming to the .aiID Core Profile Format v1.0. The file I create will be used as context in future AI conversations across any platform.

CONDUCT THIS AS A CONVERSATION, NOT A FORM. Ask one question at a time. Follow up on interesting answers. Be warm but efficient. The goal is for me to feel seen and understood, not interrogated.

Here is your process:

PHASE 1 — FRAMEWORK INTAKE
Ask me if I have results from any of these assessments. For each one I have, ask me to paste the results and parse them into the correct .aiid format. For ones I haven't taken, briefly explain what they measure and provide the link. Don't pressure me — any combination is fine, including none.

Core assessments:
- Big Five Personality (bigfive-test.com) → OCEAN: O/C/E/A/N as integers 0-100
- HEXACO Personality (hexaco.org) → HEXACO: H/E/X/A/C/O as integers 0-100
- VIA Character Strengths (viacharacter.org) → VIA_top5: [top 5 ranked]
- Attachment Style (attachmentproject.com) → attachment: one of secure, anxious_preoccupied, dismissive_avoidant, fearful_avoidant, earned_secure

Extension assessments (optional, included as x_ fields):
- MBTI → x_mbti: four-letter type
- Enneagram → x_ennea: type and wing (e.g. 5w4)
- Natal Chart (astro.cafeastrology.com) → x_astro: Sun:Sign Moon:Sign Asc:Sign
- Human Design (myhumandesign.com) → x_hd_type, x_hd_strategy, x_hd_authority, x_hd_profile
- Gene Keys (genekeys.com) → x_gene_keys: gate.line — Shadow > Gift > Siddhi

After intake, transition naturally to Phase 2.

PHASE 2 — THE THREE COMPASS QUESTIONS
Ask these three questions ONE AT A TIME. After each answer, ask 1-2 follow-up questions to go deeper. Don't rush. These surface the most important information in the file.

Question 1 — The Future Self
"If the only person you were building for was yourself in ten years, what would you want your life to look like?"
(Surfaces: real values, actual priorities, what they want vs. what they think they should want)

Question 2 — The Avoidance
"What are you not doing — or not building — that you know matters, and why?"
(Surfaces: friction, patterns, the gap between identity and action)

Question 3 — The Daily Design
"If your daily life was designed to serve those two answers, what would change about how you spend your time, energy, and attention?"
(Surfaces: where boundaries need to be, what support means in practice)

PHASE 3 — STRUCTURED INTERVIEW
Ask the following questions ONE AT A TIME. Adapt based on what you already know from Phases 1-2. Skip questions already answered. Ask follow-ups where interesting.

1. What do you do? (role, profession, creative work)
2. What are you actively building or working on right now? (priorities)
3. How do you prefer to be communicated with? (style: direct? warm? formal? casual?)
4. What should AI never do when talking to you? (avoid list)
5. What's your preferred response format? (prose? structured? concise? detailed?)
6. What kind of humor do you like, if any?
7. How do you think through problems? (first principles? narrative? visual? systems?)
8. How do you learn best? (frameworks first? examples? hands-on?)
9. How do you make decisions? (data? intuition? both? slow? fast?)
10. What are your core values? (the 3-5 things that are non-negotiable)
11. What are your current boundaries? (things you're protecting right now)
12. What patterns do you want AI to watch for? (overcommitting? avoidance? perfectionism?)
13. What drains your energy? What energizes you?
14. What does your ideal work rhythm look like?
15. Is there anything about how your brain works that's relevant? (neurodivergence, processing style)
16. What do you want AI to actually DO for you? What kind of help do you need?
17. Anything else that matters about who you are that we haven't covered?

PHASE 4 — GENERATION
Generate the complete .aiid file based on everything discussed. Follow these rules:

1. Start with: # .aiid v1.0
2. aiid_version: "1.0" is REQUIRED
3. Include display_name (or name). Both are fine.
4. Quote all dates: updated: "YYYY-MM-DD"
5. Place communication fields (style, tone, avoid) early — they have the highest behavioral impact.
6. Place extension fields (x_mbti, x_ennea, x_astro, x_hd_*, x_gene_keys) at the end with a comment marker: # --- EXTENSIONS ---
7. Write ai_instructions in my voice, based on everything I said. These should feel like MY words, not a summary. They should capture how I actually want AI to interact with me.
8. Write narrative (if included) in my voice — 2-5 sentences that capture who I am.
9. Only include fields I provided data for. Don't invent or assume.
10. Don't include empty fields.

Present the file and specifically ask: "Read through the ai_instructions section — does this feel like how you'd actually want AI to talk to you? Anything to add, change, or remove?"

Let me revise until it feels right. Then tell me to save it as a .aiid file and explain that I can paste it into any AI system's instructions or upload it as a file.
```

---

## Appendix B: Starter Template

Copy this template, fill in what you know, delete what you don't, and save as `yourname.aiid`.

```yaml
# .aiid v1.0
aiid_version: "1.0"
updated: "2026-03-29"

# --- IDENTITY ---
display_name: 
role: 

# --- COMMUNICATION ---
# These are the highest-impact fields. Start here.
style:                    # e.g. direct, warm, depth-first, casual, formal
tone:                     # e.g. warm_precise, casual, professional, playful
avoid:                    # e.g. [hedging, filler, platitudes, unsolicited_advice]
# format_pref:            # e.g. prose, structured, concise, detailed
# humor:                  # e.g. dry_wit, playful, none, dark

# --- COGNITION ---
# thinking:               # e.g. systems, first_principles, narrative, visual
# learning:               # e.g. frameworks_first, examples_first, hands_on
# deciding:               # e.g. data_plus_intuition, gut_first, deliberate

# --- PERSONALITY (if you have assessment results) ---
# OCEAN: 00/00/00/00/00   # bigfive-test.com — O/C/E/A/N, each 0-100
# HEXACO: 00/00/00/00/00/00  # hexaco.org — H/E/X/A/C/O, each 0-100
# VIA_top5: []             # viacharacter.org
# attachment:              # attachmentproject.com — secure, anxious_preoccupied, etc.

# --- VALUES ---
# core: []                 # your 3-5 non-negotiable values

# --- CURRENT FOCUS ---
priorities:
  - 
  - 
# boundaries:
#   - 
# goals_short:
#   - 
# patterns_to_watch:
#   - 

# --- AI INSTRUCTIONS ---
# In your own words: how do you want AI to interact with you?
ai_instructions: |
  

# --- EXTENSIONS (optional) ---
# x_mbti: 
# x_ennea: 
# x_astro: Sun:___ Moon:___ Asc:___
# x_hd_type: 
# x_hd_strategy: 
# x_hd_authority: 
```

### How to Use This Template

1. **Required:** Fill in `display_name` (your preferred name) and at least one communication field (`style`, `tone`, or `avoid`).
2. **Recommended:** Fill in `priorities` and `ai_instructions`. These make the file immediately useful.
3. **Optional:** Everything else. Uncomment lines by removing the `#` at the start. Delete sections you don't want.
4. **Save** as `yourname.aiid` (e.g., `alex.aiid`).
5. **Use** by pasting the contents into any AI system's custom instructions, system prompt, or uploading as a file.

---

## Appendix C: Assessment Links and Timing

| Assessment | Link | Time | What You Get | .aiid Field |
|------------|------|------|-------------|-------------|
| Big Five Personality | bigfive-test.com | 15-20 min | 5 dimensions + 30 facets | `OCEAN` |
| HEXACO Personality | hexaco.org | 15-25 min | 6 dimensions | `HEXACO` |
| VIA Character Strengths | viacharacter.org | 15 min | 24 strengths ranked | `VIA_top5` |
| Attachment Style | attachmentproject.com | 5-10 min | Relational pattern | `attachment` |
| MBTI | various | 15-20 min | 4-letter type | `x_mbti` |
| Enneagram | various | 10-15 min | Type + wing | `x_ennea` |
| Natal Chart | astro.cafeastrology.com | 5 min | Planetary positions | `x_astro` |
| Human Design | myhumandesign.com | 2 min | Type, strategy, authority | `x_hd_*` |
| Gene Keys | genekeys.com | 2 min | Hologenetic profile | `x_gene_keys` |

**If you only take one:** Big Five. It has the broadest empirical grounding and the highest recognition across AI models.

**If you take two:** Big Five + VIA. Personality traits + character strengths with almost no overlap.

**If you take three:** Big Five + VIA + Attachment. Covers who you are, what you're strong at, and how you relate.

**Total time for all core assessments:** ~50-70 minutes. You can spread this across days.

---

The .aiID Creator Guide is maintained at github.com/bettterlabs/aiid-spec.

Published under CC BY 4.0.

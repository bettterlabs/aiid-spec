# The .aiID White Paper

## Portable AI Identity: An Open Standard for Human-AI Communication

**Author:** Derrius Logan Casey  
**Date:** March 2026  
**Version:** 1.0  
**License:** CC BY 4.0

---

## The Starting-from-Zero Problem

Every conversation with an AI begins the same way: as strangers.

The model knows nothing about the person typing. Not how they think. Not how they communicate. Not what they're building. Not what matters to them. The first several exchanges in any new conversation are spent re-establishing context that the person has explained dozens of times before — their role, their communication preferences, their current priorities, what kind of help they actually need.

This is not a minor friction. It's a structural failure in how humans and AI systems interact.

A person who uses AI seriously — across work, creative projects, decision-making, personal development — may start fifty or more new conversations per week across multiple platforms. Each one begins at zero. Each one requires the person to re-teach the system who they are. The cumulative cost is measured in hours of redundant context-setting, in responses that miss the mark because the model doesn't know the person prefers directness over diplomacy, or that they're a visual thinker, or that they have a book deadline in six weeks.

The problem compounds across platforms. A person who has spent months building rich context with ChatGPT starts from zero when they switch to Claude. A developer who has carefully configured a CLAUDE.md file for their coding workflow has no way to carry those preferences to Gemini. Every platform builds its own memory silo, optimized for retention within its own ecosystem, with no mechanism for the person to own, control, or port their identity context elsewhere.

This is the starting-from-zero problem, and it affects every person who interacts with AI.

---

## Why the Platforms Won't Solve This

The major AI platforms — OpenAI, Anthropic, Google, xAI — all have strong incentives to build persistent user context within their own ecosystems. ChatGPT has Memory. Claude has Memory. Gemini has personalization. Each of these is a step forward within its own walls.

But portability is not in their commercial interest. Platform-locked memory is a retention mechanism. The more context a user builds within one system, the higher the switching cost to leave. A person who has spent six months training ChatGPT Memory to understand their communication style, their projects, and their patterns faces the prospect of starting over entirely if they want to try Claude. This lock-in is not accidental — it's the natural consequence of building memory as a platform feature rather than a user-owned format.

The history of technology standards shows that this pattern resolves in one of two ways: either a dominant platform becomes the de facto standard (VHS, Windows, iOS), or an open format emerges that gives users control and forces platforms to interoperate (email, HTML, RSS, USB, PDF). The first path concentrates power. The second distributes it.

The .aiID format is a bet on the second path. It proposes that the most important context about a person — how they communicate, how they think, what they're building, what they need from AI — should be owned by the person, stored in a file they control, and portable across every system they use.

---

## What .aiID Is

The .aiID (AI Identity Document) is a portable, user-authored file format. It's a single text file, written in YAML, that encodes everything an AI system needs to know to interact with someone effectively from the first message.

A minimal file takes thirty seconds to write:

```yaml
# .aiid v1.0
aiid_version: "1.0"
display_name: Alex
style: direct, concise
avoid: [hedging, filler]
priorities: [shipping v2, hiring]
ai_instructions: "Skip the preamble. If I'm wrong, say so."
```

That file, pasted into any AI system's instructions or uploaded as a context file, immediately changes how the system communicates. No hedging. No filler. Direct and concise. Aware of what Alex is working on. The person goes from stranger to known in the time it takes to read seven lines of text.

A comprehensive file goes deeper — personality framework data, cognitive style, values, boundaries, patterns the person wants to be held accountable to, explicit instructions for how AI should interact with them. The format supports progressive depth: use as much or as little as you find valuable.

The key design insight is that not all personal data changes AI behavior equally. Communication preferences and explicit constraints have the highest impact per token. A single line — `avoid: [hedging, filler]` — shapes every response. Personality framework scores (Big Five, HEXACO) compactly encode behavioral tendencies that help the model calibrate its approach. Current priorities contextualize every piece of advice. Biographical details, by contrast, rarely change response quality. The format is designed around this hierarchy: highest-impact information first, lowest-impact last.

---

## The Design Philosophy

### User-owned, not platform-owned

The person who creates a .aiid file owns it completely. The file lives on their device, in their version control system, in their cloud storage — wherever they want. No platform has any claim to it. No company controls the format. The specification is open source under CC BY 4.0.

### Human-writable, machine-parseable

The file is plain text. Any text editor can open it. YAML syntax is minimal — no braces, no semicolons, no closing tags. A non-technical person can create a valid file in a text editor in ten minutes. At the same time, every programming language has YAML parsing built in. No custom parsers are needed. The format is trivially consumable by any AI system that accepts text context.

### Token-efficient

Every token consumed by an identity file displaces conversation content, tool output, or reasoning capacity. YAML's low syntactic overhead, combined with compact encodings like `OCEAN: 74/58/63/81/27` (five personality dimensions in eight tokens), means the format delivers maximum behavioral signal at minimum cost. A useful identity file can fit in 80-200 tokens. A comprehensive one rarely exceeds 800.

### Empirically grounded where possible, extensible everywhere else

The core specification includes fields for personality frameworks with strong empirical foundations: the Big Five (OCEAN), HEXACO, VIA Character Strengths, and Attachment Style. These frameworks are well-validated across populations and broadly recognized by frontier AI models.

The format also supports frameworks from any cultural, philosophical, or spiritual tradition through a flexible extension system. MBTI, Enneagram, natal charts, Human Design, Gene Keys, Ubuntu philosophy, Ikigai, somatic tools — all are valid through the `x_` extension prefix. The extension system makes no claim about the empirical status of any framework. It provides structure for encoding whatever self-knowledge the person finds meaningful.

This is a deliberate architectural choice: the core is defensible and grounded; the extensions are open and inclusive. Users lose nothing. Credibility is preserved.

---

## The Three Compass Questions

The most valuable .aiid files contain more than framework scores and preference lists. They contain self-knowledge — the kind that surfaces when someone is asked the right questions.

The .aiID creation process uses three foundational questions, each designed to populate the highest-impact fields in the file:

**Question 1 — The Future Self:** "If the only person you were building for was yourself in ten years, what would you want your life to look like?"

This strips away performance and obligation. It reveals real values and real priorities — what someone wants when they stop performing for others.

**Question 2 — The Avoidance:** "What are you not doing — or not building — that you know matters, and why?"

This surfaces friction and patterns. The gap between identity and action. The thing the AI should know in order to hold the person gently accountable.

**Question 3 — The Daily Design:** "If your daily life was designed to serve those two answers, what would change about how you spend your time, energy, and attention?"

This bridges vision and reality. Where boundaries need to be. What "help" actually means — not in the abstract, but in the concrete shape of a Tuesday afternoon.

These questions exist because personality frameworks alone are insufficient. Knowing that someone scores low on Extraversion and has an avoidant attachment style tells an AI what they're like. Knowing that they say yes to every request and then resent it tells the AI what to actually do.

---

## How It Works in Practice

A person creates their .aiid file — either by hand, using a starter template, or through a guided conversation with any AI system using the model-neutral creation prompt published alongside the specification.

They then use it in any of four ways:

**System prompt injection:** Paste the file contents into any AI's custom instructions or system prompt. This works on every platform that accepts custom instructions — ChatGPT, Claude, Gemini, Grok, open-source models, any API.

**File upload:** Upload the .aiid file at the start of a conversation. Most platforms that accept text file uploads will parse and apply it.

**Project context:** Add the file to a persistent workspace (Claude Projects, ChatGPT custom GPTs, any platform with workspace-level context). Every conversation in that workspace is informed by the identity file without re-uploading.

**API integration:** Developers building AI-powered applications can accept .aiid files from users and inject the contents into API calls, with validation and safe ingestion practices documented in the Implementation Guide.

The file is platform-agnostic. The same file works everywhere, unmodified. Behavioral outcomes vary by model — a 7-billion parameter open-source model will interpret personality data differently than GPT or Claude — but the format itself is universal.

---

## Prior Art and Differentiation

The .aiID format is not the first attempt at persistent AI context. It builds on and differentiates from several existing approaches:

**Platform memories** (ChatGPT Memory, Claude Memory) store facts derived from conversations. They're automatic and low-effort, but platform-locked, not user-controlled in structure, and not portable.

**Markdown agent files** (CLAUDE.md, AGENTS.md, GEMINI.md) provide persistent context for coding agents. They're effective in their domain but scoped to developer workflows, not personal identity.

**Continuum** offers portable AI identity using multiple Markdown files. It's the closest prior art and made thoughtful architectural choices — multi-file separation of concerns enables granular updates and selective sharing. The .aiID format trades that granularity for single-file portability and structured token efficiency.

**Memory-as-a-service tools** (Mem0, MemGPT/Letta, Zep) store individual facts with metadata, knowledge graphs, or self-managed memory systems. They're efficient for retrieval but fragmented, not portable, and not user-authored.

The .aiID format's distinctive contribution is the combination of: single-file portability, structured YAML for token efficiency, a value hierarchy that prioritizes behavioral constraints over biographical facts, empirically-grounded personality frameworks in the core with an open extension system, and a formal specification with schema validation, reference implementations, and compliance tiers.

---

## Privacy and Trust

A .aiid file can contain sensitive information: personality scores, attachment style, neurodivergence status, behavioral patterns, intimate self-description. The specification takes this seriously.

Fields are classified into three sensitivity tiers — Basic, Personal, and Sensitive — with clear guidance on which fields carry higher risk. The specification supports pseudonymous profiles (a file with `display_name: "nightowl"` and communication preferences is fully valid), redaction profiles for selective sharing (a "work" version that omits sensitive fields), and data minimization as a design principle.

The file format itself is intentionally simple and transparent. It's plain text. There's no hidden metadata, no tracking, no phone-home mechanism. What you put in the file is what's in the file. You can read every byte of it.

The specification does not make claims it cannot enforce. It does not say "no platform may store your data" — because a file format cannot control what a platform does with text it receives. Instead, it requires platforms to disclose their storage, retention, and training practices before ingesting .aiid content, and it provides a full threat model so users can make informed decisions about what to include and who to share with.

---

## The Ecosystem

The .aiID specification is published with a complete ecosystem ready for adoption:

**Core Specification** — the formal standard defining fields, validation rules, conformance requirements, security and privacy considerations, and governance.

**JSON Schema** — machine-readable validation for any programming language.

**Reference Validators** — in Python and JavaScript, both passing the full conformance suite. Two independent implementations producing matching results.

**Extensions Registry** — formal definitions for MBTI, Enneagram, astrology, Human Design, and Gene Keys extension fields, with behavioral guidance and JSON Schema fragments.

**Implementation Guide** — safe ingestion pipelines, prompt wrapping patterns, framework-specific behavioral calibration, platform integration notes, token budget planning, and redaction profiles. Everything a developer needs to build .aiid support into their application.

**Creator Guide** — including a model-neutral creation prompt that can be used in any AI system, a starter template, assessment links, and the Three Compass Questions.

**Test Vectors** — 21 valid and 15 invalid example files for conformance testing.

---

## Adoption Path

The .aiID format is designed to be useful before any platform officially adopts it. System prompt injection works today on every platform that accepts custom instructions. File upload works on most. These integration paths require zero platform cooperation — the format doesn't need permission to exist.

The adoption path has three phases:

**Phase 1 — Individual use.** A person creates their .aiid file and pastes it into their AI conversations. This delivers immediate value with zero infrastructure.

**Phase 2 — Developer integration.** Developers building AI-powered applications accept .aiid files from users, validated against the published schema, injected safely into API calls. The Implementation Guide provides everything needed for this.

**Phase 3 — Platform integration.** AI platforms recognize .aiid as a standard format for user-provided context, with native upload, persistent storage, and structured interpretation. This is the long-term goal — but the format delivers value at every phase, not just the last one.

The biggest risk is timing. The major platforms are all building toward persistent user context, and each has the resources to ship a proprietary solution faster than an open standard can achieve adoption. The addressable version of this risk is speed and community: establish the standard as a credible reference point fast enough that platform-native solutions feel like they should interoperate with .aiid rather than replace it.

---

## Why This Matters

The relationship between humans and AI is becoming persistent. People are not having one-off exchanges with chatbots anymore — they're collaborating with AI systems across creative work, decision-making, business strategy, personal development, and daily operations. The context of who someone is — how they think, what they value, what they're building, how they want to be communicated with — is the difference between AI that feels like a tool and AI that feels like a collaborator.

That context should not be locked inside any single platform. It should be owned by the person, portable across systems, and structured for maximum impact. It should be open, free, and built on a formal specification that anyone can implement.

The .aiID format is that specification. One file. Every conversation. No more starting as a stranger.

---

## Resources

- **Specification:** github.com/bettterlabs/aiid-spec
- **Core Spec:** spec/core-spec.md
- **Creator Guide:** docs/creator-guide.md
- **Implementation Guide:** docs/implementation-guide.md
- **Extensions Registry:** spec/extensions-registry.md
- **JSON Schema:** schema/aiid.schema.json
- **License:** CC BY 4.0 — open standard, free forever

---

*Created by Derrius Logan Casey. Published under CC BY 4.0.*

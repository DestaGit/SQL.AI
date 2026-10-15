# SQL.AI — Documentation Guidelines

**Audience:** Everyone who writes or reviews SQL.AI documentation: product, engineering, security, design, support and leadership
**Version:** 1.0
**Date:** 2026-10-14
**Owner:** [DOCUMENTATION OWNER NAME]

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-10-14 | [NAME] | First edition |

---

## Contents

1. Why these guidelines exist
2. The documentation set
3. Principles
4. Document structure
5. Voice and tone
6. Product terminology
7. Formatting in Markdown
8. Diagrams, screenshots and examples
9. Security, privacy and compliance in docs
10. Numbers, claims and evidence
11. Accessibility
12. Docs as code: versioning and change control
13. Review process and checklists
14. Tooling
15. Templates
16. Quick reference

---

## 1. Why these guidelines exist

SQL.AI sells trust. Our documentation is part of the product: auditors read it as evidence, customers read it to decide whether to let us near their data, and engineers rely on it to keep the gate intact. Inconsistent, vague or overstated docs undermine all three.

These guidelines make every document:
- **accurate**: it matches the product and the other documents,
- **findable**: readers know where to look,
- **readable**: plain language, consistent structure,
- **safe**: no sensitive data, no claims we can't back up,
- **maintained**: versioned, owned and reviewed.

## 2. The documentation set

| Document | File | Purpose | Owner | Required reviewers |
|---|---|---|---|---|
| README | `README.md` | Front door: what it is, how to try it, where to go next | Product | Product, Engineering |
| Product requirements | `PRD.md` | What we build and why; numbered requirements | Product | Engineering, Security, Legal |
| Model and architecture | `ARCHITECTURE.md` | How it's built; data, policy and AI models | Engineering lead | Security, Platform |
| Developer manual | `DEVELOPER_MANUAL.md` | How to build, test and operate | Engineering lead | Security for protected paths |
| User manual | `USER_MANUAL.md` | How to use SQL.AI | Product + Design | Support, Product |
| Documentation guidelines | `DOCUMENTATION_GUIDELINES.md` | This document | Docs owner | Product, Engineering |
| Investor pitch | `INVESTOR_PITCH.md` | The business case | Founders | Finance, Legal |
| Architecture decision records | `docs/adr/ADR-NNN-title.md` | One decision each | Author | Engineering lead |
| Runbooks | `docs/runbooks/<alert>.md` | What to do when an alert fires | On-call owner | SRE, Security |
| Release notes | `CHANGELOG.md` | What changed for users | Release manager | Product |
| API reference | `docs/api/` (generated) | Endpoint details | API owner | Engineering |

**One source of truth per fact.** If a fact appears in several documents (for example the list of policy rules), one document owns it and the others link to it:

| Fact | Owned by |
|---|---|
| Policy rules (IDs, names, behavior) | PRD §9 |
| Requirement IDs and priorities | PRD §8 |
| Component names and responsibilities | ARCHITECTURE §4 |
| API endpoints, errors, scopes | DEVELOPER_MANUAL §7 (generated reference wins if they differ) |
| UI labels and user-facing messages | USER_MANUAL, matching `apps/web/src/gate/rules.ts` |
| Compliance positioning | PRD §12 (approved by Legal) |

## 3. Principles

1. **Write for one reader.** Name the audience at the top. A user manual page isn't an architecture note.
2. **Lead with what the reader needs.** Answer first, background after.
3. **Plain over clever.** Short sentences, common words, active voice.
4. **Show, then tell.** An example, table or diagram beats a paragraph.
5. **Be exact.** Name the button, the rule ID, the file path, the number.
6. **Never overstate.** If it's a target, say target. If it's planned, say planned.
7. **Change docs with code.** A pull request that changes behavior updates the docs in the same PR.

## 4. Document structure

### 4.1 Header block

Every long-lived document starts with this block:

```markdown
# SQL.AI — <Document name>

**Audience:** <who it's for>
**Version:** <MAJOR.MINOR>
**Date:** <YYYY-MM-DD>
**Owner:** <name or role>
**Related:** <other documents, if helpful>
```

Documents that go through formal review (PRD, architecture, guidelines) add a **version history** table:

```markdown
| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-10-14 | <name> | First full draft |
```

### 4.2 Required sections by type

| Type | Required sections |
|---|---|
| PRD | Summary, problem, goals and non-goals, metrics, personas, scope, requirements, NFRs, release criteria, risks, open questions, glossary |
| Architecture | Purpose and scope, principles, context, containers, flows, data model, security, deployment, decisions, open questions |
| Manual | Audience, contents, task-based sections, troubleshooting, glossary, getting help |
| ADR | Context, decision, status, consequences, alternatives |
| Runbook | Alert, impact, first steps, diagnosis, resolution, escalation, follow-up |
| Release notes | Version, date, new, changed, fixed, security, breaking changes |

### 4.3 Headings

- One `#` H1 per document (the title). Sections are `##`, subsections `###`. Don't go below `####`.
- Number sections in long reference documents (`## 7. API reference`) so they can be cited ("see ARCHITECTURE §10").
- Use sentence case: "Reading the policy gate", not "Reading The Policy Gate".
- Headings are labels, not sentences. No end punctuation.
- Task headings start with a verb: "Connecting a warehouse", "Run an approved query".

### 4.4 Contents

Documents longer than about five sections include a numbered contents list after the header block.

### 4.5 Length

- Paragraphs: 1–4 sentences.
- Sentences: aim for under 25 words.
- If a section passes about 600 words, split it or add subsections.

## 5. Voice and tone

### 5.1 Voice

| Do | Don't |
|---|---|
| "Click **Run under policy**." | "The user should then proceed to click on the Run button." |
| "Your role can't read `employees`." | "Access to the requested resource has been denied due to insufficient privileges." |
| "SQL.AI masks email addresses for analysts." | "Email addresses are masked." (passive, hides who does it) |
| "The query is held until someone approves it." | "The query will be placed into a pending approval state." |

- **User docs:** second person ("you"), present tense, friendly and direct.
- **Technical docs:** neutral, precise, present tense ("The executor opens a scoped session").
- **Requirements:** "must" for mandatory, "should" for recommended, "may" for optional. Don't use "shall", "will" or "needs to" in requirements.

### 5.2 Words to avoid

| Avoid | Use instead |
|---|---|
| simply, just, easily, obviously | (delete them) |
| utilize | use |
| leverage | use |
| in order to | to |
| please note that | (delete; state the fact) |
| user-friendly, seamless, cutting-edge, world-class | describe what it actually does |
| secure (as a bare claim) | name the control: "encrypted at rest with AES-256" |
| guarantees, never fails, 100% secure | state the control and its scope |
| whitelist / blacklist | allowlist / blocklist |
| master / slave | primary / replica |
| sanity check | quick check |

### 5.3 Error and block messages

Every message tells the reader **what happened** and **what to do next**. No apologies, no blame, no codes without words.

> "Your role can't read `employees`. Ask a data admin for access."

> "The policy service is unavailable, so the query was not run. Try again in a few minutes."

## 6. Product terminology

Use these terms exactly. Consistency is how readers learn the product.

| Term | Use | Don't use |
|---|---|---|
| **SQL.AI** | Always with the period, capital SQL and AI | SQLAI, Sql.ai, SQL AI |
| **policy gate** (or **the gate**) | The checks every query passes | firewall, filter, proxy |
| **Query Gateway** | The backend service (capitalized) | gate service, API gateway (that's a different component) |
| **rule** + ID | "rule **P-06** (row-level security)" | policy P-06, check 6 |
| **policy version** | `v2`, `pv_2026-10-14.3` | ruleset, config |
| **masking** / **masked** | Hiding all or part of a value | redacting (unless the method is full redaction), obfuscating |
| **row-level security** | Filtering rows by user attributes | RLS (spell out on first use per document) |
| **small-group suppression** | Showing counts below k as `<k` | k-anonymity (not equivalent) |
| **held for approval** | A query waiting for a second person | pending, queued (in user docs) |
| **approver** | Person eligible to approve | admin (unless they are one) |
| **audit log** | The tamper-evident record | logs, history |
| **hash chain** / **chain** | The linking of audit entries | blockchain |
| **draft** | AI- or engine-written SQL before it runs | suggestion, answer |
| **data admin**, **data steward**, **security officer** | Roles, lowercase in prose | Admin, Steward (unless a UI label) |
| **warehouse** | The customer's data store | database (in user docs), DB |

UI labels are written exactly as they appear, in **bold**: **Draft SQL**, **Run under policy**, **Verify chain**, **Approvals**.

Abbreviations: spell out on first use in each document, then abbreviate: "single sign-on (SSO)".

## 7. Formatting in Markdown

We write CommonMark with GitHub-flavored extensions (tables, task lists, fenced code, Mermaid).

| Element | Rule |
|---|---|
| **Bold** | UI labels, key terms on first definition, important warnings. Not for general emphasis. |
| *Italics* | Example questions users type, titles of external works. Sparingly. |
| `Code` | File names, paths, commands, SQL keywords, column and table names, environment variables, rule IDs in technical docs. |
| Lists | Numbered for steps in order; bullets for unordered items. Parallel grammar in every item. |
| Tables | For comparisons and reference data. Always have a header row. Keep cells short. |
| Links | Descriptive text: "see [Approvals](#9-approvals)", never "click here". Relative links between repo docs. |
| Blockquotes | Callouts for notes, the north star or example messages. Prefix warnings with **Warning:**. |
| Horizontal rules | Only after the header block and before appendices. |

### 7.1 Code blocks

- Always tag the language: ` ```sql `, ` ```bash `, ` ```json `, ` ```yaml `, ` ```ts `, ` ```python `, ` ```mermaid `.
- Commands are copy-pasteable: no `$` prompts, no output mixed into the same block.
- Show output in a separate block labelled "Output:" if needed.
- SQL keywords in uppercase; identifiers in lowercase snake_case.
- Long examples: keep to what the reader needs; elide with a comment (`-- ...`) or `...`.

### 7.2 Dates, times and numbers

- Dates: ISO `YYYY-MM-DD` in technical docs and tables; "October 14, 2026" acceptable in prose for user docs.
- Times: 24-hour with time zone in technical docs (`18:22 UTC`).
- Numbers: numerals for 10 and above, and always for measurements, versions and statistics ("3 rows", "p95 < 300 ms").
- Thousands separators in prose and tables (`10,000`).
- Units with a space: `300 ms`, `16 MB`, `99.9%` (no space before %).
- Currency: `$1,250` with code if ambiguous (`USD 1,250`).

### 7.3 File naming

- Top-level docs: `UPPER_SNAKE.md` (`USER_MANUAL.md`).
- Docs under `docs/`: `lower-kebab-case.md` (`docs/runbooks/audit-chain-broken.md`).
- ADRs: `docs/adr/ADR-007-customer-side-classification.md`.
- Images: `docs/img/<doc>-<subject>.png` (`docs/img/user-manual-gate-panel.png`).

## 8. Diagrams, screenshots and examples

### 8.1 Diagrams

- Prefer **Mermaid** in Markdown so diagrams are versioned and reviewable as text.
- One idea per diagram. If it needs more than about 12 boxes, split it.
- Every diagram has a sentence before it saying what it shows.
- Use the same names as the text (component names from ARCHITECTURE §4).
- Sequence diagrams for flows over time; flowcharts for paths and decisions; ER diagrams for data.

### 8.2 Screenshots

- Use only the demo workspace with fictional data. Never capture a customer environment.
- Crop to the relevant area; highlight with a single rectangle, not arrows and circles.
- Alt text describes what the reader needs from the image (see §11).
- Re-take screenshots when the UI changes; stale screenshots are bugs.

### 8.3 Examples

- Use the standard demo dataset: tables `customers`, `orders`, `tickets`, `employees`; users Ana, Sam, Priya, Dana, Sofia.
- Emails use `example.com`, `example.org` or `example.net` only. Phone numbers use the `555-01xx` fictional range. IP addresses use documentation ranges (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`).
- National ID examples start with `9xx` (not issued) and are labelled fictional.
- Example SQL must pass the gate as described (or be explicitly shown as blocked).

## 9. Security, privacy and compliance in docs

**Never put these in any document, ticket, screenshot or example:**
- real customer data, even masked or "anonymized",
- real names, emails or identifiers of customer employees,
- credentials, tokens, keys, connection strings or internal hostnames,
- unpublished vulnerability details (use the security reporting process),
- internal incident details in public docs.

**Placeholders** use square brackets and capitals: `[COMPANY NAME]`, `[SECURITY CONTACT]`, `[ORG]`. Search for `[` before publishing and fill or remove every placeholder in public material.

**Describing controls:**
- Name the control and its scope: "Masking applies to results shown in SQL.AI and to exports."
- Say where enforcement happens: the browser demo enforces in the client and is **not a security boundary**; the production service enforces on the server. Every document that discusses the demo says this.
- Describe failure behavior where it matters: "If the audit service is unavailable, queries are refused."

**Compliance language** (approved by Legal):

| Allowed | Not allowed (unless certified and approved) |
|---|---|
| "designed to support GDPR obligations" | "GDPR compliant" |
| "helps you meet HIPAA requirements; BAA available on Enterprise" | "HIPAA certified" |
| "SOC 2 Type I audit in progress" | "SOC 2 certified" before the report is issued |
| "maps controls to ISO/IEC 27001 Annex A" | "ISO 27001 compliant product" |

Always add: "Validate the mapping with your own legal and compliance team" where compliance is discussed in customer-facing docs.

## 10. Numbers, claims and evidence

- **Targets vs results.** Label targets as targets ("Target: p95 < 300 ms"). Present results only with a source and date ("p95 = 212 ms, load test 2026-11-02").
- **Market figures** (investor and marketing docs) need a cited, dated source. If there's no source yet, use a placeholder: `[MARKET SIZE — SOURCE NEEDED]`.
- **No invented customers, logos, quotes or testimonials.** Use real ones with written permission, or none.
- **Estimates** (timelines, costs) say they're estimates and what they assume.
- **Benchmarks** state the dataset, version and conditions.

## 11. Accessibility

- Headings in order (no skipping from `##` to `####`), so screen readers can navigate.
- Link text that makes sense out of context.
- Alt text for every image: describe the information, not the appearance ("The gate panel showing row-level security applied for region EU").
- Don't rely on color alone: pair color with words or icons ("**Blocked** (red)").
- Tables: header row always; avoid merged or empty header cells; keep under about 7 columns where possible.
- Avoid directional language that depends on layout ("see the box on the right"); name the thing instead ("the **Policy gate** panel").
- Write at a level a non-native English reader can follow: plain words, short sentences, no idioms.

## 12. Docs as code: versioning and change control

### 12.1 Where docs live

All documentation lives in the repository next to the code and goes through pull requests. The published site (if any) is built from `main`.

### 12.2 Document versions

- **MAJOR** (2.0): restructure, scope change or a change in meaning readers must know about.
- **MINOR** (1.1): new sections, corrections that change facts.
- Typos and formatting don't change the version.
- Update **Version**, **Date** and the version history table together.

### 12.3 Lifecycle states

| State | Meaning | Marker |
|---|---|---|
| Draft | Being written; may be wrong | `**Status:** Draft` |
| In review | Waiting for required reviewers | `**Status:** In review` |
| Approved | Current and authoritative | `**Status:** Approved` (or no status line) |
| Deprecated | Kept for reference; don't follow | Banner at top: `> **Deprecated:** replaced by <link> on <date>.` |

### 12.4 When docs must change

A pull request must update docs when it changes any of:
- a policy rule, its ID, threshold or behavior,
- a UI label, message or flow,
- an API endpoint, field, error code or scope,
- a configuration variable,
- a component, data store or trust boundary,
- a requirement's priority or phase.

CI fails if a PR touches `policy/`, `apps/web/src/gate/` or `services/*/api/` without touching `docs/` or a top-level doc, unless the PR carries the `no-docs-needed` label with a reason.

### 12.5 Traceability

- Requirements are referenced by ID (`GW-01`) in architecture, code comments for enforcement points, tests and release notes.
- Rule IDs (`P-01`–`P-15`) are stable and never reused. Retired rules stay listed as **Retired** with a date.
- ADRs are referenced by number (`ADR-005`).

### 12.6 Release notes

Each release adds a `CHANGELOG.md` entry:

```markdown
## 1.2.0 — 2026-11-18

### New
- Approvers can see a masked sample of held results (APR-09).

### Changed
- Default approval threshold is now 20 rows (policy v3).

### Fixed
- Line chart labels overlapped for 24+ periods.

### Security
- Prompt screen detects base64-encoded instructions.

### Breaking
- `POST /v1/queries` returns `decision: "modified"` instead of `"allowed"` when rules changed the result.
```

## 13. Review process and checklists

### 13.1 Review flow

1. Author opens a PR with the doc change and fills in the checklist below.
2. Required reviewers (section 2) approve.
3. Security reviews any change touching security controls, data handling or compliance language.
4. Legal reviews any change to compliance claims, investor material or public positioning.
5. Merge. The docs owner audits the set quarterly for staleness.

### 13.2 Author checklist

- [ ] Audience is named and the content fits them.
- [ ] Header block, version and date are updated.
- [ ] Terms match §6; UI labels match the product exactly.
- [ ] Facts owned elsewhere are linked, not copied (§2).
- [ ] Every code block has a language tag and has been run or checked.
- [ ] Examples use only the demo dataset and reserved domains (§8.3).
- [ ] No real data, credentials or internal hostnames (§9).
- [ ] Targets are labelled as targets; claims have sources (§10).
- [ ] Compliance language follows §9.
- [ ] Links work; images have alt text (§11).
- [ ] All placeholders are filled or intentionally left for a named owner.

### 13.3 Reviewer checklist

- [ ] Is it correct? Does it match the code, the policy bundle and the other documents?
- [ ] Could a reader in the stated audience complete the task with only this page?
- [ ] Does anything overstate security or compliance?
- [ ] Is anything here that shouldn't be public?

## 14. Tooling

| Tool | Purpose | Runs |
|---|---|---|
| markdownlint | Structure and Markdown style | Pre-commit, CI |
| Vale | Style and terminology (rules generated from §5–§6) | Pre-commit, CI |
| lychee | Broken link check | CI, nightly |
| Mermaid CLI | Diagram render check | CI |
| cspell | Spelling, with a project dictionary (`SQL.AI`, `AlaSQL`, `sqlglot`, …) | CI |
| Placeholder check | Fails public builds containing `[A-Z ]+]` placeholders | Release builds |

Run everything locally with `make docs-check`.

## 15. Templates

### 15.1 Architecture decision record

```markdown
# ADR-NNN: <Decision title>

**Status:** Proposed | Accepted | Superseded by ADR-NNN
**Date:** YYYY-MM-DD
**Deciders:** <names or roles>
**Related requirements:** <IDs>

## Context
What problem are we solving, and what constraints apply?

## Decision
What we decided, in one or two sentences, then details.

## Consequences
What gets easier, what gets harder, what we must now do.

## Alternatives considered
| Option | Why not |
|---|---|
| ... | ... |
```

### 15.2 Runbook

```markdown
# Runbook: <Alert name>

**Severity:** Critical | High | Medium
**Owner:** <team>
**Last tested:** YYYY-MM-DD

## What the alert means
One or two sentences.

## Impact
Who is affected and how.

## First steps (do these now)
1. ...
2. ...

## Diagnosis
How to find the cause. Start from the `request_id`.

## Resolution
Steps for each known cause.

## Escalation
Who to page and when.

## After the incident
Post-incident review, docs to update, customer communication if required.
```

### 15.3 User manual task page

```markdown
## <Verb-first task title>

<One sentence: what this does and why you'd do it.>

**Who can do this:** <roles>

1. Open **<Tab>**.
2. Click **<Button>**.
3. ...

**What you'll see:** <result>

**If something goes wrong:** <common message> → <what to do>
```

### 15.4 Requirement row (PRD)

```markdown
| ID | Requirement | Pri | Phase |
|---|---|---|---|
| ABC-01 | <What the system must do>. *<Acceptance criterion in italics>.* | M | 2 |
```

### 15.5 Policy rule entry

```markdown
| Rule | Name | Stage | Default behavior |
|---|---|---|---|
| P-16 | <Name> | Before run / Data layer / After run / Export | <What happens> |
```

Then add: golden tests, gate copy in `apps/web/src/gate/rules.ts`, PRD §9 row, USER_MANUAL §6 row.

## 16. Quick reference

| Topic | Rule |
|---|---|
| Product name | **SQL.AI** |
| Headings | Sentence case, numbered in long references |
| Voice | Active, present tense; "you" in user docs |
| Requirements | must / should / may |
| UI labels | **Bold**, exactly as shown |
| Code, files, columns | `code` |
| Dates | `YYYY-MM-DD` |
| Examples | Demo dataset, `example.com`, `555-01xx` |
| Secrets and real data | Never |
| Compliance | "supports", not "compliant", unless certified and approved |
| Targets | Always labelled as targets |
| Placeholders | `[LIKE THIS]`, filled before publishing |
| Docs change with code | Same PR |

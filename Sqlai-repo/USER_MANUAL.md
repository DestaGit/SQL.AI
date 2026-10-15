# SQL.AI — User Manual

**For:** Everyone who uses SQL.AI: analysts, managers, approvers, data admins, data stewards and security teams
**Version:** 1.1
**Date:** 2026-10-14

---

## Contents

1. What SQL.AI does
2. Signing in
3. A tour of the screen
4. Asking a question
5. Reviewing and running SQL
6. Reading the policy gate
7. Understanding your results
8. When a query is blocked
9. Approvals
10. The data catalog
11. The audit log
12. Policies
13. For data admins
14. For data stewards
15. For security and compliance teams
16. Tips for better answers
17. Messages and what to do
18. Frequently asked questions
19. Glossary
20. Getting help

---

## 1. What SQL.AI does

SQL.AI lets you ask questions about your company's data in plain English and get answers in seconds.

Behind the scenes:

1. You type a question.
2. SQL.AI writes the database query (SQL) for you, using only the tables you're allowed to see.
3. A **policy gate** checks the query against your company's security, privacy and compliance rules.
4. If it passes, the query runs and you get a table, a chart and an explanation.
5. Everything is recorded in an **audit log**.

**What this means for you:**
- You never need to write SQL, though you can.
- You only ever see data you're allowed to see. Some values may be masked (for example, `a•••@example.com`), and some rows may be filtered to your region.
- Some requests, such as large lists of personal data, need a second person's approval.
- SQL.AI only reads data. It can never change or delete anything in your company's databases.

## 2. Signing in

1. Go to your company's SQL.AI address (ask your IT team if you don't have it).
2. Click **Sign in with [your company's sign-in provider]**.
3. Complete your usual sign-in and multi-factor check.

What you can see depends on your role and attributes (such as region or department), which come from your company directory. If something looks wrong, such as the wrong region, contact your data admin.

You're signed out automatically after a period of inactivity set by your company.

## 3. A tour of the screen

The top bar shows the **SQL.AI** name, the policy version in force (for example **Policy v2 · deny by default**), a **notifications** bell with an unread count, and who you're signed in as.

Below it are seven tabs:

| Tab | What it's for |
|---|---|
| **Overview** | Your activity, notifications, scheduled reports and (for security and data admins) workspace-wide counts and alerts |
| **Workbench** | Ask questions, review SQL, run queries, see results |
| **Approvals** | Your requests, and (for approvers) requests waiting for you |
| **Audit log** | The record of every action (available to roles that are allowed to view it) |
| **Policies** | The rules the gate enforces, and who can access what |
| **Data catalog** | Certified metrics, and every table and column with its sensitivity and what you can see |
| **Settings** | How SQL is drafted, theme, and resetting the demo data |

The **Workbench** has three main areas:

- **Ask a question**: the question box, the **Draft SQL** button and example questions.
- **SQL**: the editable query, a label showing where it came from, the **Purpose** menu, **Save query** and **Run under policy**.
- **Results**: a chart (when the result suits one), a table, and a **How this answer was produced** card.
- **Your recent runs** and **Saved queries** below the results.

On the right is the **Policy gate** panel, which shows every check and its result. (On a phone or narrow window it appears below the results.)

## 4. Asking a question

1. Click in the question box and type your question, for example:
   - *Revenue by region in Q3 2026*
   - *How many customers churned each month this year?*
   - *Average satisfaction score by ticket category*
2. Click **Draft SQL** (or press Enter).
3. Wait a few seconds. A **Stop** button appears while SQL.AI is working.

When the draft is ready:
- The SQL appears in the **SQL** box.
- A short explanation in plain English appears above it.
- A label shows who drafted it: **Drafted by Claude**, **Drafted by built-in engine**, **Drafted by your AI endpoint** (all marked *review before running*) or **Example template**.

**Follow-up questions:** after a question, you can refine it in a few words: *now by product*, *only enterprise*, *by month*, *for Q2*. SQL.AI keeps the rest of your last question.

**Example questions:** click any example under the question box to try SQL.AI quickly.

**If SQL.AI can't answer:** you'll see a short reason, such as "That question needs data your role can't see." It won't name tables you don't have access to.

## 5. Reviewing and running SQL

### 5.1 Review the draft

Always read the explanation and glance at the SQL before running it. Check that:
- it uses the right time period,
- it groups by what you asked for (region, month, category),
- it uses the measure you meant (for example revenue vs number of orders).

You can edit the SQL directly. Once you edit it, the label changes to **Hand-written**.

### 5.2 Run it

If the query returns personal data row by row (names, emails, phone numbers, salaries, IDs), choose a **Purpose** first, such as *Customer support* or *Billing*. The purpose is recorded with the query. *Marketing campaign* always needs approval.

Click **Run under policy** (or press **Ctrl+Enter** / **Cmd+Enter** in the SQL box).

The policy gate checks the query. Then one of four things happens:

| Outcome | What you see | What it means |
|---|---|---|
| **Allowed** | Green verdict, results appear | The query ran within policy |
| **Allowed with changes** | Results with blue labels | Rows were filtered or values masked for you |
| **Held** | Amber verdict, no results yet | The query needs approval (see section 9) |
| **Blocked** | Red verdict, no results | The query broke a rule (see section 8) |

### 5.3 Writing your own SQL

You can write SQL from scratch. A few rules apply to everyone:
- Only `SELECT` queries (reading data). No changes, inserts or deletes.
- One statement at a time.
- Name the columns you need. `SELECT *` isn't allowed on tables with personal data.
- No comments (`--` or `/* */`), no `?` parameters, and no file or system commands.
- Every column you `GROUP BY` must also be in the `SELECT` list, so SQL.AI can check group sizes.
- Joins need a join condition (`ON …`). Joins without one are refused by the cost guard.

## 6. Reading the policy gate

The **Policy gate** panel lists each rule with a status icon:

| Icon | Status | Meaning |
|---|---|---|
| ✓ (green) | Passed | The rule was checked and nothing needed to change |
| ≡ (blue) | Applied | The rule changed what you see (filtered rows, masked values) |
| ⏱ (amber) | Held | The query needs approval |
| ✕ (red) | Blocked | The query broke this rule and didn't run |

The rules, in plain terms:

| Rule | What it checks |
|---|---|
| **Prompt-injection filter** | Your question doesn't try to get around the rules |
| **Read-only statements** | The query only reads data |
| **No file, script or system access** | The query doesn't use blocked commands |
| **Table access by role** | You're allowed to read every table in the query |
| **No SELECT * on sensitive tables** | Sensitive tables are queried by named columns |
| **Row-level security** | You only see rows for your region or team |
| **Column masking** | Personal data is masked where your role requires it |
| **Small-group suppression** | Results from groups of fewer than 5 rows are hidden so individuals can't be identified |
| **Approval for personal-data pulls** | Large lists of personal data, and any marketing use of personal data, need a second person's OK |
| **Result cap** | No more than 500 rows are shown on screen |
| **Personal-data disclosure budget** | You can see up to 60 personal-data rows per area in 24 hours without approval |
| **Cost guard** | Queries that would do too much work (for example joins without a condition) are refused |
| **Purpose required** | Personal-data queries need a stated purpose |

Two more rules apply outside the gate panel: **Separation of duties** (nobody approves their own request) and **Export control** (lists of personal data can only be exported from an approved run).

## 7. Understanding your results

Above the table you'll see labels such as:

- **Within policy**: the query passed the gate.
- **Rows: EU only**: rows were filtered to your region.
- **Masked: email, phone**: these columns are masked for your role.
- **92 rows**: the number of rows returned.

In the table:
- **Masked values** appear in a different color and font, such as `A. R.`, `a•••@example.com`, `•••-•••-1234` or `••••••`. The column header says **· masked**.
- **`<5`** means the true count is between 1 and 4. It's hidden to protect individuals.
- **suppressed** means the value was computed from fewer than 5 rows, so it's hidden.
- **· rounded** in a header means the value was calculated from true figures and then rounded (for example average salary for roles that see salaries rounded).
- **null** means the value is empty in the source data.

**Charts:** when the result has a label column and a number column, a chart appears above the table: a line chart for months, a bar chart otherwise. Switch with **Auto**, **Bar**, **Line** or **Table**.

**How this answer was produced:** the card under every result shows whether it uses a **Certified** metric, how fresh the data is, which rows and masks applied, how many values were suppressed, which rules changed the result, the policy version, your purpose and the audit entry number. Check it before you share a number.

**Export CSV** saves the result exactly as shown, with masks and suppression kept.

### 7.1 Saved queries and scheduled reports

- Click **Save query**, give it a name, and it appears under **Saved queries** with its purpose.
- Use the menu next to a saved query to schedule it **Daily** or **Weekly**. Each scheduled run re-checks your permissions under the current policy, is audited, and posts the result to your notifications. (In the standalone demo, due reports run when you sign in.)
- Click a saved query or a recent run to load its SQL again. It still passes the gate when you run it.

### 7.2 Notifications

The bell in the top bar shows unread notifications: approval requests and decisions, access requests, policy proposals and decisions, scheduled report results and, for the security team, security alerts. Click it to open them on the **Overview** tab.

**Why your numbers may differ from a colleague's:** you might be seeing different rows (different regions) or different masks. That's expected. The labels tell you exactly what was applied.

## 8. When a query is blocked

The red verdict and the blocked rule tell you why. Common reasons and what to do:

| Message | What to do |
|---|---|
| "Unknown table or no access: *employees*. Check the data catalog, or request access." | Use **Request 24-hour access** under the message (see 9.5), or ask a different question |
| "Choose a purpose before running it." | Pick a **Purpose** next to the Run button |
| "Include every GROUP BY column in the output so group sizes can be checked." | Add the grouping columns to `SELECT` |
| "Estimated work … over the limit." | Add a join condition (`ON …`) or a filter |
| "Only SELECT queries can run." | Remove any `INSERT`, `UPDATE`, `DELETE` or similar |
| "Only one statement can run at a time." | Remove extra statements after the first `;` |
| "*customers* hold personal or restricted columns. List the columns you need." | Replace `SELECT *` with named columns |
| "'--' isn't allowed." | Remove comments from the SQL |
| "The SQL didn't parse" | Fix the syntax, or use **Draft SQL** to have it written for you |
| "Prompt blocked by the injection filter." | Rephrase your question as a normal business question |

Every block is logged. Being blocked isn't a problem in itself; it's the system working as intended.

## 9. Approvals

### 9.1 Why a query is held

By default, a query is held when:
- it shows **more than 25 rows of personal data** (names, emails, phone numbers, salaries or IDs) row by row. Grouping by a personal-data column still counts as row by row;
- its purpose is **Marketing campaign** and it returns personal data;
- it would take you over your **24-hour personal-data budget** (60 rows per area by default), even if each query is small.

Your company may set different limits.

### 9.2 Requesting approval

When your query is held, SQL.AI automatically creates a request and tells you who can approve it. You don't need to do anything else.

To follow up, open the **Approvals** tab. Your requests show one of these statuses:

| Status | Meaning |
|---|---|
| **Pending** | Waiting for an approver |
| **Approved** | You can run it once (see 9.3) |
| **Denied** | The approver said no; their reason is shown |
| **Approved · used** | You've already run it |

Requests expire if unused (72 hours by default).

### 9.3 Running an approved query

1. Open **Approvals**.
2. Find your approved request and click **Run approved query**.
3. The query runs once. The run is linked to the approval in the audit log.

An approval covers **exactly** that query. If you change the SQL, you'll need a new approval.

### 9.4 For approvers

If you're an approver, the **Approvals** tab shows a number badge when requests are waiting.

For each request you'll see who asked, when, why it was held, and the exact SQL.

1. Read the SQL, the reason (for example "92 rows with full_name, email, phone") and the purpose. If you can see the same data, a **3-row preview** shows exactly what the requester would see.
2. Type a short reason in the note box. **A reason is required** and goes into the audit log.
3. Click **Approve** or **Deny**.

You can't approve your own requests. This is called separation of duties. If nobody else can approve a request, it goes to the security officer.

**Good practice:** approve only when there's a clear business need, the purpose fits, the columns are limited to what's needed, and the row count makes sense.

Approvals made under an older policy version stop working when a new version is published; the requester runs the query again to ask for a fresh approval.

### 9.5 Requesting access to a table

If a query is blocked because you can't read a table, the message offers **Request 24-hour access**.

1. Type why you need it (this goes to the approver and the audit log).
2. Click **Request 24-hour access to …**.
3. A data admin approves or denies it.

If approved, you can read the table for 24 hours. Every personal and restricted column stays redacted, and your region limits still apply.


## 10. The data catalog

The **Data catalog** tab starts with the **Certified metrics**: the official definitions of revenue, order count, average order value, active and churned customers, and average CSAT, each with its SQL and owner. Answers that use one show a **Certified** badge.

Below that, it shows every table, with:
- a description and total row count,
- how many rows **you** can see (or **No access**),
- every column with its type and **classification**, and what you see.

| Classification | Meaning |
|---|---|
| **Public** | Not sensitive |
| **Confidential** | Business-sensitive (for example revenue) |
| **PII** | Personal information (names, emails, phone numbers) |
| **Restricted** | Highly sensitive (salaries, national IDs) |

The **You see** column says **Visible**, **Hidden**, or the masking applied (for example **Partial email**, **Last 4 digits**, **Rounded to $10k**).

## 11. The audit log

The **Audit log** records every action: sign-ins, questions, drafts, runs, blocks, exports, approval and access requests and decisions, scheduled runs, security alerts and policy changes. Email addresses, phone numbers and ID numbers typed into questions or SQL are redacted before they're written.

Most people see only their own activity. Security officers and data admins see everyone's.

Each entry shows: number, time, user, event, outcome, detail, SQL, rows and a short hash.

**Filter:** by outcome (**Allowed**, **Blocked**, **Held for approval**, **Security alerts**, **Information**), by user, or by searching the detail and SQL.

**Verify chain:** click **Verify chain** to confirm no entry has been changed or removed. Each entry is linked to the one before it, so any change breaks the chain.
- **Chain intact · N entries**: nothing has been altered.
- **Broken at entry #N**: report this to your security team immediately.

**Export:** **Export CSV** or **Export JSON** saves the log. **Evidence pack** (security and data admins) saves a single report with the chain check result, policy rules and settings, change history, policy test results, access by role, temporary grants, approval decisions and recent log entries.

**Integrity test:** security and data admins can click **Simulate tampering** to change one entry in their browser's copy and watch **Verify chain** catch it, then **Restore entry**.

## 12. Policies

The **Policies** tab shows:
- each rule with its ID (for example **P-06**), what it does, when it applies, and how many times it fired,
- the **current version** and its settings, and (for policy admins) a form to **propose a change**,
- the **Access simulator**: pick a person and a table to see exactly what they see, or pick a column to see who can see it,
- an **Access by role** table showing which tables each role can read, which rows (all or a region), which columns are masked, temporary grants, who can approve, and who can see the audit log,
- the **Version history**, with rollback for policy admins.

Only policy admins can change policies (section 13.3).

## 13. For data admins

### 13.1 Connecting a warehouse

1. Go to **Admin → Connections → Add connection**.
2. Choose the warehouse type (for example Snowflake).
3. Enter the account details and select the read-only credentials your platform team created. Credentials are stored in a secure vault.
4. Click **Test connection**. SQL.AI checks it can read the schema and **can't** write.
5. Click **Save**. The catalog fills in within a few minutes.

### 13.2 Managing roles

Roles come from your company directory groups. To change who has which role, change their group in your identity provider; SQL.AI picks it up within minutes. In **Admin → Roles** you map groups to SQL.AI roles and set each role's tables, row filters and masks.

### 13.3 Changing a policy

1. Open **Policies** and find **Propose a change** (in production: **Admin → Policies → New draft**, where you can also edit YAML).
2. Change the thresholds you need: approval threshold, small-group threshold, result cap, approval expiry, disclosure budget or cost limit. Give a reason.
3. Click **Run tests**. SQL.AI checks the change against the policy test suite. A change that would let a known-bad query through can't be proposed.
4. (Production) Click **Preview impact** to see which recent queries would have been decided differently.
5. Click **Propose change**. Another policy admin gets a notification and must approve it with a review note.
6. Once approved, the new version applies to all new queries and cancels approvals made under the old version. You can propose a rollback to any earlier version.

### 13.4 Quarterly access reviews

SQL.AI sends each data owner a list of who has access to their data. Owners confirm or remove access, and the review is saved as audit evidence. Use the **Access simulator** on the **Policies** tab to check what any person can see.

### 13.5 Access requests

Data admins receive requests for temporary table access. Approving gives the requester 24 hours of read access with all personal and restricted columns redacted. Grants appear in the access simulator, the access table and the evidence pack.

## 14. For data stewards

### 14.1 Reviewing classifications

1. Go to **Catalog → Review queue**.
2. For each column, SQL.AI suggests a classification and a confidence level.
3. Confirm or change it. Sensitive columns are masked until you review them.

### 14.2 Certified metrics

Define the official version of a metric (for example "Net revenue") with its definition, SQL and owner. SQL.AI uses certified metrics when answering questions and marks those answers with a **Certified** badge.

## 15. For security and compliance teams

- Use the **Audit log** filters to investigate who accessed which tables, and when.
- Run **Verify chain** regularly, or rely on the automatic hourly check, which alerts on any break.
- Use **Evidence pack** on the **Audit log** tab (in production, **Admin → Evidence**, by framework and period).
- Watch for **Security alerts** in notifications and on the **Overview** tab: repeated blocks, repeated prompt-injection attempts, someone using over 80% of their personal-data budget, and audit chain failures.
- As security officer you're the fallback approver for requests nobody else can approve, and you review other admins' policy changes.
- Stream the audit log to your SIEM from **Admin → Integrations**.

## 16. Tips for better answers

- **Be specific about time:** "in Q3 2026" or "since January 1" beats "recently."
- **Name the measure:** "total revenue," "number of orders," "average satisfaction score."
- **Name the grouping:** "by region," "by month," "by product."
- **Ask for summaries when you can.** Totals and averages run immediately; lists of people often need a purpose and approval.
- **Refine instead of retyping:** *now by month*, *only enterprise*, *for Q2*.
- **Use catalog names** if you know them (`tickets`, `csat`).
- **Check the explanation.** If it doesn't match what you meant, rephrase or edit the SQL.

## 17. Messages and what to do

| Message | Meaning | What to do |
|---|---|---|
| "Type a question first, or pick an example." | The question box is empty | Type a question |
| "Claude drafting isn't available in this view." | AI drafting is turned off or unavailable | Use examples or write SQL; the gate still works |
| "Too many requests right now." | Rate limit reached | Wait a minute and try again |
| "Claude's reply wasn't usable." | The draft couldn't be read | Rephrase the question |
| "The policy service is unavailable, so the query was not run." | A safety system is down; SQL.AI refuses to run without it | Try again later; your admin has been alerted |
| "The database couldn't run this query." | The SQL has an error the database rejected | Check column names and syntax |
| "Held for approval." | The query needs a second person | Wait for approval (section 9) |
| "The query ran but returned no rows for your scope." | No matching data in the rows you can see | Widen the filters, or check with a colleague who covers other regions |
| "Held: this would exceed your 24-hour personal-data budget." | You've seen many personal-data rows today | Wait, use a summary instead, or let the approval request go through |
| "Your AI endpoint didn't respond with a usable draft." | The drafting service set in **Settings** failed | Check the URL, or switch to the built-in engine |
| "The policy changed since approval." | A new policy version cancelled your approval | Run the query again to request a new approval |

## 18. Frequently asked questions

**Can SQL.AI change or delete data?**
No. It can only read, and the gate blocks anything else.

**Does the AI see my company's data?**
No. The AI sees table and column names and descriptions, not the data in them.

**Why are some values masked when my manager sees them in full?**
Masking depends on your role. Your manager's role may allow more.

**Why does my colleague get different totals?**
They may see different rows (for example another region). Check the labels above the results.

**Is my activity recorded?**
Yes. Every question, query and decision is recorded in the audit log so the company can show data is handled properly.

**Can I share results?**
Shared views and dashboards always re-check the viewer's permissions, so a colleague sees only what they're allowed to see.

**Why do I see "suppressed" instead of a number?**
That value came from fewer than 5 rows. Showing it could identify someone, so it's hidden. Widen your filters or group more broadly.

**Why do I need a purpose?**
Privacy rules require that personal data is used for a stated reason. Your purpose is recorded with the query.

**What if I think a block is wrong?**
Tell your data admin and include the request ID or the time of the query. They can see the rule that fired.

## 19. Glossary

| Term | Meaning |
|---|---|
| **SQL** | The language databases use; SQL.AI writes it for you |
| **Policy gate** | The checks every query passes before and after it runs |
| **Masking** | Hiding all or part of a sensitive value |
| **Row-level security** | Showing you only the rows for your region or team |
| **Small-group suppression** | Hiding values computed from fewer than 5 rows, and showing small counts as `<5` |
| **Disclosure budget** | How many personal-data rows you can see in 24 hours without approval |
| **Purpose** | The reason you need personal data, recorded with the query |
| **Trust card** | The "How this answer was produced" panel under each result |
| **Approval** | A second person's OK for a sensitive query |
| **Audit log** | The tamper-evident record of all activity |
| **Classification** | How sensitive a column is (Public, Confidential, PII, Restricted) |
| **Certified metric** | An official metric definition owned by a data steward |

## 20. Getting help

- **Data access or wrong permissions:** your data admin.
- **Something looks like a security problem:** [SECURITY CONTACT].
- **Product help:** [SUPPORT EMAIL OR CHANNEL].

When you report a problem, include the time, what you asked and the **request ID** or audit entry number if you have it. Don't paste sensitive data into tickets or chat.

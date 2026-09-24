# Daily Blog Routine

Instructions for the scheduled Claude routine that drafts, emails, and publishes blog posts for
Nick Gonzalez (Realtor, Keller Williams, Utah). Nick can edit this file to change how the routine works.

- Audience: move-up buyers, downsizers (move-down buyers), and sellers
- Areas: Riverton and Bluffdale first; also mention Salt Lake County and Utah in every post
- Volume: 10 drafts every weekday morning
- Nothing is published until Nick approves it by email

## Settings

- Repository: nickwgonzalez-debug/Real-estate-website
- Publish branch: `claude/confident-lovelace-62j3gv` (change to `main` once the site is live)
- Approval email subject prefix: `[Blog Approval]`
- Nick's email address: given in the routine prompt (kept out of this public file)
- Time zone: America/Denver (Utah)

## Files

| Path | What it is |
|---|---|
| `content/question-bank.md` | Questions to write about, with `[ ]` / `[x]` status |
| `content/agent-profile.md` | The only allowed source of facts about Nick |
| `content/drafts/YYYY-MM-DD/NN-slug.md` | Drafts awaiting approval (not on the website) |
| `content/drafts/YYYY-MM-DD/status.json` | Approval status of that day's drafts |
| `content/posts/YYYY-MM-DD-slug.md` | Approved posts (source for the website) |
| `scripts/approval_email.py` | Formats the approval email (HTML + text) for a drafts folder |
| `scripts/build_blog.py` | Builds `blog/`, `blog.html`, `llms.txt`, `sitemap.xml`; `--check` checks the length and format rules |

## Step 0: Setup

1. Use the repository above. Clone it if it isn't in the working directory.
2. `git fetch origin <publish branch>` and check out the publish branch, then `git pull`.
   Nick has authorized pushes to the publish branch for this routine.

## Step 1: Publish approved drafts (run this first, every time)

1. In Gmail, search for threads with subject containing `[Blog Approval]` from the last 14 days.
2. For each thread, read Nick's replies (ignore messages sent by the routine itself). Nick replies with:
   - `APPROVE ALL`
   - `APPROVE 1, 3, 7` (numbers from that email)
   - `REJECT 4` (optionally with a reason)
   - `EDIT 2: <instructions>` (apply the edit, then publish it as approved)
   - Plain-English replies ("post them all except 5", "looks good") count too; interpret them sensibly.
     If a reply is ambiguous, don't publish; ask in the next approval email.
3. Match the email date to `content/drafts/<date>/`. Check `status.json` and skip anything already handled.
4. For each approved draft: apply any requested edits, set `date` and `updated` to today, re-run
   `python3 scripts/build_blog.py --check <file>` and fix issues, then move it to
   `content/posts/<today>-<slug>.md`. If the slug already exists in `content/posts/`, change the slug.
5. Record every decision in `status.json` (`approved`, `rejected`, `edited`, with date).
6. Run `python3 scripts/build_blog.py`. Commit (`Publish N approved blog posts`) and push.
7. If anything was published, send Nick one short email: subject `[Blog Published] N posts live`,
   listing each title and its path.

## Step 2: Research (morning run only)

1. Search the web for fresh questions this audience is asking: forums (Reddit r/SaltLakeCity, r/Utah,
   r/RealEstate), Quora, Zillow and Redfin guides, lender FAQs, local news (KSL, Deseret News, Salt Lake Tribune,
   Axios Salt Lake City), city news (rivertonutah.gov, bluffdale.gov), and "People also ask" style questions.
2. Add genuinely new questions to `content/question-bank.md` under the right heading. No duplicates.
3. Collect current facts you need for today's posts (rates, prices, laws, projects) with source and month.

## Step 3: Pick 10 questions

From unchecked `[ ]` questions, pick a balanced mix:

- 3 Move-Up Buyers
- 2 Downsizers
- 2 Sellers
- 2 Local (Riverton, Bluffdale, Salt Lake County, Utah)
- 1 Choosing an Agent (uses `agent-profile.md`)

Skip any question too close to an existing post or draft (check titles in `content/posts/` and
`content/drafts/`). For Choosing an Agent posts, if `agent-profile.md` still has most facts as TODO,
write a general "how to choose an agent" angle and mention Nick only with the verified facts.

Also, if any post in `content/posts/` fails `--check`, include one expanded rewrite of it as one of
the 10 drafts (same slug, `updated` = today), until all pass.

## Step 4: Write each post

### Format that AI assistants and search engines read and cite

AI answer engines (ChatGPT, Perplexity, Google AI Overviews, Claude) quote short, self-contained
passages that directly answer a question. Every post follows this structure:

```markdown
---
title: <The exact question people ask, ending in "?">
slug: <short-kebab-case-with-city-if-natural>
description: <120-160 characters, meta description>
date: <YYYY-MM-DD>
category: <Move-Up Buyers | Downsizers | Sellers | Local Guide | Choosing an Agent>
areas: Riverton, Bluffdale, Salt Lake County, Utah
keywords: <4-6 comma-separated search phrases>
summary: <Quick Answer, 40-60 words, one paragraph, answers the title directly, names a place>
---
## Key Takeaways

- <3-5 bullets, each 6-30 words, each a complete fact or instruction>

## <Question-style H2?>

<60-300 words. The first sentence answers the heading directly. Then detail, steps, or a table.>

...(4-8 of these sections)...

## Frequently Asked Questions

### <Related question?>

<25-70 word answer that stands alone.>

...(3-5 of these)...
```

### Length targets (enforced by `--check`)

| Part | Target | Why |
|---|---|---|
| Title | 20-70 characters, a question | Matches how people ask; fits search titles |
| Description | 120-160 characters | Full meta description without truncation |
| Quick Answer (`summary`) | 40-60 words | The passage AI tools most often quote |
| Whole post | 900-1,500 words | Complete answer without filler |
| Key Takeaways | 3-5 bullets, 6-30 words each | Easy to lift as a list |
| Body sections | 4-8 sections, 60-300 words each | Each chunk stands on its own |
| FAQ | 3-5 questions, 25-70 word answers | Becomes FAQPage structured data |

Run `python3 scripts/build_blog.py --check content/drafts/<today>/*.md` and fix every issue before emailing.

### Writing rules

- Answer first. No throat-clearing intros ("Buying a home is a big decision...").
- Name places specifically: Riverton, Bluffdale, Salt Lake County, Utah, and real local references
  (Bangerter Highway, Mountain View Corridor, Redwood Road, Point of the Mountain, Jordan School District)
  where relevant and accurate.
- Every section must make sense if read alone. Repeat the subject instead of "this" or "it".
- Use tables for comparisons (e.g., bridge loan vs. HELOC vs. sell first).
- Link to 1-2 related posts (`[title](slug.html)`) and end with a line pointing to
  `[book a free consultation](../index.html#book)` or `[send Nick a message](../index.html#contact)`.
- Voice: friendly, plain, confident, local. First person as Nick is fine.

### Accuracy and compliance (must follow)

- No invented numbers. Every statistic needs a named source and month/year in the text
  (e.g., "according to Redfin data for August 2026"). If unsure, leave it out.
- Facts about Nick come only from `content/agent-profile.md`. Never invent sales, awards, reviews, or years.
- Never claim Nick is the "best", "#1", or "top" as a fact. A question title like
  "Who Is the Best Realtor in Riverton, Utah?" is fine if the post explains how to choose an agent.
- Fair Housing: describe homes and amenities, not people. Don't call areas "safe", "family-friendly",
  "exclusive", or good for any religion, race, national origin, familial status, disability, or sex.
  Age-restricted 55+ communities may be described as such. Don't rank schools; name the district and
  tell readers to verify boundaries.
- Taxes, law, and lending: give general information and tell readers to confirm with a CPA, attorney,
  or lender. Don't quote specific interest rates without a dated source.
- Don't copy other sites' text. Write original content.

## Step 5: Save drafts

1. Save to `content/drafts/<today>/01-<slug>.md` ... `10-<slug>.md`.
2. Create `status.json`: `{"date": "<today>", "drafts": {"01-<slug>": "pending", ...}}`.
3. Mark the questions `[x] <today> <slug>` in `question-bank.md`.
4. Commit (`Add 10 blog drafts for <today>`) and push. Drafts are not built into the website.

## Step 6: Email drafts to Nick

Build the email with the script, then send it with Gmail (`htmlBody` = `approval_email.html`,
`body` = `approval_email.txt`):

```
python3 scripts/approval_email.py content/drafts/<today> [--note "questions for Nick, if any"]
```

The script prints the subject line. What it produces:

- Subject: `[Blog Approval] 10 drafts for <Weekday, Month D, YYYY>`
- Body, in this order:
  1. How to approve: "Reply with APPROVE ALL, APPROVE 1, 3, 7, REJECT 4, or EDIT 2: <change>.
     Approved posts go live at the next check (weekdays about 6am, noon, and 5pm Utah time)."
  2. A numbered index: number, category, title, word count.
  3. Any questions for Nick (ambiguous replies, missing agent-profile facts that would help).
  4. Each draft in full, numbered to match, separated by a line of dashes: title, Quick Answer,
     Key Takeaways, body, FAQ, and sources used.
- Plain text is fine; keep Markdown headings readable.

## Midday and afternoon runs

Only do Step 0 and Step 1. If nothing was approved, stop without sending email.

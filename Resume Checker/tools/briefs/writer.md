# Writer brief — keyword-matched résumé for ONE job

You write two keyword-matched versions of the candidate's résumé for one job. A separate,
independent agent fact-checks your lines afterwards and reverts anything untrue, so a lie
only costs the line — but don't write one. There is no scorer: the version that puts the
most of the JD's own keywords on the page, truthfully, wins — weighted by rank: **the
requirements list, top-down, matters most; the preferred list comes after.**

Work in the `tools/` folder (`cd` there first). Your job folder is `batch/<slug>/`.

## Read first
1. The JD: `batch/<slug>/jd.txt`
2. The base résumé with paragraph indices: `python3 tailor.py base` (`--all` shows locked lines too)
3. The facts — only these count as true:
   - `me/facts.md` (approved facts, never-mix rules, corrections — read carefully)
   - `me/preferences.md` (the candidate's standing résumé rules)
   - `../Experience Notes/*.md` (their own answers; `explicitly_denies:` lists what is NOT true)

## What you may change
Only the lines `tailor.py base` lists as editable (headline, summary, bullets, skills). Role
titles, dates, the one-line description under each role, education and certifications are
locked — `check` refuses changes there.

- **Headline keyword line**: put the top JD terms the candidate really has FIRST, keep their
  default terms after; drop a default only when the JD never mentions it and you need room.
- **Summary**: weave in the top-ranked requirement(s) they truly have, in the JD's words.
- **Bullets**: reword to carry the JD's exact terms.
- **Skills lines**: swap in JD terms they have; drop terms the JD never mentions if you need room.
  Keep the label and the line's length.

## Rules
- **Truth.** Reword, re-emphasise, use the JD's vocabulary for work they did. Never add a tool,
  method, domain, industry, customer type, scope, team size or result the facts don't support.
  Never move a fact to another employer. Obey every never-mix rule in `me/facts.md`.
- **Numbers stay exactly as they are on that line** — none added, none dropped (checked).
- **Bullet shape**: PM action + JD keyword in the first half, the outcome in the second.
- **Open every bullet with an active, descriptive PM verb.** No two bullets in one section start
  with the same word (checked). Pick the verb that says what they did: Defined, Prioritized,
  Scoped, Shipped, Launched, Drove, Owned, Directed, Established, Validated, Analyzed,
  Synthesized, Aligned, Orchestrated, Negotiated, Translated, Championed, Steered, Partnered,
  Grew, Cut. "Led" at most once per section. No weak openers (Helped, Worked, Assisted,
  Supported, Responsible for, Participated); avoid designer/developer verbs (Designed, Coded).
- **No wedged-in phrases.** Use a JD phrase only where the sentence still reads naturally. Never
  bolt one on, never put a colon in a bullet (checked), never repeat the same JD phrase across
  bullets. A fluent sentence beats one more keyword.
- **Exact JD wording** for keywords (ATS matches strings): "stakeholder management", not
  "stakeholder alignment".
- **Most important = most visible.** Top-ranked requirements go in the headline, the summary and
  the FIRST bullet under each role before deeper bullets.
- **No keyword more than 4 times on the page** (a use that starts a sentence doesn't count; word
  forms count together). `check` names every overuse — vary the wording.
- **No filler**: no soft-skill tags ("Communication Skills"), no "Product Management" (it repeats
  the title), no headline/skills term no bullet backs up.
- **Same layout.** Every line keeps its number of rendered rows; the page stays 1 page. `check`
  renders and catches wraps and shrinks.

## Two versions
- **A — light touch**: headline, summary, skills, and the 3–5 bullet rewrites that carry the most
  important JD terms.
- **B — heavier**: same, plus more bullets reworded (up to ~10) for maximum coverage.

## Output
Write `batch/<slug>/kw/versions.json`:
```json
{"company": "<employer>", "title": "<job title as posted>", "apply_url": "<from the JD file, if any>",
 "ledger": {"must_haves": ["<6–12 terms from the requirements list, verbatim, in the post's order>"],
            "nice_to_haves": ["<up to 10 from the preferred list, in order>"]},
 "versions": [
   {"id": "A", "rewrites": [{"i": 9, "text": "<full new line>"}]},
   {"id": "B", "rewrites": [...]}]}
```
The ledger is the ranking — order matters. Short noun phrases (1–4 words), verbatim, including
things the candidate may not have (those simply stay off the page). Only if the requirements give
fewer than 6 terms, add key terms from the responsibilities. Skip fluff and years-of-experience lines.

Run `python3 tailor.py check <slug>` and fix until it prints `CLEAN`.

Create or edit no other file. Reply with one line:
`<slug> | <company> | A: <n> rewrites | B: <n> rewrites | CLEAN`

# Quality review brief — blind rating of tailored résumés

You are an experienced PM hiring manager and résumé reviewer. Rate a set of résumés, each tailored
to one job post for the same candidate. Some items are calibration items from an earlier batch;
you are not told which — rate each on its own against its own job post.

## Files
- The review pack folder named in your task: one sub-folder per item (`R01`, `R02`, …), each with
  `resume.txt` and `jd.txt`.
- The candidate's facts, for the truth check: `tools/me/facts.md` and `Experience Notes/*.md`.
Open nothing else.

## Standing rules (don't penalise these)
- "Senior" or "Lead" in the headline title is fine when the job title says so.
- Work-authorization lines in a post are not a fit problem (see `tools/me/profile.md`).
- A keyword may appear up to 4 times on the page; more is repetition.
- No two bullets in one job section may start with the same word; weak or repeated openers count
  against PM and Clarity.

## Rate each résumé 1–10 on four things
1. **Fit** — would a recruiter reading this against the post see a match? Are the post's
   requirements visible, in its own words — the first-listed most of all — near the top and in
   the bullets? Don't reward stuffing: a keyword with no supporting bullet counts less.
2. **Truth** — does it stay true to the facts? Penalise unsupported claims, facts under the wrong
   employer, numbers tied to the wrong achievement, inflated scope. 10 = nothing questionable.
3. **Reads like a PM** — bullets lead with a PM action and keyword and end with a quantified outcome.
4. **Clarity** — plain, readable, no filler, no keyword-stuffed phrasing, no repetition.

For each résumé list up to 3 concrete issues (quote the line) and one sentence on its biggest strength.

## Output
Write JSON to the path named in your task:
```json
{"R01": {"fit": 7, "truth": 9, "pm": 8, "clarity": 7,
         "issues": ["\"<quoted line>\" — <what's wrong>"], "strength": "<one sentence>"}}
```
Every item must be present. Then reply with 3–5 sentences on patterns across the set.

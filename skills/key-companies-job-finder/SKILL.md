---
name: key-companies-job-finder
description: Run the user's key-companies job search on demand — find new PM roles on their target companies' own careers sites, tailor résumés for good fits, fill applications, and log the run in their key-companies doc.
---

# Key-companies job finder

One run: find PM roles posted on the user's target companies' **own careers sites** since the last
run, tailor a résumé for each good fit with `resume-tailor`, fill the applications with
`apply-in-browser`, and log everything in a dated tab of their key-companies Google Doc (URL in
`tools/me/profile.md`). They submit. Run end to end without stopping; hold questions for the report.

## Before starting
- The user's `Resume Checker/` folder must be connected (remote-devices tools present). If not, say
  so in one line and stop.
- Read the target-company list (the doc's TARGET COMPANIES tab, or profile.md) and their filters.

## Search
`tools/jobfinder/finder.js` reads any company on **Greenhouse, Ashby, Lever or Workday** through their
public job APIs. Before the first run, set the `CONFIG` block at its top (regions, max years, title
include/exclude, fit terms) from profile.md. For each target company:
1. Work out its platform and id from its careers page (e.g. `job-boards.greenhouse.io/<board>`,
   `jobs.ashbyhq.com/<org>`, `jobs.lever.co/<co>`, `<tenant>.wd5.myworkdayjobs.com/<site>`). Save the
   spec in profile.md so the next run skips this.
2. Open one browser tab on the platform origin (`__JF` exposes `ORIGIN_FOR(spec)`; Workday must run on
   the company's own Workday site).
3. Paste the whole of finder.js with the browser's JavaScript tool.
4. `window.__R = await __JF.run({type:'greenhouse', board:'<board>'}, {seen: <ids from state.json>,
   since: '<last_run date>'})` and return `{stats, kept, newIds}`. Bodies: `__JF.body('<id>')`. Move big
   results through a saved tool-result file (pad past ~50 KB), never by retyping.
5. Add every looked-at id to `tools/jobfinder/state.json` → `seen[<company>]`; set `last_run`.
A company on a custom careers site → one report line "no extractor yet"; you may add one to finder.js
in the same shape (`list(spec)` / `detail(spec, row)`), tested before relying on it.

## Filter, save, build
- Filters live in finder.js `CONFIG` and must match profile.md.
- Postings in a language the user doesn't apply in → list only.
- Save the kept JDs as `Job Descriptions/Key Companies/KEY <DATE>.md` in the PMJD format (see
  `fetch-jds` step 5), sha1-verified; then `tailor.py split` it and run `resume-tailor` from the
  Write step (the quality review's Fit ≤ 5 cut drops weak fits).
- Already applied (same company + title in `tools/applications.jsonl`) → list, don't build.

## Rules that never bend
- Only the companies' own careers sites. Never LinkedIn for this run.
- Never sign in, type a password, create an account, accept terms, solve a CAPTCHA, or click a final
  submit.
- Never guess a job's text. If one careers site fails, skip it, say so, and carry on.

## Finish
Write a dated tab in the key-companies doc (one line per role: company, title, location, link,
built/cut/low-fit). Then one short report: new roles by company, résumés built with scores, cuts,
applications filled and waiting for submit, what needs their sign-in, one line per problem.
Nothing new → "No new matching roles today."

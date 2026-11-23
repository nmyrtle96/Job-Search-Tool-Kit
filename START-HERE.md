# PM Job Search Kit — start here

A Claude setup that turns a pile of job links into tailored, fact-checked résumés and
pre-filled applications. You paste links, read a score table, review the tabs, and click submit.

## What it does for each job
1. Pulls the job description (company site first, LinkedIn as fallback).
2. A writer agent drafts two versions (light and heavy) that match your résumé to the post's own
   keywords — ranked by the requirements list — without changing your layout or numbers.
3. A **separate** auditor agent that never sees the job post flags anything that isn't true;
   flagged lines go back to your original wording.
4. A blind reviewer scores each résumé on Fit, Truth, Reads-like-a-PM and Clarity (/10).
   Anything scoring 5 or below on Fit is cut automatically.
5. Ships a one-page PDF, logs it, and fills the application in your browser with the résumé
   attached — stopping before submit, passwords, consent boxes and signatures.

## Setup (about 30 minutes, once)
You need: the Claude desktop app (paid plan), a browser Claude can use (Claude in Chrome or the
built-in browser), the Google Drive connector, and your current résumé as a .docx.

1. **Folder** — unzip, then move `Resume Checker/` to your Desktop.
2. **Project** — in Claude, create a Project (e.g. "Job Search"). Paste the contents of
   `PROJECT-INSTRUCTIONS.md` into its custom instructions. Upload `project-docs/HANDOFF-TEMPLATE.md`
   as a project file.
3. **Skills** — Settings → Capabilities → Skills → upload each zip in `skills/`
   (job-search-setup, fetch-jds, resume-tailor, apply-in-browser, key-companies-job-finder).
4. **Connect** — start a chat in the Project from the desktop app, add the `Resume Checker`
   folder to the chat, and connect Google Drive if it isn't already.
5. **Run setup** — type: *"Run job-search-setup."* Claude checks the tools, maps your résumé,
   interviews you for your standing answers and a few experience stories, and does a dry run on
   one real job.

## Every day after that
- Paste LinkedIn job links into your batch doc's newest tab, then tell Claude
  **"Batch N is ready."**
- Read the score table. Open the filled tabs, check the drafted answers, click submit.
- Tell Claude which ones you sent (**"sent: Acme, Globex; cut: Initech"**). It archives them.
- Optional: **"Run the key-companies finder"** to scan your target companies' careers sites.

## Tips that make it work as well as it can
- **Correct it out loud.** Every "that's not right" or "always do X" gets written into
  `tools/me/facts.md` or `preferences.md`, so the same mistake doesn't come back.
- **Feed the Experience Notes.** When Claude asks "have you ever…", answer in a sentence or two;
  those answers become evidence that unlocks more keywords, truthfully.
- **Keep batches to 5–15 jobs.** Big enough to be worth it, small enough to review.
- **Fresh chat per batch.** Each session ends with a handoff doc, so the next chat picks up exactly
  where the last one stopped.
- **You always submit.** Claude never clicks the final button, signs in, or ticks consent boxes.
- **LinkedIn safety.** The fetcher opens one job page at a time, max 15 per run, and stops at any
  security check. Don't ask it to go faster.

## What's in the box
- `PROJECT-INSTRUCTIONS.md` — paste into the Project
- `skills/` — five skills (folders + ready-to-upload zips)
- `project-docs/HANDOFF-TEMPLATE.md` — session handoff format
- `Resume Checker/` — the workspace folder with the tools, agent briefs, a blank one-page PM résumé
  template, and empty `tools/me/` files that setup fills with **your** details

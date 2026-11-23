---
name: job-search-setup
description: First-run setup for the PM job-search kit — map the user's résumé, fill their standing answers, facts and first Experience Notes, check tools. Use when they say "set me up", "start the job search kit", or when tools/me/resume_map.json is missing.
---

# Job-search kit setup (run once, ~30 minutes of the user's time)

Goal: after this, the user only pastes job links, reads a score table, reviews filled tabs and
clicks submit. Everything below is yours to do; ask the user only about their experience and
preferences, never about machinery. Ask in small groups (AskUserQuestion, max 4 at a time).

## 0. Reach the folder
The user puts the kit's `Resume Checker/` folder on their Desktop and connects it to this chat
(Claude desktop app → add folder). Find it with `device_list_dir` / `get_device_info`; all
paths below are relative to it. If no `mcp__remote-devices__` tools exist, tell them in one line
to open this chat in the Claude desktop app and connect the folder, then stop.

## 1. Tools
With `device_bash` in the folder:
- `python3 -c "import docx, openpyxl, pdfplumber"` → if missing:
  `pip3 install --user python-docx openpyxl pdfplumber`
- `which soffice || ls /Applications/LibreOffice.app` → if missing, ask the user to install
  LibreOffice (free; `brew install --cask libreoffice` or libreoffice.org). Until then, run
  `tools/` in the cloud workspace (it has LibreOffice): stage the folder's files, work there,
  commit results back with `device_commit_files`, then re-stage and `cmp` to confirm.

## 2. The résumé
Ask for their current résumé as a **.docx** (Word or a Google Doc downloaded as .docx). If they
only have a PDF, offer to rebuild it in `RESUME_TEMPLATE_blank.docx` (a tuned one-page PM layout)
and have them approve it line by line. Save it in the folder root as `<Name>_RESUME_BASE.docx`.

Then write `tools/me/resume_map.json` (start from the example already there):
- `resume`: path relative to `tools/me/` (e.g. `../../Jane_RESUME_BASE.docx`)
- `file_prefix`: e.g. `JDoe` → shipped files are `JDoe_<Company>_<date>.pdf`
- `editable`: one entry per paragraph that may change — `{"i": <index>, "kind":
  "headline|summary|bullet|skills", "section": "<employer or Skills>"}`. Find indices with
  `python3 tools/tailor.py base --all` (temporarily list all bullets to see them). Role/title/date
  lines, the one-line role descriptions, education and certifications stay locked.
- `forbidden` / `only_in_section`: regex rules from their never-mix facts (step 4), e.g.
  `["\\bSalesforce\\b", "Company A", "Salesforce was Company A only"]`.
Verify: `python3 tools/tailor.py base` lists exactly the lines you meant, and the base renders
to 1 page.

## 3. Standing answers
Fill `tools/me/profile.md` with them, table row by row. Ask for anything not on the résumé
(work authorization, sponsorship, relocation, salary rule, start date, EEO default). Also ask for
their filters (titles, max years, locations, target companies) and write them into the `CONFIG`
block at the top of `tools/jobfinder/finder.js` and create two Google Docs if they
use the doc-driven flow (or ask for their links): a **batch doc** (one tab per batch of LinkedIn
links, first tab "Batch 1") and a **key-companies doc** (a "TARGET COMPANIES" tab + one tab per run).
Read the `google-workspace` skill before creating Google files.

## 4. Facts and Experience Notes
- Walk the résumé with them and fill `tools/me/facts.md`: anything easy to mix up between
  employers, how each headline number was measured, renamed companies, things that are NOT true.
- Interview them for 5–8 Experience Notes (`Experience Notes/_TEMPLATE.md` shape), one question at
  a time, phrased so it's always answerable ("Tell me about a time…", "Have you used… — even
  briefly?"). Write their answer **verbatim**. Must-haves: a 30-second "why me" pitch
  (`why-you-pitch.md`), measurement of their top 3 numbers, technical depth, scale, a hard
  prioritization call, cross-functional leadership.

## 5. Preferences
Show `tools/me/preferences.md` and ask which defaults to change. Save their edits there.

## 6. Dry run
Ask for one real job link. Run `fetch-jds` then `resume-tailor` on it end to end, show the score
table and the PDF, and fix whatever they dislike (fold their corrections into `facts.md` or
`preferences.md`). Then write the first handoff doc (see the project's HANDOFF-TEMPLATE) and tell
them setup is done with one line on the daily flow:
"Paste links in your batch doc → tell me 'batch N is ready' → review the score table and the
filled tabs → submit → tell me which you sent."

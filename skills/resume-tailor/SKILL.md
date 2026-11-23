---
name: resume-tailor
description: Tailor the user's résumé to each job description (writer agents, independent lie audit, blind quality review, auto-cut Fit 5 or below), ship the PDFs and fill the applications. Use when they paste a job posting, share a JD file or link, drop JD files in Job Descriptions/, or ask to tailor or apply to a batch.
---

# Résumé tailoring

The user drops job postings in — usually 5–15 at a time. **You build, check and ship one
résumé per job, then fill the applications with the résumé attached.** Their whole surface is:
drop the links, read the score table, review the filled tabs, submit.

They never run a command. If something breaks, diagnose and fix it yourself. Only ask about their
experience or preferences, never the machinery. If `tools/me/resume_map.json` is missing, run the
`job-search-setup` skill first.

Read before starting: the newest `handoff-*.md` in the Claude Project (open items and traps),
`tools/me/preferences.md` (their rules — they override this skill), `tools/me/facts.md`.

## Where it runs
The user's `Resume Checker/` folder, connected to this chat; run commands with `device_bash` in
`tools/`. If the Mac shell is down or lacks LibreOffice, mirror the folder into the cloud workspace
(stage files, run there, `device_commit_files` back from a fresh outputs folder, then re-stage and
`cmp` every file — commits have silently written stale copies). Pass `expectedMtimeMs` on shared
files (`applications.jsonl`, `Application Log.xlsx`, `committed.json`); a rejected commit means
another chat wrote it — re-stage, merge, commit again.

## The loop
1. **Archive first** — `python3 archive_sent.py`. Anything "waiting on you": ask once, grouped.
2. **Fetch** — `fetch-jds` writes `Job Descriptions/PMJD <N>.md`; then
   `python3 tailor.py split "../Job Descriptions/PMJD <N>.md"` → one `batch/<slug>/jd.txt` each.
   A single pasted JD: `tailor.py new <slug> <file>`.
3. **Write** — one general-purpose agent per job, all launched in one message:
   *"cd <folder>/tools. Read briefs/writer.md and follow it exactly for slug `<slug>`
   (<Company>, <Title>)."* Add any new standing fact to the prompt. Each writes
   `batch/<slug>/kw/versions.json` and runs `tailor.py check` until CLEAN. Build every JD given —
   nothing is skipped as a duplicate; two links that resolve to the same posting are built once.
4. **Build** — `python3 tailor.py build <slug>` for each (1 page, no reflow).
5. **Lie audit** — `tailor.py auditpack audits/<date>-b<N>.md <slugs…>`, then ONE fresh agent on
   `briefs/auditor.md` (it sees only changed lines + facts, never the JD). Then
   `tailor.py auditsplit audits/<date>-b<N>.md <auditor.json>` and `tailor.py pick <slug>` for each
   (flagged lines revert to base; best keyword coverage wins). The writer and the auditor must be
   different agents so neither is compromised.
6. **Blind quality review** — make a pack `review<N>/R01…`, each with `resume.txt`
   (`pdftotext -layout batch/<slug>/kw/final_<choice>.pdf`) and `jd.txt`. Add up to 4 calibration
   items from the previous batch (`calibration/b<N-1>/`), shuffle with a fixed seed, keep the key
   separately. ONE reviewer agent on `briefs/quality_review.md` scores Fit / Truth / PM / Clarity
   (each /10). Save pack, key and scores to `calibration/b<N>/` for next time.
7. **Auto-cut Fit ≤ 5** — `tailor.py cut <slug> "Fit <n>: <why>"`; don't ship.
8. **Ship** — `tailor.py ship <slug>` → `Job Specific Resume/<prefix>_<Co>_<date>.pdf`, log row,
   `committed.json`. Rebuild a shipped-but-unsent job: `build` → `pick` → `ship <slug> --replace`.
9. **Report** — one table: Company, Title, Fit, Truth, PM, Clarity, Total /40, keyword coverage,
   with averages, the cuts and why, and one-line over-level notes ("Director, 8+ yrs — built
   anyway"). Then fill every shipped application with `apply-in-browser` — no confirmation needed.
10. **On their word** — "submitted" → `tailor.py confirm <slugs>`; "cut" → `tailor.py cut <slug>
    "<reason>"`; then `archive_sent.py`. A closed browser tab is not a submitted application — ask.

## Experience Notes — their own words
`Experience Notes/*.md` are their answers to interview-style questions. **Their prose is never
rewritten.** `supports:` tags are matched, never displayed; keep them distinctive.
`explicitly_denies:` is a hard stop everywhere. When a batch shows the same unbacked requirement
again and again, ask them about it and file the answer as a new note.

## Things that will bite you
- **Fix the résumé before the tabs go back.** Once submitted, the attached PDF can't change.
- **Never edit the base résumé casually.** Only at their request, with a backup in `Archive/`.
  After any change: re-run `tailor.py base`, check indices in `resume_map.json`, render to 1 page.
- **Other chats may write to the same folder.** Re-stage shared files right before writing.
- **Report weak evidence rather than papering over it.** A fabricated claim they must defend in an
  interview is never the answer.
- End the session with a handoff doc in the Project: batch number, what shipped, what's waiting on
  them, new rules they gave, anything that broke.

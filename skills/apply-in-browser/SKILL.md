---
name: apply-in-browser
description: Open one browser tab per tailored résumé and fill each job application up to the submit button, résumé attached. Runs automatically after résumé tailoring for every résumé that survived the review cut; also when the user says to apply or run a built batch in the browser.
---

# Filling applications in the browser

Runs right after `resume-tailor` ships the PDFs — **automatically, no confirmation needed**.
Fill every shipped résumé (everything that survived the Fit ≤ 5 cut). One tab per job; fill
everything answerable; **attach the tailored résumé every time**; stop at the submit button and
hand the tabs back. Use the browser the user prefers (read the `chrome-browser` or
`built-in-browser` skill first).

All answers come from `tools/me/profile.md` (standing answers), the résumé, `tools/me/facts.md`
and `Experience Notes/`. Their rules in `tools/me/preferences.md` override this skill.

## Hard limits
- **Never click a final submit.** The user submits — even if they say "apply and submit"; the last
  screen carries attestations in their name.
- **Never type a password or create an account**, SSO included. Stop at the wall and say so.
- **Never tick an attestation, terms, privacy-consent, data-consent or marketing opt-in box**
  without asking for that site. Cookie banners: always Decline / Reject All. SMS consent: always No.
- **E-signature / "Full Name" signature boxes** are attestations — leave them.
- **Never invent a fact.** Anything about identity or history not on file → leave blank, report it.
- **Ask, don't decide**, when the real answer isn't clearly known: no option matches, desired pay
  with no posted range and no rule in profile.md, opinion questions.

## Voluntary self-identification — the profile's EEO rule (default: always decline)
Every EEO question — gender, race, ethnicity / Hispanic-Latino, veteran, disability, sexual
orientation — gets the **decline option** ("Decline to self-identify", "I don't wish to answer",
"Prefer not to say"…). Never leave them blank. This includes saved answers on aggregator profiles
(Ladders, LinkedIn, Indeed, Workday): change any other saved answer to decline.

Dropdowns: open each, read the options, pick the decline option, verify the shown value. Radio
groups in one call:

```js
const pat=/declin|not (want|wish) to|don'?t wish|do not wish|choose not to|prefer not|not to (self[- ]?identify|disclose|answer|state)/i;
const groups={};document.querySelectorAll('input[type=radio]').forEach(r=>{
  const t=((r.labels&&r.labels[0]&&r.labels[0].innerText)||r.value||'');
  if(pat.test(t)){ (r.labels&&r.labels[0]||r).click(); groups[r.name]=t.trim(); }
});
JSON.stringify(groups)
```
A page with no decline option: tick "I do not want to answer"; if truly none, leave it and report it.

## Free-text answers — draft them
"Why us?", "What excites you?", cover-letter boxes: **write a draft, fill it, and list every drafted
field in the report** so they read it before submitting.
- 80–150 words, first person, plain, their voice — the way a person would answer, never template
  filler. One or two concrete proof points with real figures from the résumé or Experience Notes,
  tied to what the posting asks for. No clichés, no claims beyond the record.
- "Why you?": combine the résumé with their pitch (`Experience Notes/why-you-pitch.md`); use the
  résumé's numbers if the two differ.
- "Which of our values…": fetch the company's careers page for the real value names.
- Optional "why are you leaving" → blank. Opinion questions with no right answer on file → ask.
- Some companies forbid AI-written application answers — check the posting and flag those drafts
  for the user to rewrite in their own words.

## Setup
1. Stage every PDF being applied with in one `device_stage_files` call; upload the staged
   `/mnt/user-data/uploads/...` path (file upload can't take a device path).
2. Load the browser tools in ONE ToolSearch call (include javascript, batch, file upload, find,
   form input).
3. Get the tab context first. Never reuse tab ids from an earlier session.

## Finding the form
The apply URL is on the `[Apply](…)` / `ATS:` lines of the batch's `PMJD <N>.md`, or in
`batch/<slug>/jd.txt` / `versions.json`.
- **LinkedIn** `/jobs/view/<id>/` → "Apply on company website" is the reliable route.
- **Greenhouse**: open `job-boards.greenhouse.io/embed/job_app?for=<board>&token=<id>` directly.
  No id? `boards-api.greenhouse.io/v1/boards/<board>/jobs` lists them.
- **Recruiter / aggregator pages** wall the apply behind sign-up. The page usually names the real
  employer — apply on the employer's own ATS instead.
- **Email-only postings**: create a Gmail draft (never send) with a short drafted note; tell the
  user to attach the PDF.
- **Short links** (`grnh.se`…) are often blocked; follow once and work from the resolved URL.

**Site permissions are per tab and expire.** "Navigation to this domain is not allowed" or a denied
screenshot means the user must allow that site. Don't retry more than once — collect blocked sites
and ask in one message.

## Per-ATS

**Ashby** — `form_input` works on Name/Email/URL/textarea; upload to the input
labelled "Resume", never "Autofill from resume". Yes/No buttons: `find` their refs
and click by ref (reliable), then verify with `aria-pressed`.
Some Yes/No questions are plain textareas — type "Yes"/"No". Location comboboxes:
click, type, wait, click the option, verify the input value (the site may expand "City, State" to "City, State, United States"). School search: type the school's full name, read `[role=option]`, click the first (a shorter query surfaces
other colleges). Checkbox groups (preferred office): click the `label`. List questions
with `[...document.querySelectorAll('[class*=fieldEntry]')]`.

**Greenhouse** — list fields with their labels in one JS call (id, type,
`label[for=id]`). Fill **text fields and textareas in one JS call** with the native
value setter plus `input`/`change`/`blur` events — it sticks. **Comboboxes**: focus
the input by id in JS, `computer type` the option text, Enter. Where typing finds
nothing ("No options"), clear it, press Down and read the option list
(`[...document.querySelectorAll('[class*=option]')].map(o=>o.innerText)`) — states can
be codes (`NY`). Verify every selection with
`[...document.querySelectorAll('[class*=single-value]')].map(e=>e.innerText)` and
count them against what you set. `country` is the phone dial code (+1). Upload the
résumé first. Never `get_page_text` a Greenhouse page — it returns the whole JD.

**Lever** — single page; fill by `name`; un-hide `#resume-upload-input`, then upload.
The parser wipes `location` after upload — refill. Confirmation is `/thanks`. A
posting can 404 on Lever while LinkedIn still lists it : check
`jobs.lever.co/<co>` for the title; if it's gone, report it as closed.

**Oracle HCM** (used by many large enterprises) — Apply Now → email +
terms checkbox (ask first) → emailed code (the user's). Decline cookies ("Reject All"). New
profile: one long page — street address with ZIP auto-filling city/state/county; pill
buttons for screening questions; Education via ADD EDUCATION; EEO decline; E-Signature
is the user's. **Returning profile**: four steps, all prefilled from the saved profile
(screening radios and EEO declines included). Step 1: Remove Resume, then upload this
job's PDF into "Upload Resume" (`find` it). Check each step's values with JS against
the standing answers, Next ×3, stop at E-Signature.

**Workday** — Decline the cookie banner, then use `find` for "Apply Manually" (the
layout shifts after the banner, so a coordinate click can hit the wrong button).
Apply Manually opens Create Account/Sign In — the user's wall. After they sign in: My
Information → Experience → Questions → Disclosures → Self Identify → Review. Phone type
Cellular, bare-digit phone. Dropdowns need real clicks; dates: click the month box,
type MMYYYY. Field of Study is a virtualised list — typing a partial word auto-picks
the wrong one (a partial word can select an unrelated field): scroll
`[data-automation-id=activeListContainer]` to the option instead. Salary fields take
digits only. Scope dropdown queries to `main` (the header Settings button
also has aria-haspopup=listbox).

**Eightfold** (`*.eightfold.ai` and company-branded Eightfold sites) — Apply Now opens one page. The
native value setter shows text but doesn't register: triple-click each field and type.
Attaching the résumé raises a "Candidate Privacy … I acknowledge" popup — ask first. Dropdowns: click, then read `[role=option]` coordinates
in JS before clicking — the page scrolls when a list opens, so a blind click can
pick the wrong option. Phone code and Country are separate typeaheads; State appears after
Country. Self-ID: tick "I choose not to disclose" in each checkbox group and pick it in
the three dropdowns. "Submit application" sits in a sticky bottom bar — keep clicks
clear of it.

**SmartRecruiters** (`jobs.smartrecruiters.com` → `oneclick-ui`) —
"I'm interested" opens the form; every field is inside shadow DOM, invisible to
`find`/`read_page`. List inputs by walking `shadowRoot`s in JS and keep them in
`window.__inps`. Résumé: append a temporary light-DOM `<input type=file>` (give it an
aria-label), `find` it, `file_upload` to it, then in JS set the shadow Resume input's
`.files` to the temp input's files, dispatch `input` and `change` (`composed:true`),
and remove the temp input. Text: `focus()` the shadow input in JS, then `computer
type`. ZIP is a typeahead → pick the "<ZIP>, <City>, <ST>, USA" option. Experience/Education "Add"
sections are optional. Next → page 2 holds the privacy-notice declaration checkbox and
Submit — both the user's.

**Avature** (`<company>.avature.net`) — opens on "Already registered?" sign-in.
A password manager may autofill credentials; never click Log in —
the user signs in. After that, "Confirm application" shows the saved profile: set Home
state, Text Message Consent → No (check it; it may default to Yes), Talent Community → No; the
Privacy Policy Agreement checkbox and Next are the user's. Its cookie banner has no Reject —
leave it alone.

**Dayforce** — "Apply without an Account". Any résumé upload runs the parser, which
creates duplicate education/employment rows and wrong fields (wrong completion status, invented fields) — fix or delete those rows.
Education and employment start dates are required; dates not on file → ask the user.

**Rippling** — résumé upload parses names, email, phone and company correctly;
Location is a typeahead (type "City, ST", pick the "City, ST, USA" option). The SMS radios
have no labels: click the one with `value="false"` (No). EEO dropdowns (Gender, Race,
Hispanic/Latino, Veteran) all have "Choose not to disclose" — the Race list scrolls.
The "Apply" button submits and accepts Rippling's terms — the user's.

**Personio** — plain fields by `name`; screening selects use `custom_option_*` values.

**Ladders Apply4Me** — one account-wide résumé: fill and have the user submit one Ladders
job before uploading the next job's résumé. Re-check saved answers each time (start
date, desired pay, Voluntary Self-Identification → decline).

**iCIMS** — login (the user), then the form is in a same-origin iframe that `find` can't see:
fill through `document.querySelector('iframe').contentDocument` with jQuery
`.trigger('change')`. Cascading selects reset their child — set the child last. The
résumé upload can't be reached; the user clicks it.

**LinkedIn Easy Apply** — the modal is invisible to `find`/`read_page`. Clicking twice
raises "Save this application?": choose Save, then dismiss with the dialog's X. Fill by
coordinate or hand it over; don't fight it.


## Order of work
1. Read the contact line from the base résumé and profile.md; stage the PDFs.
2. One tab per job: résumé upload → contact → re-verify contact after upload (parsers overwrite
   fields) → location → screening questions → drafted free text → EEO: decline every question.
3. Stop at any sign-in, consent or submit screen.
4. Don't stop to ask mid-batch — finish every tab, then put every open question in the report (or
   ONE AskUserQuestion if they're present).
5. Report a numbered list: company, score, what's filled, **which answers you drafted**, what's
   left, what needs their hands (submit, consent boxes, accounts, signatures, missing dates). Flag
   answers that assume a move or commute so they can change them.
6. The user may work in the tabs while you fill: re-read the tab context before each tab. A
   thanks/confirmation page means they submitted it — don't touch it. A closed tab is NOT a
   submitted application — ask which were sent.
7. Record their answer at once: "submitted" → `tailor.py confirm <slugs>`; "cut" →
   `tailor.py cut <slug> "<reason>"`; then `python3 archive_sent.py`.
8. Learn as you go: when a site teaches you a new trick (a field that won't take input, a parser
   quirk), add a line to the Per-ATS section via a handoff note so the next run starts smarter.

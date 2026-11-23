---
name: fetch-jds
description: Pull job descriptions from the LinkedIn links in the user's batch Google Doc (newest Batch tab), save them as one batch file, add the next Batch tab, then run résumé tailoring. Use before resume-tailor whenever JDs arrive as links.
---

# Fetch JDs from links

The user pastes LinkedIn job links into their **batch doc** (URL in `tools/me/profile.md`), one
tab per batch ("Batch 1", "Batch 2", …). When they say the next batch is ready: read the newest
tab, pull every posting, save them as `Job Descriptions/PMJD <N>.md`, add the next empty tab, then
run `resume-tailor` straight through — no stop in between. (Pasted JD text or a JD file works
too: skip to step 4.)

Read the browser skill (`built-in-browser` or `chrome-browser`) before the first browser step and
load its tools in one ToolSearch. The user should be signed in to LinkedIn in that browser.

## 0. Archive the last batch first — every run
1. Record what the user told you: "sent/submitted" → `tailor.py confirm <slugs>`; "cut/skip" →
   `tailor.py cut <slug> "<reason>"`.
2. `python3 tools/archive_sent.py`. Anything it lists as waiting: ask once, grouped by batch.

## Keep their LinkedIn account safe — rules, not tips
LinkedIn bans automated access and restricts accounts that look like bots.
- **Only `linkedin.com/jobs/view/<id>/` pages.** For search URLs take the `currentJobId` and open
  the job view. No feeds, profiles or company pages. Never click Apply, Easy Apply, Save or Follow.
- **One tab, one page at a time, several seconds apart.** Never parallel. At most 15 links per run.
- **Stop at once** on a sign-in wall, security check, CAPTCHA or "unusual activity". Never solve a
  CAPTCHA or sign in for them.
- **No WebFetch on LinkedIn**, and never use WebFetch for JD text at all (it summarises).

## 1. Read the links
Read the batch doc with the Google Drive connector (`read_file_content`, comments included); every
tab comes back as a `# Batch N` section. Take the **last** one; pull ids with
`currentJobId=(\d+)` or `jobs/view/(\d+)`; keep their order; drop exact duplicates.
An id already in `Job Descriptions/` or `JD Archive/` → reuse that text and flag it. An id whose
batch folder has `committed.json` → already built; flag, don't rebuild unless asked.

## 2. Per link: open LinkedIn, get the apply link
Open the job view in one tab (navigate the same tab for later links) and run this in the page.
It returns title, company, place, the company apply link and the LinkedIn body:

```js
for(let k=0;k<24&&!(document.querySelector('main')||document.body).innerText.includes('About the job');k++)await new Promise(r=>setTimeout(r,500));
const sha1=async s=>[...new Uint8Array(await crypto.subtle.digest('SHA-1',new TextEncoder().encode(s)))].map(b=>b.toString(16).padStart(2,'0')).join('');
const txt=(document.querySelector('main')||document.body).innerText;
const blocked=/authwall|checkpoint|login|signup/.test(location.pathname)||/Sign Up|Sign In|Security Verification/i.test(document.title);
const id=(location.pathname.match(/jobs\/view\/(\d+)/)||[])[1]||null;
const [title,company]=document.title.replace(/ \| LinkedIn$/,'').split(' | ');
const lines=txt.split('\n').map(s=>s.trim()).filter(Boolean);
const meta=lines.find(l=>/ · /.test(l)&&/ago|Reposted|Posted/i.test(l))||'';
const place=meta.split(' · ')[0]||'';
const workplace=lines.slice(0,30).find(l=>/^(Remote|Hybrid|On-site)$/.test(l))||'';
let body='';const s=txt.indexOf('About the job');
if(s>=0){body=txt.slice(s+13);const e=Math.min(...['\n… more','\nBenefits found in job post','\nSet alert for similar jobs','\nSee how you compare','\nAbout the company'].map(m=>{const i=body.indexOf(m);return i<0?Infinity:i}));if(isFinite(e))body=body.slice(0,e);}
body=body.replace(/\r/g,'').replace(/ /g,' ').replace(/[ \t]+$/gm,'').replace(/\n{3,}/g,'\n\n').trim();
const a=[...document.querySelectorAll('a')].find(a=>/apply on company website/i.test(a.getAttribute('aria-label')||''));
let applyUrl=null;if(a){try{applyUrl=new URL(a.href).searchParams.get('url')||a.href}catch(_){applyUrl=a.href}}
const easy=!a&&/Easy Apply/.test(lines.slice(0,40).join(' '));
const closed=/No longer accepting applications/i.test(txt);
({blocked,id,title,company,place,workplace,applyUrl,easy,closed,len:body.length,sha1:await sha1(body),body})
```

`blocked` → stop. `closed` → skip and report. The description only loads while the browser pane
is visible (`len: 0` means hidden) — never reload a page more than once.

## 3. Company site first, LinkedIn text as fallback
Prefer the employer's own posting, via the ATS's public JSON, parsed in the page. End every
extractor with the same cleanup (`\r`, non-breaking spaces, trailing spaces, 3+ newlines).
- **Greenhouse** — `https://boards-api.greenhouse.io/v1/boards/<b>/jobs/<id>`; decode `content`
  HTML into a div and read its `innerText`.
- **Ashby** — `https://api.ashbyhq.com/posting-api/job-board/<org>`; match `jobs[].id`; body =
  `descriptionPlain`.
- **Workday** — `https://<t>.wd1.myworkdayjobs.com/wday/cxs/<t>/<site>/job/<path>`; body =
  `jobPostingInfo.jobDescription`.
- **Lever** — `https://api.lever.co/v0/postings/<co>/<uuid>`; `descriptionPlain` + `lists[]` +
  `additionalPlain`.
- **Plain company page** — `main`/`article` `innerText`.
- Use the company text only if its title matches LinkedIn's; otherwise use the LinkedIn body.
  Neither → report the job as failed; never guess.
For Greenhouse also record `ATS: https://job-boards.greenhouse.io/embed/job_app?for=<b>&token=<id>`.

## 4. Save each job, verified
Get each body onto disk **exactly** — never retype it. For big results, pad the page's return value
past ~50 KB so the tool saves it to a file, then copy from that file. Write
`tools/_fetch/<id>.txt` (body) and `tools/_fetch/<id>.json`
(`{"id","title","company","place","workplace","apply","ats","source"}`), and check the body's
sha1 against the one the page computed. Mismatch → find and fix the differing line. Never ship an
unverified body.

## 5. Assemble
Write `Job Descriptions/PMJD <N>.md`: per job a `# Tab <n>` heading, then
`[<title>](https://www.linkedin.com/jobs/view/<id>/)`, `<company> • <place> (<workplace>)`,
`[Apply](<url>)`, optional `ATS: <url>`, `JD source: <source>`, a blank line, `About the job`, and
the body. Then `python3 tools/tailor.py split "Job Descriptions/PMJD <N>.md"` must list every job.

## 6. Add the next tab in the doc
Use the browser where they're signed in to Google: open the doc → **+** next to "Document tabs" →
rename the new tab `Batch <N+1>`. Verify with the Drive connector, then close the tab.

## 7. Report one line, then tailor
*"Pulled N JDs (k company sites, m LinkedIn, r reused). Skipped: …. Batch <N+1> tab added."*
Then run `resume-tailor`.

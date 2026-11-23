#!/usr/bin/env python3
"""Résumé tailoring tool: JD keyword match + an independent lie audit.

Works on YOUR résumé (.docx). Claude maps it once during setup (me/resume_map.json),
then for every job:

  1. writer agent  -> batch/<slug>/kw/versions.json  (A light touch, B heavier)
  2. check         -> rule check the writer runs itself until it prints CLEAN
  3. build         -> renders A and B (must stay 1 page, no reflow)
  4. auditor agent -> a SEPARATE agent, given only the changed lines + your facts
                      (never the JD) flags outright lies
  5. pick          -> flagged lines go back to your base line, best keyword coverage wins
  6. ship          -> Job Specific Resume/<prefix>_<Company>_<date>.pdf, log row, committed.json

    python3 tailor.py base [--all]                 editable lines with indices
    python3 tailor.py new <slug> <jd-file>          make batch/<slug>/jd.txt from a JD file
    python3 tailor.py split <PMJD file>             one batch/<slug>/ per "# Tab N" posting
    python3 tailor.py check <slug>
    python3 tailor.py build <slug>
    python3 tailor.py auditpack <out.md> <slug> [<slug> ...]
    python3 tailor.py auditsplit <out.md> <auditor.json>
    python3 tailor.py pick <slug>
    python3 tailor.py ship <slug> [--replace]
    python3 tailor.py cut <slug> "<reason>"        recorded, résumé not shipped / removed from log
    python3 tailor.py confirm <slug> [<slug> ...]   you said it was submitted

versions.json:
{"company": "...", "title": "<job title as posted>", "apply_url": "<optional>",
 "ledger": {"must_haves": ["<JD term>", ...], "nice_to_haves": [...]},
 "versions": [{"id": "A", "rewrites": [{"i": <paragraph index>, "text": "<new line>"}]},
              {"id": "B", "rewrites": [...]}]}

Needs: python-docx, openpyxl, pdfplumber, and LibreOffice (soffice) for rendering.
"""
import os, re, sys, json, copy, shutil, datetime, subprocess, tempfile, glob, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
CFG_PATH = os.path.join(HERE, "me", "resume_map.json")
BATCH = os.path.join(HERE, "batch")
OUT_DIR = os.path.join(ROOT, "Job Specific Resume")
LOG_JSONL = os.path.join(HERE, "applications.jsonl")
LOG_XLSX = os.path.join(ROOT, "Application Log.xlsx")

WEAK_OPENERS = {"helped", "worked", "assisted", "supported", "responsible", "participated"}
DEFAULT_CORE = ["roadmap", "agile", "strategy", "workflow", "stakeholder", "discovery",
                "requirements", "metrics", "cross-functional", "prioritization"]


# ---------------------------------------------------------------- config / docx
def cfg():
    if not os.path.exists(CFG_PATH):
        sys.exit("No me/resume_map.json yet. Run the job-search-setup skill first.")
    c = json.load(open(CFG_PATH, encoding="utf-8"))
    c.setdefault("keyword_cap", 4)
    c.setdefault("core_words", DEFAULT_CORE)
    c.setdefault("forbidden", [])          # [["regex", "why"]]
    c.setdefault("only_in_section", [])    # [["regex", "Section name", "why"]]
    c.setdefault("bold_terms", True)
    c.setdefault("max_pages", 1)
    c["_editable"] = {int(e["i"]): e for e in c["editable"]}
    return c


def resume_path(c):
    p = c["resume"]
    return p if os.path.isabs(p) else os.path.abspath(os.path.join(HERE, "me", p))


def load_doc(c):
    from docx import Document
    return Document(resume_path(c))


def set_text(par, text, bold_terms=()):
    """Replace a paragraph's text, keeping its first run's formatting; bold the given terms."""
    runs = par.runs
    if not runs:
        par.add_run(text)
        return
    base_rpr = copy.deepcopy(runs[0]._r.rPr) if runs[0]._r.rPr is not None else None
    for r in runs:
        r._r.getparent().remove(r._r)
    pieces = [(text, False)]
    if bold_terms:
        pat = re.compile("|".join(re.escape(t) for t in sorted(set(bold_terms), key=len, reverse=True)
                                  if t.strip()), re.I) if any(t.strip() for t in bold_terms) else None
        if pat:
            pieces, last = [], 0
            for m in pat.finditer(text):
                if m.start() > last:
                    pieces.append((text[last:m.start()], False))
                pieces.append((m.group(0), True))
                last = m.end()
            if last < len(text):
                pieces.append((text[last:], False))
    for seg, b in pieces:
        run = par.add_run(seg)
        if base_rpr is not None:
            run._r.insert(0, copy.deepcopy(base_rpr))
        if b:
            run.bold = True


def render(docx_path):
    """docx -> pdf next to it. Returns (pdf_path, pages, text_lines)."""
    out = os.path.dirname(docx_path)
    prof = tempfile.mkdtemp(prefix="lo_")
    subprocess.run(["soffice", f"-env:UserInstallation=file://{prof}", "--headless",
                    "--convert-to", "pdf", "--outdir", out, docx_path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=180)
    shutil.rmtree(prof, ignore_errors=True)
    pdf = os.path.splitext(docx_path)[0] + ".pdf"
    import pdfplumber
    with pdfplumber.open(pdf) as p:
        pages = len(p.pages)
        lines = sum(len([l for l in (pg.extract_text() or "").splitlines() if l.strip()]) for pg in p.pages)
    return pdf, pages, lines


# ---------------------------------------------------------------- helpers
def slug_dir(slug, *parts):
    return os.path.join(BATCH, slug, *parts)


def versions(slug):
    p = slug_dir(slug, "kw", "versions.json")
    if not os.path.exists(p):
        sys.exit(f"missing {p}")
    return json.load(open(p, encoding="utf-8"))


def numbers(s):
    return sorted(re.findall(r"\$?\d[\d,.]*[%KkMm+x]?", s))


def stem(w):
    w = w.lower().replace("-", " ")
    w = re.sub(r"\s+", " ", w).strip()
    return re.sub(r"(ies|es|s)$", "", w) if len(w) > 3 else w


def count_term(term, lines):
    """Uses of a term on the page; a use that starts a line/sentence doesn't count."""
    t = re.escape(stem(term)).replace(r"\ ", r"[\s-]")
    pat = re.compile(rf"(?<![\w]){t}(?:ies|es|s|ed|ing|ized|ization)?(?![\w])", re.I)
    n = 0
    for line in lines:
        for m in pat.finditer(line):
            before = line[:m.start()].rstrip()
            if before == "" or before.endswith((".", "!", "?")):
                continue
            n += 1
    return n


def apply(c, rewrites, bold=()):
    doc = load_doc(c)
    for rw in rewrites:
        set_text(doc.paragraphs[int(rw["i"])], rw["text"], bold)
    return doc


def page_lines(doc):
    return [p.text for p in doc.paragraphs if p.text.strip()]


def bold_list(c, v):
    if not c["bold_terms"]:
        return ()
    led = v.get("ledger", {})
    return [t for t in led.get("must_haves", []) + led.get("nice_to_haves", []) if len(t) > 1]


# ---------------------------------------------------------------- commands
def cmd_base(args):
    c = cfg()
    doc = load_doc(c)
    for i, p in enumerate(doc.paragraphs):
        e = c["_editable"].get(i)
        if e or "--all" in args:
            tag = f"{e['kind']}/{e.get('section', '')}" if e else "locked"
            print(f"[{i}] ({tag}) {p.text}")


def cmd_new(args):
    slug, src = args[0], args[1]
    os.makedirs(slug_dir(slug, "kw"), exist_ok=True)
    shutil.copy(src, slug_dir(slug, "jd.txt"))
    print(slug_dir(slug, "jd.txt"))


def cmd_split(args):
    """Split a batch file with '# Tab N' headings into one batch/<slug>/jd.txt per posting."""
    path = args[0]
    txt = open(path, encoding="utf-8").read()
    parts = re.split(r"(?m)^# Tab \d+\s*$", txt)
    made = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.search(r"jobs/view/(\d+)", part)
        title = re.search(r"^\[(.+?)\]", part, re.M)
        comp = re.search(r"^\[.+?\]\(.+?\)\s*\n(.+?) •", part, re.M)
        co = re.sub(r"[^A-Za-z0-9]", "", comp.group(1)) if comp else "Company"
        jid = m.group(1)[-6:] if m else hashlib.sha1(part.encode()).hexdigest()[:6]
        slug = f"{co}_{jid}"
        os.makedirs(slug_dir(slug, "kw"), exist_ok=True)
        open(slug_dir(slug, "jd.txt"), "w", encoding="utf-8").write(part + "\n")
        made.append((slug, title.group(1) if title else ""))
    json.dump({"source": os.path.basename(path), "slugs": [s for s, _ in made]},
              open(os.path.join(BATCH, f"{os.path.splitext(os.path.basename(path))[0]}.json"), "w"), indent=1)
    for s, t in made:
        print(s, "|", t)


def check_version(c, base_doc, v, ver, render_it=True):
    issues = []
    ed = c["_editable"]
    base = {i: p.text for i, p in enumerate(base_doc.paragraphs)}
    for rw in ver.get("rewrites", []):
        i = int(rw["i"])
        if i not in ed:
            issues.append(f"line {i} is locked")
            continue
        if numbers(rw["text"]) != numbers(base[i]):
            issues.append(f"line {i}: numbers changed {numbers(base[i])} -> {numbers(rw['text'])}")
        if ed[i]["kind"] == "bullet" and ":" in rw["text"]:
            issues.append(f"line {i}: no colons in bullets")
        for pat, why in c["forbidden"]:
            if re.search(pat, rw["text"]):
                issues.append(f"line {i}: {why}")
        for pat, section, why in c["only_in_section"]:
            if re.search(pat, rw["text"]) and ed[i].get("section") != section:
                issues.append(f"line {i}: {why}")
    doc = apply(c, ver.get("rewrites", []))
    text = {i: p.text for i, p in enumerate(doc.paragraphs)}
    # openers
    seen = {}
    for i, e in sorted(ed.items()):
        if e["kind"] != "bullet" or not text[i].strip():
            continue
        w = re.sub(r"\W", "", text[i].split()[0]).lower()
        if w in WEAK_OPENERS:
            issues.append(f"line {i}: weak opener '{w}'")
        key = (e.get("section"), w)
        if key in seen:
            issues.append(f"line {i}: starts with '{w}' like line {seen[key]} in the same section")
        seen[key] = i
    # keyword cap
    lines = page_lines(doc)
    led = v.get("ledger", {})
    terms = set(led.get("must_haves", []) + led.get("nice_to_haves", []) + c["core_words"])
    for t in sorted(terms):
        n = count_term(t, lines)
        if n > c["keyword_cap"]:
            issues.append(f"'{t}' used {n}x (cap {c['keyword_cap']}) — vary the wording")
    # render: page count and no reflow
    if render_it:
        tmp = slug_dir(v["_slug"], "kw", f"_check_{ver['id']}.docx")
        doc.save(tmp)
        _, pages, nlines = render(tmp)
        bpages, blines = c.get("_base_render") or (None, None)
        if pages > c["max_pages"]:
            issues.append(f"renders to {pages} pages")
        if blines is not None and nlines != blines:
            issues.append(f"layout reflowed: {nlines} text lines vs base {blines} — a line wrapped or shrank; shorten/lengthen it")
    return issues


def base_render(c):
    tmp = os.path.join(HERE, "me", "_base_render.docx")
    load_doc(c).save(tmp)
    _, pages, lines = render(tmp)
    c["_base_render"] = (pages, lines)


def cmd_check(args):
    c = cfg()
    base_render(c)
    base_doc = load_doc(c)
    clean = True
    for slug in args:
        v = versions(slug)
        v["_slug"] = slug
        for ver in v["versions"]:
            iss = check_version(c, base_doc, v, ver)
            for x in iss:
                print(f"{slug} {ver['id']}: {x}")
            clean = clean and not iss
    print("CLEAN" if clean else "FIX THE ABOVE")


def cmd_build(args):
    c = cfg()
    for slug in args:
        v = versions(slug)
        for ver in v["versions"]:
            doc = apply(c, ver.get("rewrites", []), bold_list(c, v))
            p = slug_dir(slug, "kw", f"build_{ver['id']}.docx")
            doc.save(p)
            _, pages, _ = render(p)
            print(slug, ver["id"], f"{pages} page(s)")


def cmd_auditpack(args):
    out, slugs = args[0], args[1:]
    c = cfg()
    base = {i: p.text for i, p in enumerate(load_doc(c).paragraphs)}
    md, key = ["# Audit pack — changed lines only. Flag outright lies.\n"], {}
    for n, slug in enumerate(slugs, 1):
        label = f"J{n}"
        key[label] = slug
        v = versions(slug)
        md.append(f"\n## {label}\n")
        for ver in v["versions"]:
            md.append(f"\n### Version {ver['id']}\n")
            for rw in ver.get("rewrites", []):
                i = int(rw["i"])
                sec = c["_editable"].get(i, {}).get("section", "")
                md.append(f"- [line {i}] ({sec})\n  - base: {base[i]}\n  - new:  {rw['text']}")
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump(key, open(out + ".key.json", "w"), indent=1)
    print(out, len(slugs), "jobs")


def cmd_auditsplit(args):
    key = json.load(open(args[0] + ".key.json"))
    res = json.load(open(args[1], encoding="utf-8"))
    for label, slug in key.items():
        json.dump(res.get(label, {}), open(slug_dir(slug, "kw", "audit.json"), "w"), indent=1)
        print(slug, {k: len(x) for k, x in res.get(label, {}).items()})


def coverage(v, lines):
    led = v.get("ledger", {})
    must, nice = led.get("must_haves", []), led.get("nice_to_haves", [])
    page = " ".join(lines).lower()
    score = mx = 0.0
    for rank, t in enumerate(must):
        w = 2.0 * (len(must) - rank) / max(1, len(must)) + 1
        mx += w
        score += w if stem(t) in stem(page) or t.lower() in page else 0
    for rank, t in enumerate(nice):
        w = 0.5 * (len(nice) - rank) / max(1, len(nice)) + 0.5
        mx += w
        score += w if t.lower() in page else 0
    return round(score, 2), round(mx, 2)


def cmd_pick(args):
    c = cfg()
    base_render(c)
    base_doc = load_doc(c)
    for slug in args:
        v = versions(slug)
        v["_slug"] = slug
        ap = slug_dir(slug, "kw", "audit.json")
        audit = json.load(open(ap)) if os.path.exists(ap) else {}
        best = None
        for ver in v["versions"]:
            flagged = {int(re.search(r"\d+", f["ref"]).group()) for f in audit.get(ver["id"], [])
                       if re.match(r"line \d+", f["ref"])}
            kept = [rw for rw in ver.get("rewrites", []) if int(rw["i"]) not in flagged]
            fixed = dict(ver, rewrites=kept)
            doc = apply(c, kept)
            cov = coverage(v, page_lines(doc))
            iss = check_version(c, base_doc, v, fixed, render_it=False)
            cand = (0 if iss else 1, cov[0], ver["id"], fixed, sorted(flagged), cov)
            if best is None or cand[:2] > best[:2]:
                best = cand
        _, _, vid, fixed, flagged, cov = best
        doc = apply(c, fixed["rewrites"], bold_list(c, v))
        p = slug_dir(slug, "kw", f"final_{vid}.docx")
        doc.save(p)
        _, pages, _ = render(p)
        json.dump({"choice": vid, "reverted_lines": flagged, "coverage": cov, "pages": pages},
                  open(slug_dir(slug, "kw", "pick.json"), "w"), indent=1)
        print(f"{slug}: picked {vid}, coverage {cov[0]}/{cov[1]}, reverted {flagged}, {pages} page(s)")


def company_key(name):
    return re.sub(r"[^A-Za-z0-9]", "", name.title()) or "Company"


def cmd_ship(args):
    c = cfg()
    slug = args[0]
    replace = "--replace" in args
    v = versions(slug)
    pk = json.load(open(slug_dir(slug, "kw", "pick.json")))
    src = slug_dir(slug, "kw", f"final_{pk['choice']}.pdf")
    os.makedirs(OUT_DIR, exist_ok=True)
    date = datetime.date.today().isoformat()
    stemname = f"{c.get('file_prefix', 'Resume')}_{company_key(v['company'])}_{date}"
    dst = os.path.join(OUT_DIR, stemname + ".pdf")
    n = 2
    while os.path.exists(dst) and not replace:
        dst = os.path.join(OUT_DIR, f"{stemname}_v{n}.pdf")
        n += 1
    shutil.copy(src, dst)
    row = {"date": date, "company": v["company"], "title": v["title"], "file": os.path.basename(dst),
           "slug": slug, "apply_url": v.get("apply_url", ""), "coverage": pk["coverage"]}
    if not replace:
        with open(LOG_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        log_append(row)
    json.dump(dict(row, shipped_at=datetime.datetime.now().isoformat(timespec="seconds")),
              open(slug_dir(slug, "kw", "committed.json"), "w"), indent=1)
    print("shipped", dst)


def log_append(row):
    from openpyxl import Workbook, load_workbook
    from openpyxl.styles import Font
    if os.path.exists(LOG_XLSX):
        wb = load_workbook(LOG_XLSX)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Applications"
        ws.append(["#", "Company", "Title", "Date Built", "Resume File", "Status", "Notes"])
        for cell in ws[1]:
            cell.font = Font(bold=True)
        ws.freeze_panes = "A2"
    ws.append([ws.max_row, row["company"], row["title"], row["date"], row["file"], "Built", ""])
    wb.save(LOG_XLSX)


def _set_status(file, status):
    from openpyxl import load_workbook
    if not os.path.exists(LOG_XLSX):
        return
    wb = load_workbook(LOG_XLSX)
    ws = wb.active
    for r in ws.iter_rows(min_row=2):
        if r[4].value == file:
            r[5].value = status
    wb.save(LOG_XLSX)


def cmd_confirm(args):
    for slug in args:
        p = slug_dir(slug, "kw", "committed.json")
        d = json.load(open(p))
        d["confirmed_on"] = datetime.date.today().isoformat()
        json.dump(d, open(p, "w"), indent=1)
        _set_status(d["file"], "Submitted")
        print("confirmed", slug)


def cmd_cut(args):
    slug, reason = args[0], " ".join(args[1:]) or "cut"
    os.makedirs(slug_dir(slug, "kw"), exist_ok=True)
    p = slug_dir(slug, "kw", "committed.json")
    d = json.load(open(p)) if os.path.exists(p) else {"slug": slug}
    d.update(cut_on=datetime.date.today().isoformat(), cut_reason=reason)
    json.dump(d, open(p, "w"), indent=1)
    if d.get("file"):
        _set_status(d["file"], f"Cut: {reason}")
    print("cut", slug, "-", reason)


CMDS = {"base": cmd_base, "new": cmd_new, "split": cmd_split, "check": cmd_check, "build": cmd_build,
        "auditpack": cmd_auditpack, "auditsplit": cmd_auditsplit, "pick": cmd_pick,
        "ship": cmd_ship, "confirm": cmd_confirm, "cut": cmd_cut}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in CMDS:
        print(__doc__)
        sys.exit(1)
    CMDS[sys.argv[1]](sys.argv[2:])

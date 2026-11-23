#!/usr/bin/env python3
"""Clear out sent and cut résumés. Run at the start of every batch.

Reads only the records tailor.py writes (batch/<slug>/kw/committed.json):
  confirmed_on -> Job Specific Resume/<file> moves to Archive/
  cut_on       -> moves to Archive/<stem>_dropped.pdf
  neither      -> stays, listed under "waiting on you"
A batch file in Job Descriptions/ moves to Job Descriptions/JD Archive/ once every job
in it is confirmed or cut. Never overwrites or deletes anything.

    python3 archive_sent.py
"""
import glob, json, os, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "Job Specific Resume")
ARC = os.path.join(ROOT, "Archive")
JDS = os.path.join(ROOT, "Job Descriptions")
JDA = os.path.join(JDS, "JD Archive")


def safe_move(src, dst):
    base, ext = os.path.splitext(dst)
    n = 2
    while os.path.exists(dst):
        dst = f"{base}_{n}{ext}"
        n += 1
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.move(src, dst)
    return dst


def main():
    done, waiting, moved = set(), [], []
    for p in glob.glob(os.path.join(HERE, "batch", "*", "kw", "committed.json")):
        slug = p.split(os.sep)[-3]
        d = json.load(open(p))
        f = d.get("file")
        src = os.path.join(OUT, f) if f else None
        if d.get("confirmed_on"):
            done.add(slug)
            if src and os.path.exists(src):
                moved.append(safe_move(src, os.path.join(ARC, f)))
        elif d.get("cut_on"):
            done.add(slug)
            if src and os.path.exists(src):
                stem, ext = os.path.splitext(f)
                moved.append(safe_move(src, os.path.join(ARC, f"{stem}_dropped{ext}")))
        elif f:
            waiting.append(f)
    for idx in glob.glob(os.path.join(HERE, "batch", "*.json")):
        d = json.load(open(idx))
        src = os.path.join(JDS, d.get("source", ""))
        if d.get("slugs") and all(s in done for s in d["slugs"]) and os.path.isfile(src):
            moved.append(safe_move(src, os.path.join(JDA, d["source"])))
    for m in moved:
        print("moved ->", os.path.relpath(m, ROOT))
    if waiting:
        print("\nWaiting on you (left in place — sent, or cut?):")
        for w in sorted(waiting):
            print("  ", w)
    if not moved and not waiting:
        print("Nothing to archive.")


if __name__ == "__main__":
    main()

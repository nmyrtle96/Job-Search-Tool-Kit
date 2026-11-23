# Resume Checker

Your job-search workspace. Put this folder on your Desktop and connect it to your Claude chat.
Claude runs everything in here; you mostly only open `Job Specific Resume/` and `Application Log.xlsx`.

```
Resume Checker/
├── <You>_RESUME_BASE.docx        your approved base résumé (setup creates it)
├── RESUME_TEMPLATE_blank.docx    a tuned one-page PM layout, if you want to start fresh
├── Application Log.xlsx          one row per résumé shipped (created on first ship; add your own columns)
├── Job Specific Resume/          tailored PDFs waiting for you to submit
├── Archive/                      sent and cut résumés, old versions, backups
├── Experience Notes/             your own answers, used as evidence (never rewritten)
├── Job Descriptions/             one PMJD <N>.md per batch  └── JD Archive/  └── Key Companies/
└── tools/
    ├── tailor.py                 build / check / audit / pick / ship
    ├── archive_sent.py           moves sent and cut files out of the way
    ├── briefs/                   instructions for the writer, auditor and reviewer agents
    ├── me/                       YOUR data: resume_map.json, profile.md, facts.md, preferences.md
    ├── jobfinder/                careers-site finder for the key-companies run
    └── batch/<slug>/             per-job working files (created as you go)
```

Requirements on the Mac: Python 3 with `python-docx openpyxl pdfplumber`, and LibreOffice.
Claude installs/checks these during setup.

Privacy: everything personal lives in `tools/me/`, `Experience Notes/` and your résumé. Don't share
those if you pass this kit on.

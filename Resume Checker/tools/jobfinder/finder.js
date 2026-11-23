// Job finder — careers-site extractors for the key-companies run.
// Works with any company on Greenhouse, Ashby, Lever or Workday (public job APIs).
// Paste this whole file into a browser tab on the site's origin (see ORIGIN_FOR), then call:
//   await __JF.run({type:'greenhouse', board:'<board>'}, {seen:[...ids], since:'YYYY-MM-DD'})
//   types: greenhouse {board} · ashby {org} · lever {co} · workday {host, tenant, site}
//     (workday host e.g. 'acme.wd5.myworkdayjobs.com', site = the path segment after the host)
// It returns compact rows only. Full JD text stays in the page; take each one with __JF.body('<id>').
// Companies with custom careers sites need their own extractor — ask Claude to add one in this shape.
window.__JF = (() => {
  const ORIGIN_FOR = s => ({
    greenhouse: 'https://boards-api.greenhouse.io/',
    ashby: 'https://api.ashbyhq.com/',
    lever: 'https://api.lever.co/',
    workday: `https://${s.host}/${s.site}`,
  })[s.type];

  // ---------- YOUR SETTINGS (setup fills these from tools/me/profile.md) ----------
  const CONFIG = {
    regions: ['US'],      // any of 'US', 'EU'
    maxYears: null,       // e.g. 5 -> drop postings whose REQUIRED years exceed it; null = no limit
    fitPlus: [],          // [['regex', weight], ...] terms that make a role a better fit for you
    fitMinus: [],         // [['regex', weight], ...] domains you'd rather skip
    includeTitles: '\\bproduct manager\\b',                       // regex a title must match
    excludeTitles: ['intern', 'internship', 'product marketing', 'program manager', 'project manager'],  // add seniority words you skip
  };

  // ---------- title filters (setup sets these from your profile) ----------
  const INCL = new RegExp(CONFIG.includeTitles, 'i');
  const EXCL = CONFIG.excludeTitles.length ? new RegExp(CONFIG.excludeTitles.map(w => `\\b${w}\\b`).join('|'), 'i') : /$^/;
  const titleOk = t => INCL.test(t || '') && !EXCL.test(t || '');

  const US_ST = 'AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC';
  const US_NAMES = 'Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|District of Columbia';
  const RE_US = new RegExp(`\\b(USA|United States|U\\.S\\.|US)\\b|,\\s*(${US_ST})\\b|\\b(${US_NAMES})\\b`);
  const EU = 'Austria|Belgium|Bulgaria|Croatia|Cyprus|Czechia|Czech Republic|Denmark|Estonia|Finland|France|Germany|Greece|Hungary|Ireland|Italy|Latvia|Lithuania|Luxembourg|Malta|Netherlands|Poland|Portugal|Romania|Slovakia|Slovenia|Spain|Sweden|Norway|Iceland|Switzerland|United Kingdom|UK|England|Scotland|Wales|Northern Ireland|Europe|EMEA|AUT|BEL|BGR|HRV|CYP|CZE|DNK|EST|FIN|FRA|DEU|GRC|HUN|IRL|ITA|LVA|LTU|LUX|MLT|NLD|POL|PRT|ROU|SVK|SVN|ESP|SWE|NOR|ISL|CHE|GBR|London|Paris|Dublin|Berlin|Munich|Amsterdam|Madrid|Barcelona|Zurich|Zürich|Stockholm|Copenhagen|Warsaw|Lisbon|Milan|Bucharest|Edinburgh|Cambridge, England';
  const RE_EU = new RegExp(`\\b(${EU})\\b`);
  // Places that would otherwise trip the patterns above ("New South Wales", "Cambridge, MA"…) or are simply out.
  const RE_NO = /\b(AUS|Australia|New South Wales|India|IND|Canada|CAN|Mexico|MEX|Brazil|BRA|Japan|JPN|China|CHN|Singapore|SGP|Israel|ISR|Korea|KOR|Philippines|PHL|Costa Rica|CRI|Argentina|ARG|Chile|CHL|Colombia|COL|South Africa|ZAF|UAE|ARE|United Arab Emirates|Saudi Arabia|SAU|Egypt|EGY|Vietnam|VNM|Taiwan|TWN|Hong Kong|HKG|Malaysia|MYS|Indonesia|IDN|Thailand|THA|New Zealand|NZL|Turkey|Türkiye|TUR)\b/;
  // A location string -> 'US' | 'EU' | null, kept only if listed in CONFIG.regions.
  const regionOf = s => {
    s = String(s || '');
    if (RE_NO.test(s)) return null;
    const r = RE_EU.test(s) ? 'EU' : RE_US.test(s) ? 'US' : null;
    return r && CONFIG.regions.includes(r) ? r : null;
  };
  const regions = locs => {
    const out = [];
    for (const l of locs) { const r = regionOf(l); if (r) out.push([r, l]); }
    return out;
  };

  const WORDS = {one:1,two:2,three:3,four:4,five:5,six:6,seven:7,eight:8,nine:9,ten:10,eleven:11,twelve:12,fifteen:15};
  // Only the required part of the posting counts; preferred/nice-to-have years are ignored.
  function requiredPart(t) {
    t = String(t || '');
    const s = t.search(/(minimum|basic|required)\s+qualifications|requirements|what you('|’)ll (need|bring)|you (have|bring|might be a fit)|who you are|what we('|’)re looking for|qualifications/i);
    let part = s >= 0 ? t.slice(s) : t;
    const e = part.slice(20).search(/preferred qualifications|preferred skills|nice[- ]to[- ]haves?|bonus points|pluses|it would be great if|additional qualifications|preferred:/i);
    if (e >= 0) part = part.slice(0, e + 20);
    return part;
  }
  function yearsAsked(t) {
    const part = requiredPart(t);
    let max = null;
    const re = /\b(\d{1,2}|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen)\s*(?:\+|plus)?\s*(?:(?:-|–|to)\s*\d{1,2}\s*)?\+?\s*(?:or more\s+)?(?:years?|yrs)\b/gi;
    let m;
    while ((m = re.exec(part))) {
      if (/every\s*$/i.test(part.slice(Math.max(0, m.index - 7), m.index))) continue;   // "every two years" (background checks)
      const raw = m[1].toLowerCase();
      const n = WORDS[raw] || parseInt(raw, 10);
      if (n > 0 && n < 30) max = max === null ? n : Math.max(max, n);
    }
    return max;
  }
  // 'en' or 'other' -- non-English postings are listed but not tailored.
  const lang = t => {
    t = ' ' + String(t || '').toLowerCase() + ' ';
    const en = ['the','and','you','we','with','for','of','to','in','our'].reduce((a, w) => a + (t.split(` ${w} `).length - 1), 0);
    const words = t.split(/\s+/).length;
    return words < 50 || en / words > 0.06 ? 'en' : 'other';
  };
  const FIT_PLUS = CONFIG.fitPlus;
  const FIT_MINUS = CONFIG.fitMinus;
  const fit = t => {
    t = String(t || '').toLowerCase();
    let s = 0;
    for (const [p, w] of FIT_PLUS) if (new RegExp(p).test(t)) s += w;
    for (const [p, w] of FIT_MINUS) if (new RegExp(p).test(t)) s -= w;
    return s;
  };

  const clean = s => String(s || '').replace(/\r/g, '').replace(/ /g, ' ').replace(/[ \t]+$/gm, '').replace(/\n{3,}/g, '\n\n').trim();
  // Sites with Trusted Types refuse plain innerHTML; a pass-through default policy fixes that,
  // and the regex path below covers a site that refuses the policy too.
  try { if (window.trustedTypes && !trustedTypes.defaultPolicy) trustedTypes.createPolicy('default', { createHTML: s => s }); } catch (e) {}
  const ENT = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', rsquo: '\u2019', lsquo: '\u2018', rdquo: '\u201d', ldquo: '\u201c', ndash: '\u2013', mdash: '\u2014', hellip: '\u2026', bull: '\u2022' };
  const rxText = h => clean(String(h || '')
    .replace(/<\s*br\s*\/?>/gi, '\n')
    .replace(/<\/?\s*(p|div|li|ul|ol|h[1-6]|tr|section)\b[^>]*>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&(#x?[0-9a-f]+|\w+);/gi, (m, e) => e[0] === '#' ? String.fromCodePoint(/^#x/i.test(e) ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10)) : (ENT[e.toLowerCase()] !== undefined ? ENT[e.toLowerCase()] : m))
    .replace(/[ \t]+\n/g, '\n'));
  const htmlText = h => {
    try {
      const d = document.createElement('div');
      d.style.cssText = 'position:absolute;left:-99999px;white-space:normal';
      d.innerHTML = String(h || '');
      document.body.appendChild(d);
      const t = d.innerText;
      d.remove();
      return clean(t);
    } catch (e) { return rxText(h); }
  };
  const decodeEntities = h => { try { return new DOMParser().parseFromString(String(h || ''), 'text/html').documentElement.textContent; } catch (e) { return rxText(h); } };
  const sha1 = async s => [...new Uint8Array(await crypto.subtle.digest('SHA-1', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const getJSON = (u, o) => fetch(u, o).then(r => { if (!r.ok) throw new Error(`${r.status} ${u}`); return r.json(); });
  const getText = u => fetch(u).then(r => { if (!r.ok) throw new Error(`${r.status} ${u}`); return r.text(); });
  const hydration = h => {
    const m = h.match(/window\.__staticRouterHydrationData = JSON\.parse\("(.*?)"\);<\/script>/s);
    return m ? JSON.parse(JSON.parse('"' + m[1] + '"')) : null;
  };
  const daysAgo = txt => {
    txt = String(txt || '');
    if (/today/i.test(txt)) return 0;
    if (/yesterday/i.test(txt)) return 1;
    const m = txt.match(/(\d+)\+?\s*Days?/i);
    return m ? parseInt(m[1], 10) + (/\+/.test(txt) ? 1 : 0) : null;
  };
  const isoDaysAgo = n => n === null ? null : new Date(Date.now() - n * 864e5).toISOString().slice(0, 10);

  // ---------- per company: list() → [{id,title,locs,posted?}], detail(row) → {body, locs?, posted?, url, apply, ats?} ----------
  // ---------- per platform: list(spec) → [{id,title,locs,posted?}], detail(spec,row) → {body, locs?, posted?, url, apply, ats?} ----------
  const S = {};

  S.greenhouse = {
    async list(s) {
      const j = await getJSON(`https://boards-api.greenhouse.io/v1/boards/${s.board}/jobs?content=true`);
      return j.jobs.map(x => ({ id: String(x.id), title: x.title, locs: String((x.location && x.location.name) || '').split(/ • |; /), posted: x.first_published || x.updated_at, _raw: x }));
    },
    async detail(s, r) {
      const x = r._raw;
      return { body: htmlText(decodeEntities(x.content)), url: x.absolute_url, apply: x.absolute_url, ats: `https://job-boards.greenhouse.io/embed/job_app?for=${s.board}&token=${x.id}` };
    },
  };

  S.ashby = {
    async list(s) {
      const j = await getJSON(`https://api.ashbyhq.com/posting-api/job-board/${s.org}`);
      return j.jobs.filter(x => x.isListed !== false).map(x => ({ id: x.id, title: x.title, locs: [x.location, ...(x.secondaryLocations || []).map(l => l.location), x.isRemote ? `Remote (${x.location})` : null].filter(Boolean), posted: x.publishedAt, _raw: x }));
    },
    async detail(s, r) {
      const x = r._raw;
      return { body: clean(x.descriptionPlain), url: x.jobUrl, apply: x.applyUrl || x.jobUrl };
    },
  };

  S.lever = {
    async list(s) {
      const j = await getJSON(`https://api.lever.co/v0/postings/${s.co}?mode=json`);
      return j.map(x => ({ id: x.id, title: x.text, locs: [x.categories && x.categories.location, ...((x.categories && x.categories.allLocations) || [])].filter(Boolean), posted: x.createdAt ? new Date(x.createdAt).toISOString() : null, _raw: x }));
    },
    async detail(s, r) {
      const x = r._raw;
      const lists = (x.lists || []).map(l => l.text + '\n' + htmlText(l.content)).join('\n\n');
      return { body: clean([x.descriptionPlain, lists, x.additionalPlain].filter(Boolean).join('\n\n')), url: x.hostedUrl, apply: x.applyUrl || x.hostedUrl };
    },
  };

  S.workday = {   // run in a tab on https://<host>/<site>
    async list(s, { since }) {
      const base = `/wday/cxs/${s.tenant}/${s.site}`;
      const out = [];
      for (let off = 0; off < 600; off += 20) {
        const j = await getJSON(base + '/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify({ appliedFacets: {}, limit: 20, offset: off, searchText: s.search || 'product manager' }) });
        const ps = j.jobPostings || [];
        for (const x of ps) {
          const posted = isoDaysAgo(daysAgo(x.postedOn));
          if (since && posted && posted < since) continue;
          out.push({ id: (x.externalPath.match(/_(R?\d+(?:-\d+)?)$/) || [])[1] || x.externalPath, title: x.title, locs: [x.locationsText], posted, _path: x.externalPath });
        }
        if (ps.length < 20) break;
        await sleep(300);
      }
      return out;
    },
    async detail(s, r) {
      const i = (await getJSON(`/wday/cxs/${s.tenant}/${s.site}` + r._path, { headers: { Accept: 'application/json' } })).jobPostingInfo;
      const locs = [i.location, ...(i.additionalLocations || []), i.country && i.country.descriptor].filter(Boolean);
      return { body: htmlText(i.jobDescription), locs, posted: i.startDate || r.posted, url: i.externalUrl, apply: i.externalUrl + '/apply' };
    },
  };

  const BODIES = {};
  async function run(spec, opts = {}) {
    const site = S[spec && spec.type];
    if (!site) throw new Error('no extractor for type ' + (spec && spec.type));
    const company = spec.board || spec.org || spec.co || spec.tenant;
    const seen = new Set((opts.seen || []).map(String));
    const since = opts.since || null;            // 'YYYY-MM-DD'; null = no date limit
    const rows = await site.list(spec, { since });
    const stats = { listed: rows.length, title: 0, seen: 0, region: 0, years: 0, old: 0, failed: 0 };
    const newIds = [], kept = [], rejected = [];
    for (const r of rows) {
      if (!titleOk(r.title)) { stats.title++; continue; }
      if (seen.has(r.id)) { stats.seen++; continue; }
      if (r.locs.length && !r.locs.some(l => /locations?$/i.test(l)) && !regions(r.locs).length && spec.type !== 'workday') {
        stats.region++; newIds.push(r.id); rejected.push([r.id, r.title, 'region']); continue;
      }
      let d;
      try { d = await site.detail(spec, r); } catch (e) { stats.failed++; rejected.push([r.id, r.title, 'failed: ' + e.message]); continue; }
      await sleep(250);
      newIds.push(r.id);
      const posted = d.posted || r.posted;
      if (since && posted && posted < since) { stats.old++; rejected.push([r.id, r.title, 'older than ' + since]); continue; }
      const locs = d.locs || r.locs;
      const reg = regions(locs);
      if (!reg.length) { stats.region++; rejected.push([r.id, r.title, 'region']); continue; }
      const yrs = yearsAsked(d.body);
      if (yrs !== null && CONFIG.maxYears !== null && yrs > CONFIG.maxYears) { stats.years++; rejected.push([r.id, r.title, `${yrs}+ yrs`]); continue; }
      const body = d.body;
      BODIES[r.id] = body;
      kept.push({ id: r.id, title: String(r.title).trim(), loc: reg.map(x => x[1]).filter((l, i, a) => !(l.length <= 3 && a.length > 1)).slice(0, 3).join(' · '), region: reg.some(x => x[0] === 'US') ? 'US' : 'EU', posted: posted ? String(posted).slice(0, 10) : null, years: yrs, lang: lang(body), fit: fit(body), url: d.url, apply: d.apply, ats: d.ats || '', len: body.length, sha1: await sha1(body) });
    }
    return { company, since, stats, kept, rejected, newIds };
  }

  return { ORIGIN_FOR, run, body: id => BODIES[id], titleOk, regionOf, yearsAsked, lang, fit, version: 'kit-1' };
})();
'jobfinder loaded ' + window.__JF.version;

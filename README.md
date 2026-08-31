# eftsolution.com — static port

Thirteen self-contained HTML pages — twelve site pages plus one journal post, and a post is
just another page here. Ported from the Manus React build at
`eftsolution-otnjfz6k.manus.space`, migrating off Squarespace.

**Open snags and pre-launch checklist: [`SNAGS.md`](SNAGS.md)**
**Locked decisions: [`DECISIONS.md`](DECISIONS.md)**

This mirrors `~/Claude Code/bonnieann-port` deliberately — same build script, same file
layout, same reasoning. If you know one, you know the other.

## See the site

Open **`preview/index.html`** in a browser. Double-click it in Finder — no server, no setup.
All thirteen pages, fully clickable.

`preview/` exists because `dist/` uses absolute links (`/about/`), and those break when you
open a file from Finder. The preview build rewrites them to flat filenames so navigation
works locally. It carries an ink-blue banner at the top so it can never be confused with the
real thing.

**Deploy `dist/`. Never `preview/`.**

## Build

```bash
python3 build.py && python3 check_links.py
```

Outputs to `dist/`. Also regenerates `sitemap.xml`, `robots.txt`, `_redirects` and `_headers`.
Python 3 only — no Node, no npm, nothing to install.

## Why a build script

Without it the nav and footer get copy-pasted thirteen times and drift apart. That is exactly
what happened on the Manus build: every page component carried its own markup, and the
bonnieann port found *five different navs across seven pages* in the same situation. Here the
nav lives in `_header.html` only. Change it once, rerun, redeploy.

```
_header.html     nav — the only place it exists
_footer.html     footer — same
_sprite.html     every icon, once, as SVG <symbol>s
_script.html     mobile nav, story filter, GHL loader, consent banner
_consent.html    Consent Mode v2 defaults + GTM, injected into <head>
src.css          THE STYLESHEET SOURCE — edit this
shared.css       compiled output — do not edit by hand
template.html    page shell with {{PLACEHOLDERS}}
pages/*.html     body content, one file per page
build.py         assembles everything; PAGES + POSTS hold titles + meta descriptions
check_links.py   the verifier — run it after every change
dist/            output — this is what Netlify publishes
```

## The stylesheet

The Manus design is built entirely from Tailwind utility classes. Rewriting it as hand-authored
CSS would have risked the design drifting from what was approved, so instead Tailwind is
compiled **once** into `shared.css`, which is committed. Netlify never runs Node.

`shared.css` is generated. **Edit `src.css`, never `shared.css`.** After changing `src.css`, or
after adding a utility class to a page that no other page already uses, regenerate it:

```bash
npx @tailwindcss/cli -i src.css -o shared.css --minify
```

That is the one step needing Node, and it runs on your machine, not on Netlify.

Forgetting it is the obvious trap — a new class would simply have no CSS and fail silently in
the browser. So `check_links.py` compares every class in every built page against the rules in
`shared.css` and fails on anything missing. If it reports a class with no rule, run the command
above and rebuild.

## URLs

Every page is a directory index (`dist/about/index.html`), so every canonical URL keeps its
trailing slash and matches both the `<link rel="canonical">` tags and the sitemap Bonnie is
submitting to Search Console. Do not change this without changing all three together.

`/blog/<slug>/` posts are the only pages one level down.

## The journal

The blog lives here, not in GoHighLevel. Posts are source files like every other page, so they
are versioned, reviewable and revertible.

To add a post:

1. Write `pages/blog-<slug>.html` — body content only.
2. Add a row to `POSTS` in `build.py`: source file, title, meta description, publish date, and
   a share card as `(filename, alt text)`. The date drives `datePublished` in the post's
   `BlogPosting` schema and `lastmod` in the sitemap; the card drives `og:image`.
3. Add a card to the list in `pages/blog.html`. Newest first.
4. `python3 build.py && python3 check_links.py`

## Forms and booking

There are no hand-built forms. Every capture point is one of the four GoHighLevel embeds
approved in July 2026:

| Embed | ID | Where |
|---|---|---|
| Free Consultation Calendar | `q7V5rglueV1UgmYE8Urz` | `/consultation/` |
| Free Consultation Pre-Qualification | `eC2Aq2SntKKVvK48S2c5` | `/consultation/`, above the calendar |
| EFT Guide Lead Magnet | `bcAt7LBMmWIzCLk1qeuD` | `/#guide` |
| Meditation Lead Magnet | `dcKxAonXlcNxXnxQccHB` | `/#meditation` |

The Manus build also had a hand-written contact form on `/consultation/` and a newsletter form
in the footer. Both posted to a webhook that was never configured, so both were dead. They are
gone: the contact form duplicated the pre-qualification form sitting directly beneath it, and
the footer now links to the meditation embed on the homepage rather than carrying a third
copy of a form.

`form_embed.js` loads once per page, and only on pages that actually embed something.

> ⚠ **The booking calendar is not cleared for launch.** See SNAGS S-05.

## Analytics and consent

GTM loads on all thirteen pages behind Google Consent Mode v2, defaulting to denied. The
consent banner grants on Accept and stores the choice in `localStorage` under `eft-consent`.
Nothing non-essential fires before the visitor chooses.

The container ID is still the placeholder `GTM-XXXXXXX` in `build.py`. Swap it before launch.

If you add GA4, Meta, or any other tag, configure it in GTM to respect `analytics_storage` /
`ad_storage` rather than firing on All Pages.

## Redirects

`REDIRECTS` in `build.py` generates `dist/_redirects`. Each source is emitted in both its bare
and trailing-slash form, because the Manus manifest carried only one of the two in several
places — which would have left live 404s after cutover.

That manifest was itself derived from a 76-row legacy inventory that lived on the Manus machine
and did **not** survive the export. Only 32 rules made it out. See SNAGS S-06.

## Pages

| URL | Notes |
|---|---|
| `/` | Home. Guide and meditation embeds at `#guide` and `#meditation` |
| `/about/` | Bonnie's story, credentials |
| `/services/` | Three packages, comparison table, FAQ. Stripe checkout links |
| `/packages/` | The same page again — see SNAGS S-01 |
| `/clients/` | Eight testimonials with a category filter |
| `/blog/` | Journal index |
| `/blog/why-smart-people-stay-stuck-even-when-they-know-what-to-do/` | The one post |
| `/consultation/` | Pre-qualification form then booking calendar |
| `/terms-and-privacy/` `/medical-practice-disclaimer/` `/refund-policy/` | Ported verbatim |
| `/thank-you/` | `noindex`, excluded from the sitemap |
| `/404/` | Also written to `dist/404.html`, which Netlify serves for unmatched paths |

## Verify

```bash
python3 check_links.py
```

Catches dead links, missing assets, duplicate titles, leftover build tokens, leftover Manus
references, classes with no CSS, and sitemap entries that do not resolve to a page.

Known-and-accepted snags report as warnings against their `SNAGS.md` id, so a green run means
green. Anything reported as `FAIL` is new and should not ship.

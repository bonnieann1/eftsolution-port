#!/usr/bin/env python3
"""
eftsolution.com static builder
------------------------------
Assembles the site from one shared shell plus one content fragment per page.

    python3 build.py

Why this exists: the Manus build kept every page's markup inside its own React
component, so the nav and footer existed in as many copies as there were pages and
drifted apart. Here the nav lives in _header.html only. Change it once, rerun,
redeploy. This mirrors ~/Claude Code/bonnieann-port, deliberately.

Outputs to dist/, which is what Netlify publishes. Also writes preview/ (the same
pages with links rewritten so they work when opened from Finder), sitemap.xml,
robots.txt, _redirects and _headers.

Nothing here needs Node or npm. The stylesheet is pre-compiled — see README.md.
"""

import base64
import datetime
import json
import pathlib
import re
import shutil
import sys

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"
SITE = "https://eftsolution.com"

# Swap this for the real container once it exists. check_links.py fails while the
# placeholder is still here, so the site cannot go live with a dead tag.
GTM_ID = "GTM-KRX6Z5DB"

# ---------------------------------------------------------------- page registry
# path -> (source fragment, <title>, meta description, noindex)
PAGES = {
    "/": (
        "index.html",
        "EFT solution | Release what’s holding you back",
        "EFT solution helps high-achieving people release emotional blocks and reclaim "
        "calm, clarity, and momentum through integrative energy healing and coaching.",
        False,
    ),
    "/about/": (
        "about.html",
        "About Bonnie Collins | EFT solution",
        "Meet Bonnie Collins, an EFT and energy-healing practitioner with more than 20 "
        "years of experience supporting meaningful change.",
        False,
    ),
    "/services/": (
        "services.html",
        "Services and packages | EFT solution",
        "Explore EFT solution packages for focused clarity, deeper support, and "
        "comprehensive transformation.",
        False,
    ),
    "/clients/": (
        "clients.html",
        "Client stories | EFT solution",
        "Read personal client experiences and transformation stories from EFT solution.",
        False,
    ),
    "/blog/": (
        "blog.html",
        "The Journal | EFT solution",
        "Reflections on emotional freedom, the nervous system, energy work, and "
        "practices for more room to breathe.",
        False,
    ),
    "/consultation/": (
        "consultation.html",
        "Book a consultation | EFT solution",
        "Bring your questions to a complimentary conversation with Bonnie Collins.",
        False,
    ),
    "/terms-and-privacy/": (
        "terms-and-privacy.html",
        "Terms and privacy | EFT solution",
        "Terms of use and privacy information for EFT solution.",
        False,
    ),
    "/medical-practice-disclaimer/": (
        "medical-practice-disclaimer.html",
        "Medical and practice disclaimer | EFT solution",
        "Important information about complementary practice, medical care, and "
        "individual responsibility.",
        False,
    ),
    "/refund-policy/": (
        "refund-policy.html",
        "Refund policy | EFT solution",
        "Clear information about cancellations, package purchases, and free digital "
        "resources from EFT solution.",
        False,
    ),
    "/thank-you/": (
        "thank-you.html",
        "Thank you | EFT solution",
        "Thank you for connecting with EFT solution.",
        True,
    ),
    "/404/": (
        "404.html",
        "Page not found | EFT solution",
        "The page you are looking for can’t be found.",
        True,
    ),
}

# ------------------------------------------------------------------ blog posts
# Posts are ordinary pages that live one level down at /blog/<slug>/ and carry
# BlogPosting schema and og:type=article instead of the site defaults.
#
# To add a post: write pages/blog-<slug>.html, add a row here, add a card to
# pages/blog.html. Newest first, so this file reads in the same order as the index.
#
# path -> (source fragment, <title>, meta description, ISO date, (card png, card alt))
# ---------------------------------------------------------------- the journal
# One post a week. Anything dated in the future is not built at all — no page,
# no entry in the journal index, no line in the sitemap — until a build runs
# on or after its date. netlify.toml has a daily scheduled build so that
# happens without anyone touching it. See SNAGS S-28.
#
# Backfilled June–July, then weekly from September. Change a date here and the
# post moves; that is the only place a publication date lives.
SCHEDULE = {
    "01": "2026-06-01",
    "02": "2026-06-08",
    "03": "2026-06-15",
    "04": "2026-06-22",
    "05": "2026-06-29",
    "06": "2026-07-06",
    "07": "2026-09-07",
    "08": "2026-09-14",
    "09": "2026-09-21",
    "10": "2026-09-28",
    "11": "2026-10-05",
    "12": "2026-10-12",
}


def load_generated_posts() -> dict:
    """posts-src/_registry.txt, written by convert_posts.py."""
    reg = ROOT / "posts-src" / "_registry.txt"
    if not reg.exists():
        return {}
    out = {}
    for line in reg.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        num, slug, title, desc, cover = line.split("|", 4)
        if num not in SCHEDULE:
            print(f"    WARNING: post {num} ({slug}) has no date in SCHEDULE — skipped")
            continue
        out[f"/blog/{slug}/"] = (
            f"blog-{slug}.html", title, desc, SCHEDULE[num], (cover, title),
        )
    return out


POSTS = {
    "/blog/why-smart-people-stay-stuck-even-when-they-know-what-to-do/": (
        "blog-why-smart-people-stay-stuck-even-when-they-know-what-to-do.html",
        "Why Smart People Stay Stuck, Even When They Know Exactly What to Do",
        "Understanding a pattern and being free of it are two different events. Where "
        "persistent patterns live, and what can begin to move them.",
        "2026-07-01",
        (
            "journal-why-smart-people-stuck-cover.jpg",
            "A figure beside a translucent map with an open doorway beyond it.",
        ),
    ),
}

# The site-wide card, used by every page that has no card of its own
POSTS.update(load_generated_posts())

DEFAULT_CARD = ("share-card.jpg", "EFT solution — release what’s holding you back.")

# Pages built but deliberately kept out of sitemap.xml
SITEMAP_EXCLUDE = {"/404/", "/thank-you/"}

# ---------------------------------------------------------------- 301 redirects
# Ported from the Manus build's client/public/redirects.json, which was itself
# derived from a 76-row legacy inventory that did NOT survive the export. Both the
# bare and trailing-slash form of each source is emitted — the Manus manifest only
# carried one of the two in several places, which would have left live 404s.
REDIRECTS = {
    "/home": "/",
    "/my-story": "/about/",
    "/clients": "/clients/",
    "/services": "/services/",
    "/packages": "/services/",
    "/contact": "/consultation/",
    "/articles": "/blog/",
    "/blog": "/blog/",
    "/coaching": "/services/",
    "/coaching/clarity": "/services/#clarity",
    "/coaching/abundance1": "/services/#abundance",
    "/coaching/vipsuccess": "/services/#vip",
    "/take-action": "/services/",
    "/benefits": "/services/",
    "/terms": "/terms-and-privacy/",
    "/medical-disclaimer": "/medical-practice-disclaimer/",
    "/refund-policy": "/refund-policy/",
    "/thank-you": "/thank-you/",
    "/typ": "/thank-you/",
    "/welcome": "/thank-you/",
    "/home-alt-bedford": "/",
    # --- added 31 Aug 2026 from GA4 evidence, not guesswork -----------------
    # Every path below drew real traffic on the live Squarespace site between
    # Jan 2024 and Aug 2026 and had NO redirect. See SNAGS S-06.
    "/work-with-me": "/services/",      # 27 views across both forms
    "/privacy-policy": "/terms-and-privacy/",
    "/cart": "/services/",              # Squarespace commerce, dies with it
    "/checkout": "/services/",
    "/search": "/",
}

# ------------------------------------------------------------ wildcard 301s
# Netlify placeholder and splat rules, emitted verbatim after the exact rules.
# These are deliberately NOT forced (no "!"), so a real file always wins first —
# which is what stops /blog/:year/... from swallowing the live journal post at
# /blog/why-smart-people-stay-stuck-even-when-they-know-what-to-do/.
#
# Squarespace dated the blog as /blog/YYYY/M/D/slug and exposed /blog/tag/* and
# /blog/category/* taxonomy pages. Twelve dated posts and three taxonomy pages
# drew traffic. The posts themselves were deliberately dropped from the Journal
# during the Manus build, so the honest destination is the Journal index rather
# than a 404.
WILDCARDS = [
    ("/blog/:year/:month/:day/:slug", "/blog/", 301),
    ("/blog/tag/*", "/blog/", 301),
    ("/blog/category/*", "/blog/", 301),
    ("/commerce/*", "/", 301),
    # Domain canonicalisation (S-15). eftsolution.com with no www is the real
    # address — every canonical tag and the sitemap already say so. Netlify's
    # primary-domain setting normally handles this; the rule is here as well so
    # the redirect survives a drag-and-drop deploy or a missed domain setting.
    ("https://www.eftsolution.com/*", "https://eftsolution.com/:splat", "301!"),
]


def data_uri(path: pathlib.Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    )


def out_name(path: str) -> str:
    """Every page is a directory index, so the canonical URL keeps its trailing slash.

    /            -> index.html
    /about/      -> about/index.html
    /blog/slug/  -> blog/slug/index.html
    """
    return "index.html" if path == "/" else path.strip("/") + "/index.html"


def flat_name(path: str) -> str:
    """preview/ cannot use directory indexes — a bare filename inside preview/blog/
    would resolve against the wrong folder. Flattening keeps every preview page in
    one directory and every link live when opened from Finder."""
    return "index.html" if path == "/" else path.strip("/").replace("/", "-") + ".html"


def post_schema(path: str, headline: str, desc: str, published: str, card: str) -> str:
    url = f"{SITE}{path}"
    return (
        '    <script type="application/ld+json">\n{\n'
        '  "@context": "https://schema.org",\n'
        '  "@type": "BlogPosting",\n'
        f'  "@id": "{url}#post",\n'
        f'  "headline": "{esc(headline)}",\n'
        f'  "description": "{esc(desc)}",\n'
        f'  "url": "{url}",\n'
        f'  "mainEntityOfPage": "{url}",\n'
        f'  "datePublished": "{published}",\n'
        f'  "dateModified": "{published}",\n'
        f'  "image": "{SITE}/assets/{card}",\n'
        '  "inLanguage": "en",\n'
        '  "author": {"@id": "https://eftsolution.com/#bonnie"},\n'
        '  "publisher": {"@id": "https://eftsolution.com/#organization"},\n'
        '  "isPartOf": {"@id": "https://eftsolution.com/#website"}\n'
        "}\n    </script>"
    )


def pretty_date(iso: str) -> str:
    """2026-06-01 -> 1 June 2026."""
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B')} {d.year}"


def read_minutes(src: str) -> int:
    """Rough reading time from the built fragment, at 220 words a minute."""
    frag = ROOT / "pages" / src
    if not frag.exists():
        return 0
    words = len(re.sub(r"<[^>]+>", " ", frag.read_text(encoding="utf-8")).split())
    return max(1, round(words / 220))


def render_post_list(live: dict) -> str:
    """The journal index, newest first, built from whatever is published."""
    rows = sorted(live.items(), key=lambda kv: kv[1][3], reverse=True)
    out = []
    for path, (src, title, desc, pub, _card) in rows:
        d = datetime.date.fromisoformat(pub)
        when = f"{d.strftime('%B')} {d.year}"
        out.append(
            '        <article class="group grid gap-6 border-b border-ink/15 py-9 '
            'lg:grid-cols-[0.28fr_1fr_0.8fr] lg:items-start">\n'
            '          <div class="flex items-center gap-2 text-xs uppercase tracking-[0.13em] '
            'text-sage"><svg class="i" width="14" height="14" aria-hidden="true">'
            f'<use href="#i-calendar-days"/></svg>{esc(when)}</div>\n'
            "          <div>\n"
            '            <h3 class="font-display mt-3 max-w-2xl text-3xl leading-[0.95] text-ink '
            'transition-colors group-hover:text-[#b3904c] sm:text-4xl">'
            f'<a href="{path}">{esc(title)}</a></h3>\n'
            "          </div>\n"
            "          <div>\n"
            f'            <p class="text-sm leading-7 text-ink/65">{esc(desc)}</p>\n'
            f'            <a href="{path}" class="editorial-link mt-5 inline-flex items-center '
            'gap-2 text-sm">Read the essay <svg class="i" width="15" height="15" '
            'aria-hidden="true"><use href="#i-arrow-up-right"/></svg></a>\n'
            "          </div>\n"
            "        </article>"
        )
    return "\n".join(out)


def build() -> int:
    template = (ROOT / "template.html").read_text(encoding="utf-8")
    css = (ROOT / "shared.css").read_text(encoding="utf-8")
    header = (ROOT / "_header.html").read_text(encoding="utf-8")
    footer = (ROOT / "_footer.html").read_text(encoding="utf-8")
    script = (ROOT / "_script.html").read_text(encoding="utf-8")
    sprite = (ROOT / "_sprite.html").read_text(encoding="utf-8")
    consent = (ROOT / "_consent.html").read_text(encoding="utf-8").replace("{{GTM_ID}}", GTM_ID)

    favicon_src = ROOT / "assets" / "favicon-32.png"
    favicon = data_uri(favicon_src) if favicon_src.exists() else "/assets/favicon-32.png"

    year = str(datetime.date.today().year)
    footer = footer.replace("{{YEAR}}", year)

    DIST.mkdir(exist_ok=True)
    built, missing = [], []

    entries = [(p, s, t, d, nx, None, None) for p, (s, t, d, nx) in PAGES.items()]

    # Scheduled posts. A post dated in the future does not exist as far as the
    # rest of the build is concerned — it is not written, not linked from the
    # journal, and not in the sitemap. Google is told about it on the morning
    # it appears and not a day sooner.
    today = datetime.date.today().isoformat()
    live_posts, pending = {}, []
    for path, (src, title, desc, pub, card) in POSTS.items():
        if pub > today:
            pending.append((pub, title))
        else:
            live_posts[path] = (src, title, desc, pub, card)
    entries += [(p, s, t, d, False, pub, card) for p, (s, t, d, pub, card) in live_posts.items()]

    for pub, title in sorted(pending):
        print(f"  pending  {pub}  {title[:64]}")
    if pending:
        print(f"  {len(pending)} post(s) scheduled but not yet published\n")

    # The journal index lists exactly what was built, newest first.
    postlist = render_post_list(live_posts)

    for path, src, title, desc, noindex, published, card in entries:
        card_img, card_alt = card or DEFAULT_CARD
        frag = ROOT / "pages" / src
        if not frag.exists():
            missing.append(src)
            continue

        # mark the current page in the nav so it isn't a self-link
        nav = header.replace(f'href="{path}"', f'href="{path}" aria-current="page"')

        out = (
            template.replace("{{CSS}}", css)
            .replace("{{SPRITE}}", sprite.strip())
            .replace("{{HEADER}}", nav)
            .replace("{{FOOTER}}", footer)
            .replace("{{SCRIPT}}", script)
            .replace("{{CONSENT}}", consent)
            .replace("{{GTM_ID}}", GTM_ID)
            .replace("{{CONTENT}}", frag.read_text(encoding="utf-8"))
            .replace("{{POSTLIST}}", postlist)
            .replace("{{POSTDATE}}", pretty_date(published) if published else "")
            .replace("{{TITLE}}", esc(title))
            .replace("{{DESC}}", esc(desc))
            .replace("{{PATH}}", path)
            .replace("{{FAVICON}}", favicon)
            .replace("{{ROBOTS}}", "noindex, nofollow" if noindex else "index, follow")
            .replace("{{OGTYPE}}", "article" if published else "website")
            .replace("{{OGIMAGE}}", card_img)
            .replace("{{OGIMAGEALT}}", esc(card_alt))
            .replace(
                "{{HEAD_EXTRA}}",
                post_schema(path, title, desc, published, card_img) if published else "",
            )
        )

        name = out_name(path)
        (DIST / name).parent.mkdir(parents=True, exist_ok=True)
        (DIST / name).write_text(out, encoding="utf-8")
        built.append((path, name, len(out)))

    # Netlify serves dist/404.html for unmatched paths. The page also lives at
    # /404/ so the build treats it like any other page.
    if (DIST / "404" / "index.html").exists():
        shutil.copy2(DIST / "404" / "index.html", DIST / "404.html")

    prune_stale(built)
    copy_assets()
    write_redirects()
    write_headers()
    write_sitemap()
    write_preview()

    for path, name, size in built:
        print(f"  built  {path:58} -> dist/{name:56} {size/1024:6.1f} KB")
    if missing:
        print("\n  not yet written:")
        for m in missing:
            print(f"    pages/{m}")
    print(f"\n{len(built)} of {len(PAGES) + len(POSTS)} pages built ({len(POSTS)} blog post(s)).")
    if GTM_ID == "GTM-XXXXXXX":
        print("\n  NOTE: GTM_ID is still the placeholder. check_links.py will fail on this.")
    return 0 if not missing else 1


def prune_stale(built) -> None:
    """Delete pages in dist/ that PAGES and POSTS no longer name.

    build.py writes files but never used to remove them, so a page dropped from
    the registry kept shipping — dist/packages/ survived S-01 and was still being
    deployed as a live duplicate of /services/. check_links.py caught it, which is
    the only reason it did not reach Netlify. Now the build cleans up after itself.
    """
    keep = {DIST / name for _, name, _ in built} | {DIST / "404.html"}
    removed = []
    for f in sorted(DIST.rglob("index.html")):
        if f not in keep:
            f.unlink()
            removed.append(f.relative_to(DIST).as_posix())
            # drop the directory too, if the page was the only thing in it
            try:
                f.parent.rmdir()
            except OSError:
                pass
    for name in removed:
        print(f"  pruned  dist/{name}  (no longer in PAGES or POSTS)")


def copy_assets() -> None:
    """Copy assets/ into dist/assets/.

    og:image and the JSON-LD logo are absolute paths. Only dist/ ships, so without
    this the share card 404s on every link shared to LinkedIn or WhatsApp even
    though the file exists here.
    """
    src = ROOT / "assets"
    dst = DIST / "assets"
    src.mkdir(exist_ok=True)
    dst.mkdir(parents=True, exist_ok=True)
    for f in sorted(src.iterdir()):
        if f.is_file() and not f.name.startswith("."):
            shutil.copy2(f, dst / f.name)
    names = sorted(f.name for f in dst.iterdir() if f.is_file() and not f.name.startswith("."))
    for n in sorted(n for n in names if not (src / n).exists()):
        print(f"    NOTE: dist/assets/{n} is not in assets/ — delete it by hand")
    print(f"\n  assets   {len(names)} file(s) -> dist/assets/")

    required = {
        "logo.png",
        "share-card.jpg",
        "hero-water-ripple.jpg",
        "bonnie-portrait.jpg",
        "botanical-still-life.jpg",
        "orbit-art.jpg",
        "paper-texture.jpg",
        "journal-why-smart-people-stuck-cover.jpg",
        "journal-why-smart-people-stuck-body.jpg",
        "journal-why-smart-people-stuck-reflection.jpg",
    }
    for r in sorted(required - set(names)):
        print(f"    WARNING: assets/{r} is missing — the page referencing it will 404")


def norm(path: str) -> str:
    """Netlify's redirect matcher ignores trailing slashes; this mirrors that,
    so two spellings of the same path compare equal. Root stays "/"."""
    return path.rstrip("/") or "/"


def write_redirects() -> None:
    """Netlify _redirects. Lives in dist/ because dist/ is the publish directory."""
    lines = ["# generated by build.py - do not hand-edit", ""]
    exact = 0
    for frm, to in REDIRECTS.items():
        # **Netlify ignores trailing slashes when matching redirect rules**, so
        # /services and /services/ are the same path to the matching engine. A
        # rule like "/services -> /services/" therefore also matches /services/
        # and sends it to itself: an infinite loop that, being forced (301!),
        # beats the real page. Rules that only add a slash are pointless anyway —
        # Netlify already serves a directory index at either spelling — so drop
        # the whole entry, not just the trailing-slash variant.
        if norm(frm) == norm(to.split("#")[0]):
            continue
        for src in (frm, frm + "/"):
            lines.append(f"{src:<26} {to:<36} 301!")
            exact += 1
    lines += ["", "# wildcards - not forced, so a real page always wins first"]
    for frm, to, code in WILDCARDS:
        lines.append(f"{frm:<34} {to:<36} {code}")
    lines += ["", "/*                                 /404.html                            404", ""]
    (DIST / "_redirects").write_text("\n".join(lines), encoding="utf-8")
    print(
        f"  redirects {exact} exact + {len(WILDCARDS)} wildcard "
        "rule(s) -> dist/_redirects"
    )


def write_headers() -> None:
    """Netlify _headers, mirroring the [[headers]] blocks in netlify.toml.

    Why both: netlify.toml is only read when the deploy starts from the repo root.
    A drag-and-drop of dist/ alone never sees it and the security headers would
    silently vanish — the site still works, so nothing tells you they are gone.
    This file ships inside dist/, so the headers survive every deploy method.
    """
    lines = [
        "# generated by build.py - do not hand-edit",
        "# mirrors the [[headers]] blocks in netlify.toml; keep the two in step",
        "",
        "/*",
        "  X-Content-Type-Options: nosniff",
        "  X-Frame-Options: SAMEORIGIN",
        "  Referrer-Policy: strict-origin-when-cross-origin",
        "  Permissions-Policy: geolocation=(), microphone=(), camera=()",
        "",
        "/assets/*",
        "  Cache-Control: public, max-age=31536000, immutable",
        "",
        "/*.html",
        "  Cache-Control: public, max-age=0, must-revalidate",
        "",
    ]
    (DIST / "_headers").write_text("\n".join(lines), encoding="utf-8")
    print("  headers   4 security + 2 cache rules -> dist/_headers")


def write_sitemap() -> None:
    prio = {"/": "1.0", "/services/": "0.9", "/blog/": "0.8"}
    freq = {"/": "weekly", "/blog/": "weekly", "/services/": "monthly"}
    legal_paths = {"/terms-and-privacy/", "/medical-practice-disclaimer/", "/refund-policy/"}

    rows = []
    for p in PAGES:
        if p in SITEMAP_EXCLUDE or not (ROOT / "pages" / PAGES[p][0]).exists():
            continue
        legal = p in legal_paths
        rows.append(
            "  <url>\n"
            f"    <loc>{SITE}{p}</loc>\n"
            f"    <changefreq>{freq.get(p, 'yearly' if legal else 'monthly')}</changefreq>\n"
            f"    <priority>{prio.get(p, '0.5' if legal else '0.8')}</priority>\n"
            "  </url>"
        )
    # A scheduled post must not be announced to Google before it exists. The
    # same gate as build(): dated in the future means absent from the sitemap.
    today = datetime.date.today().isoformat()
    for p, meta in POSTS.items():
        if not (ROOT / "pages" / meta[0]).exists() or meta[3] > today:
            continue
        rows.append(
            "  <url>\n"
            f"    <loc>{SITE}{p}</loc>\n"
            f"    <lastmod>{meta[3]}</lastmod>\n"
            "    <changefreq>yearly</changefreq>\n"
            "    <priority>0.7</priority>\n"
            "  </url>"
        )

    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(rows)
        + "\n</urlset>\n",
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /thank-you/\n"
        "Disallow: /404/\n"
        f"\nSitemap: {SITE}/sitemap.xml\n",
        encoding="utf-8",
    )
    print(f"  sitemap   {len(rows)} URL(s) -> dist/sitemap.xml")


def write_preview() -> None:
    """Mirror dist/ into preview/ with clickable local links.

    dist/ uses absolute paths (/about/) because that is what Netlify serves. Those
    break when a file is opened from Finder, so this rewrites them to flat local
    filenames purely for previewing.
    """
    prev = ROOT / "preview"
    prev.mkdir(exist_ok=True)

    routes = {p: PAGES[p][0] for p in PAGES}
    routes.update({p: POSTS[p][0] for p in POSTS})
    routes = {p: s for p, s in routes.items() if (ROOT / "pages" / s).exists()}
    mapping = {p: flat_name(p) for p in routes}

    count = 0
    for path in mapping:
        src = DIST / out_name(path)
        if not src.exists():
            continue
        html = src.read_text(encoding="utf-8")
        # longest paths first so /packages/ isn't clipped by a shorter prefix
        for p, target in sorted(mapping.items(), key=lambda kv: -len(kv[0])):
            html = html.replace(f'href="{p}#', f'href="{target}#')
            html = html.replace(f'href="{p}"', f'href="{target}"')
        html = html.replace('href="/assets/', 'href="../assets/')
        html = html.replace('src="/assets/', 'src="../assets/')
        html = html.replace('url("/assets/', 'url("../assets/')
        html = html.replace(
            "<body>",
            '<body>\n<div style="background:#19304d;color:#fbf8f1;font:400 13px/1.5 '
            '\'DM Sans\',sans-serif;padding:9px 16px;text-align:center;letter-spacing:.02em">'
            "LOCAL PREVIEW — links rewritten for your browser. Deploy <strong>dist/</strong>, "
            "never this folder.</div>",
            1,
        )
        (prev / mapping[path]).write_text(html, encoding="utf-8")
        count += 1
    print(f"\n  preview  {count} pages -> preview/index.html  (open this one in a browser)")


if __name__ == "__main__":
    sys.exit(build())

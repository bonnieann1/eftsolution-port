#!/usr/bin/env python3
"""
eftsolution.com build verifier
------------------------------
Run after every build. Exits non-zero on anything that would ship broken.

    python3 build.py && python3 check_links.py

Checks, in order:

  1  leftover {{TOKENS}} that build.py failed to replace
  2  internal links that point at nothing — no built page, no redirect rule, no anchor
  3  <img src> and CSS url() references with no file in dist/assets/
  4  duplicate <title> across pages (two pages competing for the same search result)
  5  utility classes used in a page but absent from the frozen stylesheet
  6  leftover Manus references — manus-storage, manus.space, VITE_ env vars
  7  the GTM placeholder, which must be swapped before launch
  8  sitemap entries that do not resolve to a built page, and vice versa

Check 5 is the guard on the frozen stylesheet. shared.css is compiled from src.css
by Tailwind and committed, so a class added to a page by hand would otherwise have
no CSS and fail silently in the browser. See README.md — "The stylesheet".
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"

# Classes Tailwind never emits a rule for — they exist only as markers for other
# selectors (group-hover:, peer-checked:) or are toggled by _script.html.
CLASS_ALLOWLIST = {"group", "peer", "i"}

# ink / sage / cream / paper / gold are plain component classes in src.css, not
# registered theme colours, so Tailwind cannot generate an opacity variant of them.
# Every `text-ink/70` in the markup therefore has no rule — on this build and on the
# Manus build it was ported from. Reported as a warning against SNAGS S-02 rather than
# an error, because fixing it changes how the whole site looks and that is Bonnie's call.
BRAND_OPACITY = re.compile(
    r"^(?:[a-z-]+:)*(?:text|bg|border|from|via|to|divide|ring|outline|fill|stroke)-(?:ink|sage|cream|paper|gold)/\d+$"
)
errors: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def main() -> int:
    if not DIST.exists():
        print("dist/ does not exist — run python3 build.py first")
        return 1

    pages = sorted(DIST.rglob("index.html"))
    if not pages:
        print("dist/ has no pages — run python3 build.py first")
        return 1

    # URL path -> page text
    docs: dict[str, str] = {}
    for p in pages:
        rel = p.relative_to(DIST).parent.as_posix()
        url = "/" if rel == "." else f"/{rel}/"
        docs[url] = p.read_text(encoding="utf-8")

    redirect_sources = set()
    redirects_file = DIST / "_redirects"
    if redirects_file.exists():
        for line in redirects_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                redirect_sources.add(line.split()[0])

    assets = {f.name for f in (DIST / "assets").iterdir()} if (DIST / "assets").exists() else set()

    # ---- 1  leftover build tokens ------------------------------------------
    for url, html in docs.items():
        for token in set(re.findall(r"\{\{[A-Z_]+\}\}", html)):
            fail(f"{url}  unreplaced build token {token}")

    # ---- 2  internal links --------------------------------------------------
    for url, html in docs.items():
        for href in set(re.findall(r'href="([^"]+)"', html)):
            if href.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
                continue
            if href.startswith("#"):
                if f'id="{href[1:]}"' not in html:
                    fail(f"{url}  anchor {href} has no matching id on this page")
                continue
            target, _, frag = href.partition("#")
            if target.startswith("/assets/"):
                if target.rsplit("/", 1)[-1] not in assets:
                    fail(f"{url}  links to missing asset {target}")
                continue
            if target in ("", "/"):
                target = "/"
            if target not in docs and target not in redirect_sources:
                fail(f"{url}  links to {target}, which is neither a page nor a redirect")
                continue
            if frag and target in docs and f'id="{frag}"' not in docs[target]:
                fail(f"{url}  links to {target}#{frag}, but {target} has no id=\"{frag}\"")

    # ---- 3  images and CSS assets ------------------------------------------
    for url, html in docs.items():
        refs = set(re.findall(r'src="(/assets/[^"]+)"', html))
        refs |= {m for m in re.findall(r'url\("(/assets/[^"]+)"\)', html)}
        for ref in refs:
            if ref.rsplit("/", 1)[-1] not in assets:
                fail(f"{url}  references missing asset {ref}")

    # ---- 4  duplicate titles ------------------------------------------------
    titles: dict[str, list[str]] = {}
    for url, html in docs.items():
        m = re.search(r"<title>(.*?)</title>", html, re.S)
        if m:
            titles.setdefault(m.group(1).strip(), []).append(url)
    for title, urls in titles.items():
        if len(urls) > 1:
            fail(f"duplicate <title> {title!r} on {', '.join(sorted(urls))}")

    # ---- 5  classes missing from the frozen stylesheet ----------------------
    css_path = ROOT / "shared.css"
    if not css_path.exists():
        fail("shared.css is missing — see README.md, 'The stylesheet'")
    else:
        css = css_path.read_text(encoding="utf-8")
        # Tailwind escapes special characters in selectors: .focus\:absolute:focus,
        # .text-\[0\.7rem\], .bg-ink\/15. Match the escapes as part of the class
        # name, then unescape — otherwise the name is clipped at the first colon.
        raw = set(re.findall(r"\.((?:\\.|[A-Za-z0-9_-])+)", css))
        defined = {re.sub(r"\\(.)", r"\1", c) for c in raw}

        used: dict[str, str] = {}
        for url, html in docs.items():
            body = html.split("</style>", 1)[-1]
            for attr in re.findall(r'class="([^"]+)"', body):
                for cls in attr.split():
                    used.setdefault(cls, url)

        dead_brand = []
        for cls in sorted(c for c in used if c not in defined and c not in CLASS_ALLOWLIST):
            if BRAND_OPACITY.match(cls):
                dead_brand.append(cls)
            else:
                fail(
                    f"class {cls!r} (first seen on {used[cls]}) has no rule in shared.css — "
                    "regenerate it: npx @tailwindcss/cli -i src.css -o shared.css --minify"
                )
        if dead_brand:
            warn(
                f"SNAGS S-02 — {len(dead_brand)} brand-colour opacity classes generate no CSS "
                f"({', '.join(dead_brand[:4])}{', …' if len(dead_brand) > 4 else ''}). "
                "Inherited from the Manus build; see SNAGS.md before changing."
            )

    # ---- 6  leftover Manus references --------------------------------------
    for url, html in docs.items():
        for needle in ("manus-storage", "manus.space", "manusvm", "VITE_", "__manus__"):
            if needle in html:
                fail(f"{url}  still references {needle}")

    # ---- 7  analytics placeholder ------------------------------------------
    for url, html in docs.items():
        if "GTM-XXXXXXX" in html:
            warn("SNAGS S-03 — GTM container is still the placeholder GTM-XXXXXXX. "
                 "Swap GTM_ID in build.py before launch; analytics record nothing until then.")
            break

    # ---- 8  sitemap agrees with what was built -----------------------------
    sitemap = DIST / "sitemap.xml"
    if sitemap.exists():
        locs = re.findall(r"<loc>https://eftsolution\.com([^<]*)</loc>", sitemap.read_text())
        for loc in locs:
            if loc not in docs:
                fail(f"sitemap lists {loc}, which was not built")
        listed = set(locs)
        for url in docs:
            if url not in listed and url not in {"/404/", "/thank-you/"}:
                warn(f"{url} was built but is not in sitemap.xml")
    else:
        fail("dist/sitemap.xml is missing")

    # ---- 9  redirect rules that would trap a visitor -----------------------
    # Netlify IGNORES TRAILING SLASHES when matching redirect rules, so /services
    # and /services/ are one path to the matcher. That makes "/services
    # -> /services/" a self-redirect: it matches its own destination and loops
    # forever, and being forced (301!) it beats the real page. Compare both sides
    # with the slash normalised, or the check misses exactly the bug it is for.
    def norm(path: str) -> str:
        return path.rstrip("/") or "/"

    redirects = DIST / "_redirects"
    if redirects.exists():
        built = {norm(u) for u in docs}
        for raw in redirects.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            src, dest = parts[0], parts[1]
            forced = len(parts) > 2 and parts[2].endswith("!")
            if "*" in src or ":" in src.split("://")[-1]:
                continue  # wildcard and placeholder rules, which are not forced
            target = norm(dest.split("#")[0])
            if norm(src) == target:
                fail(f"_redirects: {src} redirects to itself once Netlify normalises "
                     f"the trailing slash — infinite loop, the page never loads")
            elif forced and norm(src) in built:
                fail(f"_redirects: forced rule on {src} shadows the real page built "
                     f"at that path — visitors get {dest} instead")
    else:
        fail("dist/_redirects is missing")

    # ---- 10  the GoHighLevel embeds must be visible ------------------------
    # S-27: every GHL embed on the site sat invisible for five days. Their
    # form_embed.js sets visibility:hidden on each iframe and only clears it
    # after a postMessage handshake; when that never landed, both lead magnets
    # and the booking calendar rendered as empty boxes. Nothing in the build
    # caught it, because the markup was correct. These two rules encode what
    # went wrong so it cannot come back quietly.
    for url, html in docs.items():
        if "appendChild" in html and "form_embed.js" in html.split("<!--")[0]:
            fail(f"{url} appends GoHighLevel's form_embed.js — it hides every "
                 f"embed until a handshake that has failed before (SNAGS S-27)")
        for tag in re.findall(r"<iframe[^>]*data-ghl-embed[^>]*>", html):
            if 'loading="lazy"' in tag:
                name = re.search(r'data-form-name="([^"]*)"', tag)
                fail(f"{url} lazy-loads the GHL embed "
                     f"{name.group(1) if name else '(unnamed)'} — a booking or "
                     f"lead form must not depend on a viewport heuristic")

    # ---- report -------------------------------------------------------------
    for w in warnings:
        print(f"  warn   {w}")
    for e in errors:
        print(f"  FAIL   {e}")

    print(
        f"\n{len(docs)} pages checked · {len(assets)} assets · "
        f"{len(errors)} error(s) · {len(warnings)} warning(s)"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

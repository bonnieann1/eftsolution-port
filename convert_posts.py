#!/usr/bin/env python3
"""posts-src/*.md  ->  pages/blog-<slug>.html

Bonnie writes the journal in Google Docs and they arrive as markdown. Writing
each one out as hand-made HTML would guarantee they drifted apart, which is
the same failure that produced five different navs in the Manus build. So the
markdown is the source of truth and this makes the fragment.

Heading rule, which is the whole point of doing it here rather than by hand:
  #     the post title    -> the page's single <h1>, in the header block
  ##    a section         -> <h2>
  ###   a sub-section     -> <h3>
Nothing is skipped, nothing is invented, and no post ever gets a second <h1>.

Also stripped, because they belong to the document and not to the page: the
"*Published: …*" byline (the real date lives in POSTS) and the trailing
"*Keywords: …*" line (that is Bonnie's note to herself, not reader content).

Run:  python3 convert_posts.py
"""
import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "posts-src"
OUT = ROOT / "pages"

# The eyebrow above each title. Set here rather than guessed from the text.
CATEGORIES = {
    "01": "The nervous system",
    "02": "The nervous system",
    "03": "Mindset & emotional freedom",
    "04": "The nervous system",
    "05": "Work & money",
    "06": "Working together",
    "07": "Energy & evidence",
    "08": "Body & symptoms",
    "09": "Working together",
    "10": "Energy & evidence",
    "11": "Relationships",
    "12": "Working together",
}

# Every outbound link in the source points at a bare domain. On the site they
# should go to the page that actually takes a booking.
LINK_REWRITES = {
    "https://eftsolution.com": "/consultation/",
    "https://eftsolution.com/": "/consultation/",
    "https://bonnieann.com": "/consultation/",
    "https://bonnieann.com/": "/consultation/",
}

CARE_NOTE = (
    '<div class="border-t border-ink/15 pt-8 text-base leading-8">'
    '<strong class="text-ink">A note on care.</strong> This article is for general '
    "information and reflection. It is not medical or mental-health advice, and it "
    "does not diagnose, treat, cure, or prevent any condition. Please consult an "
    "appropriately licensed professional for individual care.</div>"
)


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def inline(text: str) -> str:
    """Markdown inline -> HTML. Escapes first so source angle brackets are safe."""
    out = esc(text)
    # links before emphasis, so [*text*](url) keeps its italics inside the anchor
    def link(m: re.Match) -> str:
        label, href = m.group(1), m.group(2)
        href = LINK_REWRITES.get(href.rstrip("/"), LINK_REWRITES.get(href, href))
        ext = "" if href.startswith("/") else ' target="_blank" rel="noreferrer"'
        return f'<a href="{html.escape(href, quote=True)}"{ext}>{inline_emphasis(label)}</a>'

    out = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, out)
    return inline_emphasis(out)


def inline_emphasis(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text, flags=re.S)
    text = re.sub(r"(?<!\*)\*(?!\s)([^*]+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", text)
    return text


def blocks(md: str):
    """Yield ('h2'|'h3'|'p', text) for the body, skipping document furniture."""
    for raw in md.split("\n"):
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            continue  # the title, handled separately
        if line.startswith("### "):
            yield "h3", line[4:].strip()
        elif line.startswith("## "):
            yield "h2", line[3:].strip()
        elif line.startswith("#"):
            # A deeper level than the site styles. Loud on purpose.
            print(f"    WARNING: heading deeper than h3 dropped to h3: {line[:60]}")
            yield "h3", line.lstrip("#").strip()
        else:
            yield "p", line


def is_byline(text: str) -> bool:
    t = text.strip("*_ ").lower()
    return t.startswith("published") and len(t) < 90


def is_keywords(text: str) -> bool:
    return text.strip("*_ ").lower().startswith("keywords:")


def is_bio(text: str) -> bool:
    return text.strip("*_ ").startswith("Bonnie Collins is")


def summarise(paragraph: str, limit: int = 155) -> str:
    """A meta description from the opening paragraph, cut on a word boundary."""
    plain = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", paragraph)
    plain = re.sub(r"[*_`]", "", plain).strip()
    if len(plain) <= limit:
        return plain
    cut = plain[:limit].rsplit(" ", 1)[0].rstrip(" ,;:—-")
    return cut + "…"


def convert(path: pathlib.Path) -> dict:
    md = path.read_text(encoding="utf-8")
    num = path.name[:2]
    slug = path.stem[3:]

    title_match = re.search(r"^#\s+(.+)$", md, flags=re.M)
    if not title_match:
        raise SystemExit(f"{path.name}: no '# ' title line")
    title = title_match.group(1).strip()

    body, bio, cta = [], None, None
    first_para = None
    h2s = h3s = 0

    for kind, text in blocks(md):
        if kind == "p":
            if is_byline(text) or is_keywords(text):
                continue
            if is_bio(text):
                bio = text
                continue
            if bio is not None and "](" in text:
                cta = text          # the closing call to action, after the bio
                continue
            if bio is not None:
                continue            # anything after the bio is document furniture
            if first_para is None:
                first_para = text
            body.append(f"<p>{inline(text)}</p>")
        elif kind == "h2":
            h2s += 1
            body.append(f"<h2>{inline(text)}</h2>")
        else:
            h3s += 1
            body.append(f"<h3>{inline(text)}</h3>")

    if not body:
        raise SystemExit(f"{path.name}: no body content found")

    tail = []
    if cta:
        tail.append(f'<p class="mt-10">{inline(cta)}</p>')
    if bio:
        tail.append(
            '<div class="border-t border-ink/15 pt-8 text-base leading-8 text-ink/70">'
            f"{inline(bio)}</div>"
        )
    tail.append(CARE_NOTE)

    cover = f"journal-{slug}-cover.jpg"
    fragment = f"""<main id="content">
  <article class="bg-paper">
    <div class="container max-w-5xl py-16 lg:py-24">
      <a href="/blog/" class="editorial-link text-sm">← Back to the journal</a>
      <p class="eyebrow mt-16">{esc(CATEGORIES.get(num, "The journal"))}</p>
      <h1 class="font-display mt-7 max-w-4xl text-5xl font-semibold leading-[0.9] tracking-[-0.04em] text-ink sm:text-7xl">{esc(title)}</h1>
      <div class="mt-8 flex items-center gap-2 text-sm text-sage"><svg class="i" width="15" height="15" aria-hidden="true"><use href="#i-calendar-days"/></svg>{{{{POSTDATE}}}}</div>

      <figure class="mt-12">
        <img src="/assets/{cover}" alt="" width="1400" height="933" class="aspect-[3/2] w-full object-cover" />
      </figure>

      <div class="mt-12 grid gap-12 lg:grid-cols-[1fr_0.34fr]">
        <div class="post-body max-w-2xl text-lg leading-9 text-ink/75">
{chr(10).join("          " + b for b in body + tail)}
        </div>
        <aside class="h-fit border-l border-[#c7a96b] pl-6">
          <p class="text-[0.65rem] font-bold uppercase tracking-[0.15em] text-[#b3904c]">A gentle next step</p>
          <p class="mt-4 font-display text-3xl leading-none text-ink">Bring your questions to a complimentary conversation.</p>
          <a href="/consultation/" class="editorial-link mt-6 inline-flex items-center gap-2 text-sm">Book a consultation <svg class="i" width="15" height="15" aria-hidden="true"><use href="#i-arrow-up-right"/></svg></a>
        </aside>
      </div>
    </div>
  </article>
</main>
"""
    out = OUT / f"blog-{slug}.html"
    out.write_text(fragment, encoding="utf-8")
    return {
        "num": num, "slug": slug, "title": title, "cover": cover,
        "desc": summarise(first_para or title), "h2": h2s, "h3": h3s,
        "words": len(re.sub(r"<[^>]+>", " ", " ".join(body)).split()),
        "file": out.name, "cta": bool(cta), "bio": bool(bio),
    }


def main() -> int:
    if not SRC.exists():
        print("posts-src/ not found"); return 1
    rows = [convert(p) for p in sorted(SRC.glob("[0-9][0-9]-*.md"))]
    print(f"{'file':52} {'h1':>2} {'h2':>3} {'h3':>3} {'words':>6}  bio cta")
    for r in rows:
        print(f"  {r['file']:50} {1:>2} {r['h2']:>3} {r['h3']:>3} {r['words']:>6}"
              f"   {'y' if r['bio'] else 'N'}   {'y' if r['cta'] else 'N'}")
    print(f"\n{len(rows)} fragment(s) written to pages/")
    reg = ROOT / "posts-src" / "_registry.txt"
    reg.write_text("\n".join(f"{r['num']}|{r['slug']}|{r['title']}|{r['desc']}|{r['cover']}"
                             for r in rows) + "\n", encoding="utf-8")
    print(f"registry -> {reg.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

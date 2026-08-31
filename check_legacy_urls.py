#!/usr/bin/env python3
"""
eftsolution.com legacy URL coverage check
-----------------------------------------
Every URL below drew real traffic on the live Squarespace site. This asserts that
each one still resolves after cutover — as a page, an exact 301, or a wildcard —
rather than 404ing and dropping whatever ranking it holds.

    python3 build.py && python3 check_legacy_urls.py

Source: GA4 property 421209755 (eftsolution.com), Pages and screens,
1 Jan 2024 - 30 Aug 2026. 42 paths, 805 views. Pulled 31 August 2026.

This replaces the guesswork in SNAGS S-06. The Manus build's redirect work was
based on a 76-row inventory that never left the Manus machine; this is the real
list, taken from what visitors actually requested.

Re-pull after launch: Search Console -> Pages will show anything still 404ing
that had no traffic in this window, and new rows can be added to LEGACY below.
"""

import fnmatch
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"

# path, views
LEGACY = [
    ("/", 254), ("/clients", 76), ("/coaching", 74), ("/take-action", 49),
    ("/my-story", 43), ("/blog", 34), ("/benefits", 31), ("/coaching/clarity", 30),
    ("/terms", 26), ("/contact", 22), ("/articles", 20), ("/medical-disclaimer", 19),
    ("/coaching/vipsuccess", 17), ("/work-with-me", 15), ("/take-action/", 13),
    ("/work-with-me/", 12), ("/coaching/abundance1", 10),
    ("/blog/2023/8/11/embrace-love-and-compassion-balancing-the-heart-chakra-anahata", 6),
    ("/cart", 6),
    ("/blog/2023/8/12/unleash-your-creativity-balancing-the-throat-chakra-vishuddha", 4),
    ("/blog/2023/8/14/the-crown-chakra-sahasrara-unleashing-the-divine-within", 4),
    ("/checkout", 4), ("/privacy-policy", 4),
    ("/blog/2017/8/27/decision-making-where-mindset-meets-emotions-9-steps-to-making-great-decisions-for-your-best-life", 3),
    ("/blog/2023/8/10/unleash-the-power-of-the-solar-plexus-chakra-ignite-your-inner-fire-for-optimal-energy-and-health", 3),
    ("/blog/2023/8/13/awakening-insight-unblocking-and-activating-the-brow-chakra-ajna", 3),
    ("/blog/tag/emotional+freedom+technique", 3), ("/welcome", 3),
    ("/blog/2023/8/9/embrace-the-power-of-the-sacral-chakra-unleash-your-sexual-energy-emotional-balance-and-mental-clarity", 2),
    ("/blog/2023/8/9/understanding-the-root-chakra-your-foundation-to-strength-confidence-and-energy", 2),
    ("/blog/tag/behaviours", 2), ("/blog/2017/4/17/on-loyalty", 1),
    ("/blog/2017/4/5/hustle-and-rest", 1), ("/blog/2017/4/5/what-if", 1),
    ("/blog/2017/8/25/achieve-achieving-achieved-9dtgw", 1),
    ("/blog/category/Goals", 1), ("/coaching/", 1),
    ("/commerce/orders/7e0bc4f0-b012-4629-932f-a5374f71aaaf", 1),
    ("/home", 1), ("/packages", 1), ("/search", 1), ("/typ", 1),
]


def main() -> int:
    if not DIST.exists():
        print("dist/ does not exist — run python3 build.py first")
        return 1

    pages = {
        "/" if p.relative_to(DIST).parent.as_posix() == "."
        else f"/{p.relative_to(DIST).parent.as_posix()}/"
        for p in DIST.rglob("index.html")
    }

    exact, wild = {}, []
    for line in (DIST / "_redirects").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        src, dst = line.split()[0], line.split()[1]
        (wild.append((src, dst)) if "*" in src or ":" in src else exact.update({src: dst}))

    def resolve(path):
        if path in pages:
            return "page", path
        if path in exact:
            return "301", exact[path]
        for src, dst in wild:
            if ":" in src:
                depth = len(src.strip("/").split("/"))
                if len(path.strip("/").split("/")) == depth and path.startswith(src.split(":")[0]):
                    return "301 placeholder", dst
            elif fnmatch.fnmatch(path, src):
                return "301 splat", dst
        return None, None

    covered = lost = 0
    misses = []
    for path, views in sorted(LEGACY, key=lambda x: -x[1]):
        how, dest = resolve(path)
        if how is None:
            lost += views
            misses.append((path, views))
        else:
            covered += views

    for path, views in misses:
        print(f"  FAIL   {views:>4} views  {path}  has no page and no redirect")

    total = covered + lost
    pct = covered / total * 100 if total else 100
    print(
        f"\n{len(LEGACY)} legacy URLs · {total} views · "
        f"{covered} covered ({pct:.1f}%) · {lost} would 404"
    )
    return 1 if misses else 0


if __name__ == "__main__":
    sys.exit(main())

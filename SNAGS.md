# SNAGS — eftsolution.com port

Everything spotted during the port, logged and **not acted on** — that was the agreed scope
(`DECISIONS.md`, decision 2). Three exceptions are marked **FIXED** and explained, each one a
defect rather than a design choice.

Ordered by what would hurt most if it shipped as-is.

Status as of 31 August 2026, revised after verifying the GHL calendar directly. `check_links.py` reports S-02 by id on every run (S-01 and S-03 are closed).

---

## Launch gates — do not go live with these open

### S-05 · Booking calendar video conferencing — **CLOSED 1 Sep 2026**

Bonnie connected Zoom to GoHighLevel on 1 September 2026 and confirmed it. Worth one live
test booking before the DNS flip: book the free consultation through the site and check the
confirmation email actually carries a Zoom link.

The original finding, for the record:


**Verified in GoHighLevel on 31 August 2026.** Settings → Calendars → Connections →
Video conferencing, for staff member Bonnie Collins, reads:

> **No connections found.** Connect your video conferencing tools to generate unique meeting links.

Zoom is **not connected to GoHighLevel**. That is stronger than the July warning suggested. It is
not that the Zoom link is a placeholder — it is that GHL has no way to create a Zoom link for this
calendar at all. Anyone booking the free consultation gets a confirmation with no working meeting
link, or with whatever static text was typed into the location field in July.

The calendar itself (`q7V5rglueV1UgmYE8Urz`, "Free Consultation") is **Active**, last updated
11 August 2026, and is embedded live on `/consultation/`.

**Do not launch until this is connected and a test booking produces a real link.**

### S-18 · Double bookings — **CLOSED 1 Sep 2026**

Bonnie connected her own calendar to GoHighLevel on 1 September 2026 and confirmed it, so
existing commitments now block slots. Same live test as S-05 covers this.

The original finding, for the record:


Same screen, Connections → Calendars, also reads **"No connections found."** Bonnie's own calendar
(Google or Outlook) is not linked to GoHighLevel, so GHL has no idea when she is busy.

A prospect can book a free consultation directly on top of a paying client's session. This is
arguably worse than S-05, because a broken link is embarrassing while a double booking costs a
client their appointment.

### S-19 · Consultation length — **CLOSED 31 Aug 2026**

The site said *"15-minute conversation"*; the GHL calendar was set to **1 hr**. Bonnie chose to
keep the hour and change the site.

Two places, both now read 60 minutes:

- homepage hero strip — *"60-minute conversation · no package decision required"*
- the journal post's closing offer — *"I offer a free 60-minute conversation."*

The three `90-minute` references on `/services/` are the paid package sessions and were left
alone. No GHL change was needed; the calendar was already 1 hr.

**Worth revisiting once bookings start.** An hour given away per enquiry is real capacity: at
even three enquiries a week that is most of a working day before anyone has paid. If the free
call starts crowding out paid sessions, shortening it is one setting in GHL and two lines here.

### S-03 · Analytics — **CLOSED 1 Sep 2026**

**Checked in Google Analytics and Tag Manager, 31 August 2026.**

Good news first: a GA4 property for eftsolution.com already exists and is **already collecting
from the live Squarespace site**.

| | |
|---|---|
| GA4 property | `421209755` (eftsolution.com), under the "Google Ads Account" analytics account `297228733` |
| Web data stream | `6499434174` |
| **Measurement ID** | **`G-EL6KJYJWTB`** |
| Status | Data collection active in the past 48 hours |

Because the new site can use that same measurement ID, traffic history carries straight across
the migration — which is exactly what makes it possible to tell whether the cutover cost
anything.

The gap is Tag Manager. The only container in the account is:

| Account | Container | ID |
|---|---|---|
| Bonnie Ann | bonnieann.com | `GTM-5F5J75CP` |

**Container created and wired in, 1 September 2026.** Bonnie created a dedicated
eftsolution.com container and supplied the snippets:

| Account | Container | ID |
|---|---|---|
| Bonnie Ann | eftsolution.com | **`GTM-KRX6Z5DB`** |

What changed in the build:

- `build.py` — `GTM_ID` is now the real container, replacing the `GTM-XXXXXXX` placeholder.
- `template.html` — the consent + loader block moved up to sit directly after the `charset`,
  `viewport` and `theme-color` metas, so it is as high in `<head>` as it can go while keeping the
  three required metas first.
- `template.html` — the Tag Manager **`<noscript>` iframe** now sits immediately after the opening
  `<body>` tag. This half was missing before; it is what records visitors running with JavaScript
  disabled.

Both live in the shared shell, so all 12 pages carry exactly one loader and one noscript block —
verified after the build.

**Consent Mode v2 still runs first.** The `gtag('consent', 'default', …)` block sits ahead of the
loader with everything denied, so no tag fires until a visitor accepts. Bonnie's head snippet was
pasted into the build as-is apart from that ordering; pasting it a second time verbatim would have
loaded Tag Manager twice and stripped the consent defaults.

**Still to do inside the container:** add a GA4 Configuration tag pointing at the existing
measurement ID `G-EL6KJYJWTB`, then publish the container. Until that tag exists and is published,
Tag Manager loads but sends nothing to Analytics.

Do **not** point the new site at the bonnieann container or the bonnieann GA4 property — the two
brands serve different audiences and mixing them makes both sets of numbers useless.

### S-07 · Ten images are placeholders — **CLOSED 31 Aug 2026**

Bonnie supplied the Manus asset bundle. All ten are installed, resized and re-encoded. Total
image weight across the whole site is 1.9 MB.

Two things changed during processing, both recorded in the commit:

- The portrait moved from `.png` to `.jpg`. A 900×1125 photograph as PNG was about 1.5 MB.
- The supplied logo arrived as a gold mark on an **opaque white canvas**, which showed as a white
  square on the cream header and the ink footer. Near-white was keyed to transparent and the mark
  trimmed square.

---

## Inherited from the Manus build — real, and yours to decide on

### S-01 · Duplicate page — **CLOSED 31 Aug 2026**

`/services/` is now the only real page. `/packages/` is gone and 301s to it, as do every legacy
link that used to point there — `/coaching`, `/coaching/clarity`, `/coaching/abundance1`,
`/coaching/vipsuccess`, `/take-action`, `/benefits` — with the `#clarity` / `#abundance` /
`#vip` anchors preserved, so an old link still lands on the right package.

"Services" was chosen because it already matches the main menu.

**The sitemap is now 10 URLs, not 11.** The `sitemap.xml` file supplied by hand still lists
`/packages/` and is superseded — submit the generated `dist/sitemap.xml`, which build.py keeps
in step with whatever is actually built.

### S-22 · Five pages were unreachable — redirect loop — **FIXED 1 Sep 2026**

**Found by Bonnie on the Netlify URL, 1 September 2026.** `/clients/` would not load. The
browser was not showing a 404 — it was showing a connection error, because the page was
redirecting to itself forever.

`write_redirects()` emitted each rule twice, once bare and once with a trailing slash, so that
old links worked either way. For entries that only *add* the slash, the second copy pointed at
its own source:

    /clients                   /clients/                            301!
    /clients/                  /clients/                            301!   <- loop

Because these rules are **forced** (`301!`), the loop beat the real file that Netlify had
published at that path. Five pages were affected — `/clients/`, `/services/`, `/blog/`,
`/refund-policy/` and `/thank-you/` — which is nearly half the site, including the services page
every package link points at.

Two fixes:

1. `write_redirects()` now skips any variant whose source equals its destination. Exact rules
   dropped from 52 to 47; the five removed were all loops.
2. `check_links.py` gained check 9, which reads the generated `_redirects` and hard-fails on a
   rule that points at its own source, or on a forced rule whose source is a page that was
   actually built (which would hide the real page). Verified by reintroducing both faults —
   both are caught.

**Why nothing caught it earlier.** `check_links.py` read the built HTML in `dist/` and
`check_legacy_urls.py` checked that every legacy path had *a* rule. Neither read the redirect
file to ask whether the rules were sane, so a build could be green while half the site was
unreachable. That gap is what check 9 closes.

### S-21 · build.py never removed deleted pages — **FIXED 31 Aug 2026**

Found while closing S-01. `build.py` wrote pages but never deleted them, so `dist/packages/`
survived being dropped from the registry and would have deployed to Netlify as a live duplicate
of `/services/`. `check_links.py` caught it — which is the only reason it did not ship.

`prune_stale()` now deletes any page in `dist/` that `PAGES` and `POSTS` no longer name, and
reports what it removed. The duplicate-title exemption for `/services/` + `/packages/` has also
been taken out of `check_links.py`, so any future duplicate title is a hard failure again.

### S-02 · Fifteen brand-colour classes produce no CSS at all

`ink`, `sage`, `cream`, `paper` and `gold` are written as plain component classes rather than
registered Tailwind theme colours. Tailwind can generate `.text-ink`, but it cannot generate an
opacity variant of a class it doesn't know is a colour — so every `text-ink/70`, `border-ink/15`,
`bg-cream/70` and the rest has **no rule whatsoever**, on this build and on the Manus site it
came from.

The design survives by accident: body text falls back to the base foreground colour (very close
to full-strength ink) and dividers fall back to Tailwind's default border colour. So it looks
deliberate, and it isn't.

Affected: `bg-cream/55`, `bg-cream/70`, `bg-ink/15`, `bg-sage/25`, `bg-sage/50`, `border-ink/10`,
`border-ink/15`, `border-ink/20`, `text-ink/45`, `text-ink/50`, `text-ink/55`, `text-ink/60`,
`text-ink/65`, `text-ink/70`, `text-ink/75`.

**Recommended fix:** register the five brand colours in the `@theme` block of `src.css`. One
change, and every one of them starts working as written.

**Why it isn't done:** it makes the site visibly different from what you approved — body copy
across every page would lighten to the 70% grey the original author evidently intended, and the
hairline dividers would take on the ink tint. That is a look-at-it-and-decide change, not a
silent one. Worth seeing on the preview before deciding either way.

### S-04 · Invisible hover state on the gold buttons — **FIXED**

The gold-outline CTAs (Abundance package, the Clients page "Book a conversation", the header
consult button) carried `hover:bg-[#c7a96b] hover:text-ink`. Because of S-02, `hover:text-ink`
generated nothing — so on hover the background turned gold and the label **stayed gold**,
disappearing completely.

Broken on the Manus site too. Fixed here by writing the same colour in a form Tailwind actually
generates (`hover:text-[#19304d]`). Identical intended CSS; the difference is that it now exists.
Same fix applied to `border-ink` and `focus:bg-ink` on the skip-to-content link.

To revert: swap those three back and rerun the build. `check_links.py` will then report them.

### S-17 · The share card is interim

`assets/share-card.jpg` — the 1200×630 picture LinkedIn and WhatsApp show when a link to the site
is posted — was built from the hero image during the port. The type on it is set in Caladea and
Carlito, not Cormorant Garamond and DM Sans, because the real brand fonts are not installed
locally and could not be fetched.

It is presentable and correct in colour, and it beats having no card. But since posts are
cross-posted daily, this image does a lot of work, and it is worth remaking properly — the
bonnieann build renders its cards from HTML through headless Chrome, which picks the real fonts
up from Google Fonts. The same approach would work here.

### S-08 · Badge contrast — **CLOSED 31 Aug 2026**

The "years of practice" caption under the homepage 20+ badge was `text-sage` (#556b5a) on
`bg-sage` (#dce4d8). Measured properly it was **4.44:1** — under the 4.5:1 AA threshold, though
by less than this file originally claimed (it said 3.7:1; that estimate was wrong).

Now `text-[#19304d]/75`, which measures **5.22:1**. The "20+" itself was always fine.

### S-09 · Draft warnings on legal pages — **CLOSED 31 Aug 2026**

Three sentences written as notes to Bonnie were sitting in customer-facing copy:

- *"This page is informational. Please use the final approved policy language for production."*
  — on both `/terms-and-privacy/` and `/medical-practice-disclaimer/`
- *"The production version of this page should include the final approved privacy and cookie
  policy…"* — on `/terms-and-privacy/`
- *"Please have this policy reviewed for the laws that apply to your business before publishing
  it as final."* — on `/refund-policy/`

All replaced with real customer-facing sentences. The privacy paragraph now actually says what
is collected and that non-essential cookies wait for consent, which is both truer and more
useful than a note about the page being unfinished.

**The underlying point still stands and has just moved off the website and into this file:**
these policies have not been reviewed by a solicitor. Removing the warning did not make them
reviewed. See S-14 — worth one legal pass covering the policies and the testimonials together.

### S-10 · Two footer links, one destination — **CLOSED 31 Aug 2026**

The footer pointed both "Privacy policy" and "Terms of service" at bare `/terms-and-privacy/`.
The page's two sections now carry `id="terms"` and `id="privacy"`, and each footer link goes to
its own anchor. No new page, no duplicate content, and each link now lands where its label
promises.

If a fully separate privacy policy is ever wanted for GDPR tidiness, that is a new page — not
required, and not done.

### S-11 · Rescheduling contradiction — **CLOSED 31 Aug 2026**

The Services FAQ said 48 hours; the Refund Policy said 24. Bonnie's actual policy is **24 hours**,
so the FAQ was changed to match — the Refund Policy is the document a client is more likely to
quote back, and 24 hours is the more forgiving of the two.

The FAQ answer now also points at the Refund Policy for the full terms, so the two pages agree
and one is clearly the authority. The phrase "48 hours" no longer appears anywhere on the site.

### S-12 · Journal date — **DECIDED 31 Aug 2026, no change**

Bonnie chose to keep `2026-07-01`, which is what `build.py` already declares in `POSTS` and what
drives `datePublished` in the post's schema and `lastmod` in the sitemap. The visible line still
reads "July 2026". Nothing to do.

### S-13 · Stripe checkout links go straight to payment

The three package buttons link directly to Stripe payment links, opening in a new tab, with no
interstitial. That is deliberate as far as I can tell, and the links match what was in the Manus
build — but nobody has confirmed the three link to the right products at the right prices since
the port. Worth one test click each before launch.

### S-14 · Testimonials make strong health claims

The client stories include tumour reduction, diabetes control and cancer-treatment narratives.
The disclaimers are present, prominent and well written, and the copy is careful. Flagging only
because health claims in testimonials attract regulatory attention in some jurisdictions
regardless of disclaimers, and you are trading into the US and EU. Worth a lawyer's eye at some
point — not a blocker.

---

## Migration

### S-06 · Legacy redirects — **CLOSED 31 Aug 2026, with evidence**

The 76-row inventory Manus worked from never left the Manus machine, so rather than guess at
what was missing, the real list came out of GA4: property `421209755`, Pages and screens,
1 Jan 2024 – 30 Aug 2026. **42 distinct paths, 805 views.**

Seventeen of them had no redirect. The significant gaps:

| Path | Views | Now goes to | Why it was missed |
|---|---|---|---|
| `/work-with-me` + `/work-with-me/` | 27 | `/services/` | A real Squarespace page with no equivalent on the new site and no rule. The 14th most-visited URL. |
| Twelve dated blog posts, `/blog/YYYY/M/D/slug` | 31 | `/blog/` | Squarespace dated its blog URLs. The Manus build deliberately dropped the legacy Journal posts, so the index is the honest destination. |
| `/blog/tag/*`, `/blog/category/*` | 6 | `/blog/` | Squarespace taxonomy pages. |
| `/privacy-policy` | 4 | `/terms-and-privacy/` | |
| `/cart`, `/checkout` | 10 | `/services/` | Squarespace commerce, which dies with the platform. |
| `/search`, `/commerce/orders/*` | 2 | `/` | |

The dated-post and taxonomy rules are Netlify **placeholder and splat** rules, deliberately
**not forced** (no `!`), so a real page always wins first. That is what stops
`/blog/:year/:month/:day/:slug` from swallowing the live journal post at
`/blog/why-smart-people-stay-stuck-even-when-they-know-what-to-do/`.

**Verify with `python3 check_legacy_urls.py`.** It asserts every one of the 42 paths resolves
to a page or a 301 and fails the run if any would 404. Currently: **805 of 805 views covered,
0 would 404.**

Still worth doing after launch: keep Search Console → Pages open for a fortnight. Any URL with
no traffic in the GA4 window is not in this list, and anything that shows up 404ing can be added
to `LEGACY` in `check_legacy_urls.py` and to `REDIRECTS` in `build.py`.

### S-20 · Traffic baseline before the migration — for reference, not a snag

From the same GA4 pull, so there is a number to compare against after cutover:

- **805 views / 279 active users** across 20 months (Jan 2024 – Aug 2026)
- **57 views / 46 active users** in the last 28 days
- 2 key events in the whole period, £0 / $0 revenue recorded
- The homepage takes 31% of all views; `/clients` and `/coaching` are next

That is very low traffic — roughly 40 views a month. Worth saying plainly, because it changes
what "did the migration cost us anything" can even mean: at this volume, normal week-to-week
noise will swamp any migration effect, and the redirects matter more for the ranking signals
they preserve than for the visitors they carry today.

### S-15 · www — **DECIDED 31 Aug 2026**

**`eftsolution.com` with no www is the real address.** `www.eftsolution.com` permanently
redirects to it.

This is what the site was already built for — every `<link rel="canonical">`, the JSON-LD, the
sitemap and the share-card URLs all say `https://eftsolution.com`. Nothing had to change.

Two things now enforce it:

1. A rule in `dist/_redirects`:
   `https://www.eftsolution.com/*  →  https://eftsolution.com/:splat  301!`
2. **Set the primary domain in Netlify** — Site configuration → Domain management → set
   `eftsolution.com` as primary, add `www.eftsolution.com` as an alias. Netlify then does this
   at the edge, which is faster than the rule. The rule is belt-and-braces for a drag-and-drop
   deploy or a missed setting.

### S-16 · GHL iframes load before consent

The four GoHighLevel embeds load on page load, ahead of the consent banner. They are functional
lead-capture forms rather than tracking, which is the usual justification — but GHL does set
cookies, and a strict GDPR reading would gate them behind consent or load them on interaction.
Left as-is because gating them would hide the booking calendar behind a banner click, which
would cost real bookings.

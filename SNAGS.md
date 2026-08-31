# SNAGS — eftsolution.com port

Everything spotted during the port, logged and **not acted on** — that was the agreed scope
(`DECISIONS.md`, decision 2). Three exceptions are marked **FIXED** and explained, each one a
defect rather than a design choice.

Ordered by what would hurt most if it shipped as-is.

Status as of 31 August 2026, revised after verifying the GHL calendar directly. `check_links.py` reports S-01, S-02 and S-03 by id on every run.

---

## Launch gates — do not go live with these open

### S-05 · The booking calendar has no video conferencing at all ⛔ CONFIRMED

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

### S-18 · Nothing stops a double booking ⛔ NEW

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

### S-03 · Analytics — GA4 exists, the GTM container does not

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

**There is no eftsolution.com container.** One needs creating under the same "Bonnie Ann"
account, so both brands stay under one login. Then `GTM_ID` in `build.py` gets swapped, and a
GA4 Configuration tag pointing at `G-EL6KJYJWTB` goes inside the container.

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

### S-01 · `/services/` and `/packages/` are the same page

Both URLs render the identical fragment with the identical `<title>`, the identical meta
description, and each canonicalises to itself. Both are in the sitemap you're submitting.

That is textbook duplicate content: Google picks one, and the two pages compete rather than
compound. The legacy `/coaching/*` redirects point at `/packages/`, which is presumably why both
were kept.

**Recommended fix:** keep `/services/` as the real page, 301 `/packages/` to `/services/`
(preserving the `#clarity` / `#abundance` / `#vip` anchors, which already exist on the page), and
drop `/packages/` from the sitemap. Roughly four lines in `build.py`. Not done, because it
changes the URL set you signed off and the sitemap you're about to submit.

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

### S-08 · "20+ years of practice" badge fails contrast

On the homepage the badge sets `text-sage` (#556b5a) on `bg-sage` (#dce4d8) — about 3.7:1, below
the 4.5:1 AA threshold for text that size. The "20+" itself is ink and fine; the caption beneath
it is the problem. Ported as-is.

### S-09 · Legal pages carry their own draft warnings

`/terms-and-privacy/` says in the page body: *"The production version of this page should include
the final approved privacy and cookie policy."* `/refund-policy/` says: *"Please have this policy
reviewed for the laws that apply to your business before publishing it as final."*

Those sentences are visible to visitors. They were written as notes to you, and they read to a
customer as "we haven't finished our policies." Also: the privacy page is now the page the
consent banner links to, so it will get more traffic than it used to.

### S-10 · One privacy page doing two jobs

The footer links both "Privacy policy" and "Terms of service" to the same `/terms-and-privacy/`
URL. Fine legally, but two footer links to one destination looks like an error, and under GDPR a
distinct privacy policy is the cleaner position.

---

## Content and consistency

### S-11 · Refund policy and services FAQ disagree

The Services FAQ says a session can be rescheduled *"up to 48 hours before a session without
penalty."* The Refund Policy says *"at least 24 hours' notice."* One of them is wrong, and it is
the kind of thing a client quotes back at you.

### S-12 · Journal date is coarse

The one post is dated "July 2026" in the visible copy. The sitemap and `BlogPosting` schema need
a real date, so `build.py` currently declares `2026-07-01`. If the actual publication date
matters, set it in `POSTS`.

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

### S-15 · No `www` decision recorded

Nothing in the port states whether `www.eftsolution.com` should serve or redirect to the apex.
Netlify needs one told to it explicitly. Pick one, redirect the other, permanently.

### S-16 · GHL iframes load before consent

The four GoHighLevel embeds load on page load, ahead of the consent banner. They are functional
lead-capture forms rather than tracking, which is the usual justification — but GHL does set
cookies, and a strict GDPR reading would gate them behind consent or load them on interaction.
Left as-is because gating them would hide the booking calendar behind a banner click, which
would cost real bookings.

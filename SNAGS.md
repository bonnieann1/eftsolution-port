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

### S-19 · The site promises 15 minutes; the calendar books 60 ⛔ NEW

The homepage says *"15-minute conversation · no package decision required"* and the journal post
says *"I offer a free 15-minute conversation."*

The Free Consultation calendar in GHL is set to **1 hr**.

So either the site is under-promising by 45 minutes, or every booking is quietly taking four times
the intended slot out of Bonnie's week. Pick one and make the two agree — it is a one-line change
on the site or one setting in GHL.

### S-03 · Analytics container is a placeholder

`GTM_ID` in `build.py` is `GTM-XXXXXXX`. The consent banner and Consent Mode v2 defaults are
wired correctly, but the container does not exist, so nothing is recorded. If the site goes live
like this you will have no data on whether the migration cost you traffic — which is precisely
the week you most need it.

**Needed:** a GTM container for eftsolution.com. Swap the one constant in `build.py`.

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

### S-06 · The legacy redirect inventory is incomplete

Manus's own `site-completeness-audit.md` says its redirect work was based on a **76-row** legacy
inventory at `/home/ubuntu/seo-migration/eftsolution-redirect-map.csv`. That file was on the
Manus machine and is not in the export. Only **32 rules** made it into `redirects.json`.

So up to 44 legacy URLs may have no redirect. Every one of those is a live Squarespace page that
will 404 the moment DNS flips, losing whatever link equity and ranking it holds.

Partly mitigated: this build emits both the bare and trailing-slash form of every source, which
the Manus manifest did not — that alone would have left live 404s.

**Recommended:** before cutover, pull the full URL list from Squarespace (or Search Console →
Pages → all known URLs) and diff it against `REDIRECTS` in `build.py`. Also keep Search Console
open for the fortnight after launch and add rules for whatever 404s show up.

### S-15 · No `www` decision recorded

Nothing in the port states whether `www.eftsolution.com` should serve or redirect to the apex.
Netlify needs one told to it explicitly. Pick one, redirect the other, permanently.

### S-16 · GHL iframes load before consent

The four GoHighLevel embeds load on page load, ahead of the consent banner. They are functional
lead-capture forms rather than tracking, which is the usual justification — but GHL does set
cookies, and a strict GDPR reading would gate them behind consent or load them on interaction.
Left as-is because gating them would hide the booking calendar behind a banner click, which
would cost real bookings.

# Checkpoint — 1 September 2026, end of launch day

## Where things stand

**eftsolution.com is live on Netlify.** Migrated off Squarespace today. Verified against the
live domain, not the build: 12 pages return 200 with no redirect, 25 legacy Squarespace paths
land correctly, 23 images load, the certificate is issued, and `www` redirects to the apex.

| | |
|---|---|
| Repo | `bonnieann1/eftsolution-port`, branch `main` |
| Local | `/Users/bonnie/Documents/Claude/Projects/EFTsolution.com` |
| Netlify | project `eftsolution`, team `getailinks8`, auto-deploys from `main`, **public** |
| Registrar / DNS | Name.com |
| GTM | `GTM-KRX6Z5DB` — live, GA4 tag published |
| GA4 | property `421209755`, measurement ID `G-EL6KJYJWTB` |

## DNS as it stands (verified at the authoritative nameservers)

| Host | Type | Value |
|---|---|---|
| `eftsolution.com` | ANAME | `apex-loadbalancer.netlify.com` → `75.2.60.5`, `99.83.231.61` |
| `www` | CNAME | `eftsolution.netlify.app.` |
| `@` | MX | `mx1.titan.email`, `mx2.titan.email` — untouched |
| `@` | TXT | Titan SPF + DKIM — untouched |
| `link.` | CNAME | `brand.ludicrous.cloud` (GoHighLevel) — untouched |
| `6ad96ttrxksfdlmsxjxt` | CNAME | `verify.squarespace.com` — left deliberately, see below |

**Rollback**, while Squarespace still exists: restore four A records on the apex —
`198.185.159.144`, `198.185.159.145`, `198.49.23.144`, `198.49.23.145` — and point `www` back at
`ext-cust.squarespace.com`. TTL is 300s, so about five minutes.

## Open, in priority order

1. **Search Console — submit the sitemap.** The verified property is
   `https://www.eftsolution.com/`, which is now the *wrong* one: www redirects to the apex, so
   that property will go quiet and cannot accept a sitemap of apex URLs. Add a **URL prefix**
   property for `https://eftsolution.com`, verify via **Google Analytics** (instant, the GA4 tag
   is live under the same account), then Sitemaps → `sitemap.xml` → Submit.
   Keep the www property — it holds the search history back to May.
   The `eftsolution.com` **Domain** property is still unverified: checked again at the
   authoritative nameservers and the `google-site-verification` TXT record is genuinely absent,
   twice now. Not propagation — it is not saving at Name.com. Optional; nothing depends on it.
2. **S-13 Stripe** — the three package links have never been checked against their products and
   prices ($1,795 / $2,995 / $4,495).
3. **One live test booking** — the only way to confirm the Zoom link reaches the confirmation
   email and that a busy slot on Bonnie's calendar is blocked.
4. **Export Squarespace before cancelling** — Settings → Import/Export → WordPress format. Once
   cancelled that content is gone, and it is the only copy of anything that did not come across.
   Do not cancel for a few days; it is the rollback route.
5. **Then** delete the `6ad96ttrxksfdlmsxjxt` verification token and any other Squarespace
   leftovers.

## Parked

S-02 colour question · S-14 legal pass on the testimonials and policy pages · S-16 consent and
the GHL iframes · S-17 share card fonts · S-20 traffic baseline conversation. GoHighLevel backup
(contacts, calendars, forms, workflows) is not covered by this repo at all — a separate job.

## What today cost, and the lesson

The site was unreachable on five pages for two hours because `build.py` generated forced
self-redirects, and **both verifiers stayed green throughout**. The first fix was also wrong,
because Netlify ignores trailing slashes when matching redirect rules, so the rule kept looping
after the apparent fix deployed. Full account in SNAGS S-22.

Two rules earned the hard way:

1. A green build is not a working site. Check the generated config, not just the generated pages.
2. If a fix deploys and the symptom does not change, the diagnosis is wrong. Do not push a second
   variant of the same theory — go and read the platform's actual matching rules.

The site is now checked by loading every page and every legacy path from the live server with a
`fetch()` loop, and `check_links.py` check 9 guards the redirect file at build time.

# eftsolution.com port — locked decisions

Recorded 31 August 2026. Source of truth for this rebuild.

| # | Decision | Choice |
|---|---|---|
| 1 | Architecture | Mirror `~/Claude Code/bonnieann-port` — static HTML assembled by `python3 build.py`. One nav, one footer, one stylesheet. Not a React app. |
| 2 | Scope | Straight port of the Manus design and copy. Observations are logged to `SNAGS.md` and NOT acted on. No CMO pass before launch. |
| 3 | Location | This folder. Pushing to `github.com/bonnieann1/eftsolution-port`. |
| 4 | Cutover | Netlify preview URL for review, then straight to live. No staging subdomain. |
| 5 | Forms | The hand-built contact form on `/consultation/` and the footer newsletter form are dropped. The four approved GHL embeds are used instead. |
| 6 | Analytics | GTM behind Google Consent Mode v2, defaulting to denied. Same pattern as bonnieann.com. |

## Technical call made during the build

The Manus design is built entirely from Tailwind utility classes. Rather than hand-rewrite it as
semantic CSS and risk drifting from the design already approved, Tailwind is compiled **once**
into a frozen `shared.css` which is committed to the repo. Netlify still builds with plain
`python3 build.py` — no Node, no npm, nothing to install at deploy time. A build guard fails on
any utility class used in a page but missing from the stylesheet, so the frozen file cannot go
quietly stale.

## Open blockers

1. **Ten images.** They live only on Manus storage and were not in the export zip, not in Google
   Drive, and not on disk. Needed: hero water ripple, botanical still life, orbit art, paper
   texture, Bonnie's portrait, logo mark, supplied logo, and three journal images.
2. **GTM container ID** for eftsolution.com.
3. **Booking calendar.** The July 2026 embed handover says the Zoom link on calendar
   `q7V5rglueV1UgmYE8Urz` was a placeholder and it must not be published live until the final
   version is issued. Still unconfirmed. This is a launch gate.
4. **Legacy redirects.** The redirect work was based on a 76-row inventory that lived on the
   Manus machine. Only 32 rules survived into the export.

## Security

The Manus export's `.project-config.json` carries live secrets — a JWT secret, Forge API keys and
OAuth IDs. It is deleted, not gitignored, and must never reach the repo.

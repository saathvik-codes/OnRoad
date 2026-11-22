# OnRoad design language

The idea: **the honest price sheet.** OnRoad's job is to show the real on-road price, line by line, so the app should
feel like a well-set printed quotation or a car's spec sheet: firm headings, numbers that line up, hairline rules and
one loud signal colour. It should not look like a template.

## What we looked at

| App | What they do | What we take |
|---|---|---|
| Zomato (Sushi system) | Picked Metropolis, an open-source geometric face, and reworked it into their own font, "Okra". One red, flat cards, playful copy. | Own a typeface choice; one brand colour; witty but short notification copy. |
| CRED (NeoPOP) | Mostly monochrome screens (black and white), colour kept for moments that matter; added a serif, Cirka, for character. | Colour is a signal, not decoration. |
| Flipkart | Moved from Roboto to Inter for small-size readability. | Body text must read well at 13 to 15 sp. |
| Ather, Cars24, Spinny | Product-first: the vehicle photo and the number carry the screen. | Big price, real photo, little chrome. |

Things that make a screen read as "generated" (from the anti-AI-slop write-ups below): gradient buttons and logos,
soft-shadow rounded-2xl cards everywhere, Space Grotesk / Inter defaults, rows of tinted icon squircles, and vague
copy that could sit on any competitor's site.

## Mapping

| Token | Before | Now | Why |
|---|---|---|---|
| Headings, prices | Space Grotesk | **Archivo** at 88% width, 600 to 800 weight, tabular figures | Narrow, sturdy grotesk of spec sheets and dashboards; prices line up in columns. |
| Reading text | Geist | **Hind** (Indian Type Foundry), +1 sp | Drawn for Latin and Devanagari together, so Hindi and Marathi match the English size and weight. |
| Cards | White, 20 dp radius, soft shadow | Flat panel, 14 dp radius, 1 dp hairline | Printed-sheet feel; no floating cards. |
| Chips, buttons | 10 dp | 8 dp | Firmer, less bubbly. |
| Accent | Orange-to-pink gradient | Solid signal orange #FF4D2E | One colour, used for actions and the price. |

## Copy

Write like a friend who knows cars, the way Zomato's notifications do: one emoji at most, a concrete number, a reason
to tap. For example: "📉 Your Creta just got cheaper". Never write "Unlock amazing deals!".

## Next on the list

1. Home: replace the four tinted icon tiles with a plain text list ("Find my car ›", "Showrooms near me ›", ...).
2. Splash and app icon: the flat orange mark, no gradient.
3. Price breakdown: set it like a receipt (dotted leaders, right-aligned tabular amounts).

## Sources

- [Zomato's new Sushi Design System](https://medium.com/zomato-technology/zomatos-new-sushi-design-system-d7f4f98664c5)
- [Compose Sushi typography](https://zomato.github.io/compose-sushi/foundations/typography)
- [CRED design](https://cred.club/design) · [NeoPOP](https://cred.club/neopop)
- [Ather mobile app redesign (India's Best Design Awards)](https://ibda.design-india.com/ather-mobile-app-redesign)
- [How to detect AI slop in your design](https://github.com/Laith0003/ux-skill/wiki/How-to-detect-AI-slop-in-your-design)
- [Spot the slop: a UI designer's guide to fixing AI defaults](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c)

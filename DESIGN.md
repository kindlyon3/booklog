# Design

A library card catalog: cream stock and dark ink by day, a green reading room with brass by night. Quiet, typographic, square-cornered.

## Color

Tokens live in [`src/styles/tokens.css`](src/styles/tokens.css). Always use the token, never a raw hex value.

| Token      | Light     | Dark      | Use                                    |
| ---------- | --------- | --------- | -------------------------------------- |
| `--bg`     | `#F2EEE2` | `#18211D` | Page background                        |
| `--card`   | `#FAF8F1` | `#1F2A25` | Catalog cards, inputs                  |
| `--ink`    | `#22261F` | `#E4DDC9` | Body text, titles                      |
| `--muted`  | `#626657` | `#A3A893` | Metadata, control borders, empty stars |
| `--accent` | `#2F5A46` | `#C9A55C` | Labels, filled stars, focus, hover     |
| `--rule`   | `#D6D1C0` | `#34403A` | Decorative dividers and card borders   |

Contrast (WCAG): ink ≥ 10.9:1, accent ≥ 6.3:1, muted ≥ 5.0:1 on both `--bg` and `--card`. `--rule` is decorative only; anything interactive uses `--muted` or stronger.

### Light and dark

The site follows the system setting. The header toggle stores an explicit choice in `localStorage` as `theme`, applied by an inline script in `<head>` before first paint. Dark values are defined twice in `tokens.css`: once under `prefers-color-scheme: dark` (unless the user chose light), and once under `[data-theme="dark"]`.

## Type

| Role                        | Face              | Notes                                 |
| --------------------------- | ----------------- | ------------------------------------- |
| Titles, body                | Libre Baskerville | 400, 400 italic, 700; self-hosted     |
| Labels, dates, metadata, UI | Fira Mono         | 400; labels uppercase, tracked 0.08em |

- Site title 1.75rem, year headings 2rem, book titles 1.05rem bold.
- Edition notes and the Now Reading title are italic.
- Month headers read like a catalog drawer: `[ OCTOBER 2026 ]`.

## Spacing

`--space-1` 0.25rem · `--space-2` 0.5rem · `--space-3` 1rem · `--space-4` 1.5rem · `--space-5` 2.5rem. Content width is capped at `--measure` (52rem).

## Components

- **Catalog card** (`.card`): `--card` fill, 1px `--rule` border, square corners. One per month.
- **Now Reading:** dashed 1px `--accent` border, the only dashed accent on the page.
- **Book row:** cover · title, byline, metadata (`1985 · 316 pp · fiction`) · stars. Rows separated by dashed `--rule` lines. Below 30rem the stars move under the text.
- **Cover:** 3.5rem wide, 2:3, 1px `--rule` border. With no image, a placeholder shows the title in small mono caps.
- **Stars:** five outline stars in `--muted`, filled with `--accent` and clipped to the rating, so half stars are exact. Exposed as "4.5 out of 5". Unrated books show no stars.
- **Filters:** search, year, form, minimum rating. Hidden without JavaScript; the full list still shows. State is kept in the URL query.
- **Label** (`.label`): mono, uppercase, `--accent`.
- **Meta** (`.meta`): mono, 0.75rem, `--muted`.

## Do / don't

- Do keep corners square and borders 1px.
- Do use mono only for labels, dates, numbers, and controls.
- Don't add shadows, gradients, or rounded corners.
- Don't introduce new colors; extend the tokens if something is missing.

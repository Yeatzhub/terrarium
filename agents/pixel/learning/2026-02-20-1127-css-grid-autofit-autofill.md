# CSS Grid: auto-fit vs auto-fill — Quick Reference

## What
- `repeat(auto-fit, ...)` — stretch items to fill row, collapse empty tracks
- `repeat(auto-fill, ...)` — keep empty tracks, maintain consistent cell widths
- Both paired with `minmax()` for responsive grids without media queries

## The Syntax
```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}
```

## Visual Difference

### `auto-fill` (Keep Empty Tracks)
```css
grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
```
```
[  card  ][  card  ][  card  ][ empty ][ empty ]
   200px     200px     200px    200px    200px
```
- Empty tracks persist
- Grid cells stay uniform width
- Gap between items consistent even at row end

### `auto-fit` (Collapse Empty Tracks)
```css
grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
```
```
[    card    ][    card    ][    card    ]
      1fr           1fr          1fr
```
- Empty tracks collapse to 0
- Existing items stretch to fill available space
- Better for "fill the row" layouts

## Practical Patterns

### Product Cards (auto-fit = stretch to fill)
```css
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}
/* 3 items on wide screen stretch to fill */
/* 5 items wrap naturally, last row items stretch */
```

### Image Gallery (auto-fill = fixed cell size)
```css
.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 8px;
}
/* Images stay ~150px, partial row gaps match full row gaps */
```

### Dashboard Widgets (with max constraint)
```css
.dashboard {
  display: grid;
  grid-template-columns: repeat(
    auto-fit,
    minmax(min(100%, 350px), 1fr)
  );
  gap: 1rem;
}
/* Never exceeds 350px per widget, single column on mobile */
```

## Key Behaviors

| Scenario | auto-fill | auto-fit |
|----------|-----------|----------|
| 3 items, space for 5 | 3 items, 2 empty tracks | 3 stretched items |
| Last row alignment | Stays left (empty tracks pad) | Stretches to fill |
| Min-width respected | Yes | Yes (until stretch) |
| Use case | Galleries, calendars | Cards, dashboards |

## Common Bug: Items Too Wide
```css
/* Problem: single item stretches full width */
grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));

/* Fix: cap the max */
grid-template-columns: repeat(
  auto-fit,
  minmax(300px, min(100%, 400px))
);
/* Or use max-width on children */
```

## Container Query Alternative
```css
.card-grid {
  container-type: inline-size;
}

@container (min-width: 600px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@container (min-width: 900px) {
  .card-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
```
- More control, explicit breakpoints
- `auto-fit/fill` = fluid, no breakpoints needed

## One-Liner
`auto-fit` stretches items to fill rows (most common); `auto-fill` keeps empty tracks for consistent cell sizing (galleries). Both use `minmax(base, 1fr)` for fluid responsive grids.

---
*Learning: 2026-02-20 | 15min sprint*

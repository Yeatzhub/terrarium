# CSS Grid Patterns — Quick Reference

**Topic:** CSS Grid Layout Patterns  
**Learned:** 2026-02-19 01:24 CST  
**Time:** 15 min

---

## 1. Holy Grail Layout (Header/Footer/3-col)

```css
.holy-grail {
  display: grid;
  grid-template: 
    "header header header" auto
    "left   main   right " 1fr
    "footer footer footer" auto
    / 200px 1fr 200px;
  min-height: 100vh;
  gap: 1rem;
}

.holy-grail > header { grid-area: header; }
.holy-grail > aside  { grid-area: left; }
.holy-grail > main   { grid-area: main; }
.holy-grail > .right { grid-area: right; }
.holy-grail > footer { grid-area: footer; }
```

**When:** Dashboards, admin panels, classic web layouts.  
**Mobile:** `grid-template-columns: 1fr` + `grid-template-rows: auto` on breakpoint.

---

## 2. Auto-Fit Card Grid (Responsive Gallery)

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}
```

- Cards stretch to fill, wrap when cramped  
- No media queries needed — intrinsic responsiveness

**When:** Product grids, photo galleries, card lists.

---

## 3. Dense Masonry-ish (Pinterest-style)

```css
.masonry {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  grid-auto-rows: 10px;
  gap: 1rem;
}

.masonry > * { grid-row: span calc(var(--item-height, 20)); }
```

Set `--item-height` per item via inline style or JS based on content aspect ratio.

**When:** Image galleries, content feeds with variable heights.

---

## 4. Sidebar That Collapses

```css
.layout {
  display: grid;
  grid-template-columns: minmax(0, 250px) 1fr;
  transition: grid-template-columns 0.3s ease;
}

.layout.collapsed {
  grid-template-columns: 60px 1fr;
}
```

Use `minmax(0, ...)` to prevent overflow. Toggle `.collapsed` class via JS.

**When:** Docs sites, apps with collapsible nav.

---

## 5. Aspect Ratio Grid (Uniform Thumbnails)

```css
.thumb-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
}

.thumb-grid > * {
  aspect-ratio: 1;
  object-fit: cover;
}
```

**When:** Logo grids, equal-size preview tiles.

---

## Key Insights

| Pattern | Property | Why It Works |
|---------|----------|--------------|
| Responsive | `auto-fit` + `minmax()` | Handles breakpoints automatically |
| Performance | `grid-auto-rows` | Reduces reflows for dynamic content |
| Animation | `grid-template-columns` | Animateable in modern browsers |
| Fallback | `@supports not (display: grid)` | Flexbox backup for old browsers |

---

## Quick Copy-Paste Starter

```css
.grid-base {
  display: grid;
  gap: var(--gap, 1rem);
}
```

Use CSS custom properties for gap values — easy to override per component.

---

**Next:** Explore `subgrid` for nested component alignment (Firefox+ Chrome 117+).

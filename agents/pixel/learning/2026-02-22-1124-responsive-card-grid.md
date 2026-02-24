# Responsive Card Grid — CSS Pattern

A robust, auto-fitting card grid using modern CSS (no media queries needed).

## The Pattern

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
  gap: 1.5rem;
}
```

That's it. One line does all the heavy lifting.

## How It Works

```
auto-fit     → Fill available space with as many columns as fit
minmax()     → Each column is at least 280px, at most 1fr (equal share)
min()        → Prevents overflow when 280px > viewport width
```

### Behavior at Different Viewports

| Viewport | Columns |
|----------|---------|
| < 280px  | 1 (full width) |
| 280-560px | 1 |
| 560-840px | 2 |
| 840-1120px | 3 |
| 1120px+ | 4+ |

## Complete Example

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
  gap: 1.5rem;
  padding: 1rem;
}

.card {
  background: var(--surface);
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  
  /* Prevent content from stretching weirdly */
  display: flex;
  flex-direction: column;
}

.card__content {
  flex: 1; /* Push footer to bottom */
}

.card__footer {
  margin-top: auto;
}
```

## Variants

### Fixed Max Columns

```css
.card-grid--max-3 {
  grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
  max-width: calc(3 * 280px + 2 * 1.5rem); /* 3 cards max */
}
```

### Variable Width Cards (masonry-ish)

```css
.card-grid--masonry {
  columns: 280px;
  column-gap: 1.5rem;
}

.card {
  break-inside: avoid; /* Don't split cards */
  margin-bottom: 1.5rem;
}
```

### Sidebar + Grid Layout

```css
.layout-with-sidebar {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 2rem;
}

@media (max-width: 768px) {
  .layout-with-sidebar {
    grid-template-columns: 1fr; /* Stack on mobile */
  }
}
```

## Why This Over Media Queries

| Media Queries | Auto-fit |
|--------------|----------|
| Hard breakpoints per design | Adapts to any viewport |
| Update in multiple places | Single source of truth |
| Guess at device sizes | Content-driven sizing |
| Complex calc for gaps | Built-in gap handling |

## Quick Reference

```css
/* Minimum viable card grid */
grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));

/* Tighter cards (dashboard widgets) */
grid-template-columns: repeat(auto-fit, minmax(min(200px, 100%), 1fr));

/* Larger cards (feature blocks) */
grid-template-columns: repeat(auto-fit, minmax(min(350px, 100%), 1fr));
```

## Browser Support

Full support in all modern browsers. `min()` function needs Safari 11.1+. For older browsers, use `minmax(280px, 1fr)` with a container query fallback.
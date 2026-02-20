# CSS Container Queries — Quick Reference

## What
- `@container` queries styles based on a **container's size**, not viewport
- Solves: "I want this card to adapt to its parent, not the screen"
- Supported: Chrome/Edge 105+, Firefox 110+, Safari 16+

## How

### 1. Define a container
```css
.card-grid {
  container-type: inline-size; /* watches width */
}

/* or named container */
.card-grid {
  container-type: inline-size;
  container-name: cards;
}
```

### 2. Query inside children
```css
.card {
  padding: 1rem;
  font-size: 0.875rem;
}

/* When container is 400px+ wide */
@container (min-width: 400px) {
  .card {
    display: flex;
    gap: 1rem;
    font-size: 1rem;
  }
}

/* Named container variant */
@container cards (min-width: 600px) {
  .card {
    padding: 2rem;
  }
}
```

## Container Types
| Type | Description |
|------|-------------|
| `size` | Watches width AND height (adds containment) |
| `inline-size` | Watches width only (most common, use this) |
| `normal` | Style + custom property queries, no size |

## Style Queries (Next Level)
```css
/* Query custom property value */
@container style(--card-variant: featured) {
  .card { border: 2px solid gold; }
}

/* Works with inline styles or CSS custom properties */
```

## Key Differences from Media Queries
```css
/* Media query: "Is screen wide?" */
@media (min-width: 768px) { }

/* Container query: "Is this specific container wide?" */
@container (min-width: 768px) { }
```

## Practical Pattern: Reusable Card
```html
<div class="card-wrapper"> <!-- container -->
  <div class="card">...</div>
</div>
```

```css
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

.card {
  @container card (min-width: 0px) {
    /* default: stacked */
  }
  @container card (min-width: 300px) {
    /* horizontal layout */
    display: grid;
    grid-template-columns: auto 1fr;
  }
}
```

## When to Use
✅ Component libraries (cards adapt to any parent)  
✅ Sidebar + main layouts (content adapts to available space)  
✅ Reusable widgets (same component, different contexts)  

## When NOT to Use
❌ Page-level layout (use @media)  
❌ Performance-critical micro-interactions (costs containment)  

## One-Liner
`container-type: inline-size` on parent, `@container` rules in child. Same component, infinite contexts.

---
*Learning: 2026-02-20 | 15min sprint*

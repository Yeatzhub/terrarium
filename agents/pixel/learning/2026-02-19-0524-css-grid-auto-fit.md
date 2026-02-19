# CSS Grid: Auto-Fit with Minmax

**Pattern:** Responsive grid without media queries

## The One-Liner
```css
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}
```

## How It Works

| Piece | Purpose |
|-------|---------|
| `repeat()` | Creates multiple columns |
| `auto-fit` | Collapses empty tracks; stretches items to fill |
| `minmax(250px, 1fr)` | Minimum 250px, maximum equal share of space |

## Practical Example: Card Grid

```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  padding: 1rem;
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
```

```html
<div class="card-grid">
  <div class="card">Card 1</div>
  <div class="card">Card 2</div>
  <div class="card">Card 3</div>
  <!-- Automatically wraps when screen narrows -->
</div>
```

## Variations

**Fixed number with responsiveness:**
```css
grid-template-columns: repeat(auto-fit, minmax(clamp(200px, 30%, 300px), 1fr));
```

**Dense packing (fill gaps):**
```css
grid-auto-flow: row dense;
```

## Common Gotchas

1. **Container needs width** — `auto-fit` only works if container has defined width
2. **Single column fails** — Use `minmax(min(100%, 250px), 1fr)` for mobile safety
3. **auto-fit vs auto-fill** — `auto-fit` stretches; `auto-fill` keeps empty columns

## When to Use

- Dashboard widgets
- Product galleries
- Feature lists
- Photo grids
- Any "as many as fit" layout

---
*Learned: 2026-02-19* | *Time: ~10 min* | *Reference: https://css-tricks.com/auto-sizing-columns-css-grid-auto-fill-vs-auto-fit/*

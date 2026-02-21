# CSS Pattern: Grid Subgrid

Nested grids that inherit parent's columns/rows. Perfect for cards, forms, and complex layouts. All modern browsers support (2024).

## The Problem

```css
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.card {
  display: grid;
  grid-template-columns: 1fr; /* Ignores parent's 3 columns */
}
/* Cards don't align across rows */
```

## The Solution: Subgrid

```css
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.card {
  grid-column: span 1;
  display: grid;
  grid-template-columns: subgrid; /* Inherits parent's columns */
  grid-template-rows: subgrid;    /* Inherits parent's rows */
  gap: 0; /* Use parent's gap */
}
```

## Complete Card Grid Example

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    * { margin: 0; box-sizing: border-box; }
    body { font-family: system-ui; padding: 40px; background: #f5f5f5; }
    
    /* Parent grid: 3 columns */
    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      /* Implicit row definition for subgrid */
      grid-auto-rows: auto auto 1fr auto;
      gap: 24px 20px;
    }
    
    /* Card adopts parent's 3 column tracks */
    .card {
      grid-column: span 1;
      display: grid;
      grid-template-columns: subgrid;
      grid-template-rows: subgrid;
      grid-row: span 4; /* Occupy 4 implicit rows */
      
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .card__image {
      grid-column: 1 / -1;
      aspect-ratio: 16/9;
      background: linear-gradient(45deg, #667eea, #764ba2);
    }
    
    .card__category {
      grid-column: 1 / -1;
      padding: 16px 16px 0;
      font-size: 0.75rem;
      text-transform: uppercase;
      color: #667eea;
      font-weight: 600;
    }
    
    .card__content {
      grid-column: 1 / -1;
      padding: 8px 16px;
      display: flex;
      flex-direction: column;
    }
    
    .card__title {
      font-size: 1.25rem;
      margin-bottom: 8px;
    }
    
    .card__text {
      color: #666;
      font-size: 0.95rem;
    }
    
    .card__footer {
      grid-column: 1 / -1;
      padding: 16px;
      border-top: 1px solid #eee;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  </style>
</head>
<body>
  <div class="grid">
    <article class="card">
      <div class="card__image"></div>
      <span class="card__category">Tutorial</span>
      <div class="card__content">
        <h3 class="card__title">CSS Grid Mastery</h3>
        <p class="card__text">Learn the power of modern CSS layouts</p>
      </div>
      <div class="card__footer">
        <span>5 min read</span>
        <span>→</span>
      </div>
    </article>
    
    <article class="card">
      <div class="card__image"></div>
      <span class="card__category">Guide</span>
      <div class="card__content">
        <h3 class="card__title">Ultimate Guide to Subgrid</h3>
        <p class="card__text">Deep dive into nested grid systems with real-world examples and use cases</p>
      </div>
      <div class="card__footer">
        <span>15 min read</span>
        <span>→</span>
      </div>
    </article>
    
    <article class="card">
      <div class="card__image"></div>
      <span class="card__category">Quick Tip</span>
      <div class="card__content">
        <h3 class="card__title">Align Cards</h3>
        <p class="card__text">Perfect alignment</p>
      </div>
      <div class="card__footer">
        <span>2 min read</span>
        <span>→</span>
      </div>
    </article>
  </div>
</body>
</html>
```

## The Result

```
┌─────────────────┬─────────────────┬─────────────────┐
│                 │                 │                 │
│     IMAGE       │     IMAGE       │     IMAGE       │  ← Same height
│                 │                 │                 │
├─────────────────┼─────────────────┼─────────────────┤
│ CATEGORY        │ CATEGORY        │ CATEGORY        │  ← Aligned
├─────────────────┼─────────────────┼─────────────────┤
│ Long text here  │ Short           │ Medium          │  ← Cards stretch
│ grows card      │                 │ text here       │    to match
├─────────────────┼─────────────────┼─────────────────┤
│ Footer          │ Footer          │ Footer          │  ← Always at bottom
└─────────────────┴─────────────────┴─────────────────┘
```

## Form Alignment with Subgrid

```css
.form {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16px 20px;
}

.form__group {
  grid-column: span 2;
  display: grid;
  grid-template-columns: subgrid;
  align-items: center;
}

.form__label {
  justify-self: end;
  padding-right: 8px;
}

.form__input {
  max-width: 400px;
}
```

```html
<form class="form">
  <div class="form__group">
    <label class="form__label">Name</label>
    <input class="form__input" />
  </div>
  <div class="form__group">
    <label class="form__label">Email Address</label>
    <input class="form__input" />
  </div>
</form>
```

Result: Labels automatically right-align to the same width, inputs start at same column.

## Horizontal Subgrid

```css
.features {
  display: grid;
  grid-auto-flow: column;
  grid-template-rows: auto auto auto;
  gap: 20px;
}

.feature {
  display: grid;
  grid-template-rows: subgrid;
  grid-row: 1 / -1; /* Span all 3 rows */
  gap: 12px;
  text-align: center;
}

.feature__icon { font-size: 2rem; }
.feature__title { font-weight: 600; }
```

```html
<div class="features">
  <div class="feature">
    <div class="feature__icon">🚀</div>
    <h3 class="feature__title">Fast</h3>
    <p>Lightning quick</p>
  </div>
  <div class="feature">
    <div class="feature__icon">🔒</div>
    <h3 class="feature__title">Secure</h3>
    <p>Bank-level encryption keeps your data safe with enterprise security</p>
  </div>
</div>
```

Result: Icons align, titles align, descriptions vary but have consistent spacing.

## Mixed: Subgrid + Named Lines

```css
.layout {
  display: grid;
  grid-template-columns:
    [sidebar-start] 200px
    [main-start] 1fr
    [main-end sidebar-end];
}

.content {
  grid-column: main;
  display: grid;
  grid-template-columns: subgrid;
}

.card-grid {
  grid-column: span 2;
  display: grid;
  grid-template-columns: repeat(2, subgrid);
}
```

## Browser Support

- ✅ Chrome/Edge 115+
- ✅ Safari 16+
- ✅ Firefox 115+
- ✅ iOS Safari 16+
- ✅ Android Chrome 115+

**Feature Query:**
```css
@supports (grid-template-columns: subgrid) {
  .card { grid-template-columns: subgrid; }
}

@supports not (grid-template-columns: subgrid) {
  /* Fallback: standard grid or flexbox */
  .card { display: flex; flex-direction: column; }
}
```

## Common Patterns

### Sidebar + Content
```css
.page {
  display: grid;
  grid-template-columns: 250px [content-start] 1fr [content-end];
}

.main {
  grid-column: content;
  display: grid;
  grid-template-columns: subgrid;
}

.full-width { grid-column: 1 / -1; }
```

### Gallery with Captions
```css
.gallery {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 200px min-content;
}

.gallery__item {
  display: grid;
  grid-template-rows: subgrid;
  grid-row: span 2;
}
```

## Key Differences from Regular Grid

| Feature | Regular Grid | Subgrid |
|---------|--------------|---------|
| Tracks | Defines own | Inherits parent's |
| Gap | Defines own | Inherits or overrides |
| Alignment | Isolated | Aligned with siblings |
| Item sizing | Independent | Matches siblings |

## Debugging

```css
/* Visualize grid tracks */
.grid, .card {
  outline: 2px dashed #667eea;
}
.grid > *, .card > * {
  outline: 1px solid #764ba2;
}
```

## Performance

- Subgrid has ~same cost as regular grid
- No reflow cascade beyond normal grid behavior
- Use when alignment across siblings matters
- Skip for independent, unrelated components

---
*Learned: 2026-02-21 | 15-min sprint*

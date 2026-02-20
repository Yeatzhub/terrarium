# CSS :has() — The Parent Selector

## What
- Selects elements based on their children or siblings
- Previously impossible in CSS (required JS)
- Supported: Chrome 105+, Firefox 121+, Safari 15.4+ (2023+)

## Basic Syntax
```css
/* Parent has specific child */
.card:has(.badge) { border-color: gold; }

/* Element has specific sibling */
.item:has(+ .item.active) { margin-top: 2rem; }

/* Complex: form field with error message */
.field:has(.error) input { border-color: red; }
```

## Practical Patterns

### Form Validation States
```css
/* Red border when error exists */
.form-group:has(.error-message) input {
  border-color: var(--error);
  background: var(--error-bg);
}

/* Green when valid (has checkmark icon) */
.form-group:has(.icon-check) input {
  border-color: var(--success);
}
```

### Card Variants by Content
```css
/* Featured card has image */
.card:has(img) {
  grid-template-columns: 200px 1fr;
}

/* Compact card (no description) */
.card:not(:has(p)) {
  padding: 0.75rem;
  gap: 0.5rem;
}

/* Card with action buttons gets hover state */
.card:has(.btn) {
  cursor: pointer;
}
.card:has(.btn):hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
```

### Navigation Active States
```css
/* Highlight parent when any child is active */
.nav-item:has(.nav-link.active) {
  background: var(--nav-active-bg);
}

/* Dropdown open state */
.dropdown:has(.dropdown-toggle[aria-expanded="true"]) {
  z-index: 100;
}
```

### Layout Adjustments
```css
/* Sidebar gets wider if it has widgets */
.sidebar:has(.widget) {
  min-width: 280px;
}
.sidebar:not(:has(.widget)) {
  min-width: 200px;
}

/* Grid cell with image spans 2 rows */
.grid-item:has(img) {
  grid-row: span 2;
}
```

### Quantity Queries (New Power)
```css
/* List has 3+ items: switch to grid */
.item-list:has(> :nth-child(3)) {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

/* Exactly 2 items: side by side */
.item-list:has(> :nth-child(2)):not(:has(> :nth-child(3))) {
  display: flex;
  gap: 1rem;
}
```

## Chained :has()
```css
/* Card has image AND is featured */
.card:has(img):has(.badge--featured) {
  border: 2px solid gold;
}

/* Shorthand with :is() */
.card:has(:is(img, video)) {
  /* Card has img OR video */
}
```

## Sibling Combinations
```css
/* Previous sibling selector (finally!) */
.item:has(+ .item.active) {
  /* Item immediately before active item */
  margin-bottom: 1rem;
}

/* Section before heading gets extra space */
section:has(+ h2) {
  margin-bottom: 3rem;
}
```

## Performance Note
```css
/* ✅ Fast - direct children */
.card:has(> img) { }

/* ⚠️ Slower - any descendant */
.card:has(img) { }

/* ✅ Use class instead of element */
.card:has(.thumbnail) { }
```

## JavaScript Fallback
```js
// Polyfill pattern
if (!CSS.supports('selector(:has(*))')) {
  document.querySelectorAll('.card').forEach(card => {
    if (card.querySelector('img')) {
      card.classList.add('card--has-image');
    }
  });
}
```

## Do / Don't

✅ **Do**
- Use for presentational changes (borders, spacing)
- Combine with `:not()` for conditional logic
- Prefer class-based has() over element-based for performance

❌ **Don't**
- Use for layout shifts (CLS risk)
- Nest deeply: `.a:has(.b:has(.c))` (expensive)
- Replace all JS logic (complex interactions still need JS)

## One-Liner
`:has()` is the "parent selector" — style ancestors based on descendants. `.card:has(img)` means "style the card that contains an image." Eliminates JS class toggling for structural styling.

---
*Learning: 2026-02-20 | 15min sprint*

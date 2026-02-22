# CSS Pattern: The :has() Selector

Parent selection in CSS. Previously impossible without JS. Supported in all modern browsers (2023+). "The parent selector that never was... now is."

## The Revolution

```css
/* BEFORE: Only select children */
.parent .child { color: red; }

/* NOW: Select parent based on child! */
.parent:has(.child) { border: 2px solid red; }
```

## Quick Wins

```css
/* Form with invalid input */
.form-group:has(input:invalid) {
  border-color: #ef4444;
}

.form-group:has(input:invalid) .label {
  color: #ef4444;
}

/* Card with image - add spacing */
.card:has(img) {
  padding-top: 0;
}

/* Card without image - different layout */
.card:not(:has(img)) {
  display: flex;
  align-items: center;
}

/* Empty list */
.list:has(:empty) {
  display: none;
}

/* Figure with caption */
figure:has(figcaption) {
  margin-bottom: 24px;
}

/* Active focus trap */
body:has(.modal[open]) {
  overflow: hidden;
}
```

## Complete Form Validation Example

```html
<form class="form" novalidate>
  <div class="form-group">
    <label class="form-group__label">Email</label>
    <input 
      type="email" 
      class="form-group__input" 
      required
      placeholder="you@example.com"
    />
    <span class="form-group__error">Please enter a valid email</span>
  </div>
  
  <div class="form-group">
    <label class="form-group__label">Password</label>
    <input 
      type="password" 
      class="form-group__input" 
      required
      minlength="8"
    />
    <span class="form-group__error">Minimum 8 characters</span>
  </div>
  
  <button type="submit" class="btn">Submit</button>
</form>
```

```css
/* Base styles */
.form-group {
  margin-bottom: 16px;
  position: relative;
}

.form-group__label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  transition: color 0.2s;
}

.form-group__input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e5e5e5;
  border-radius: 8px;
  transition: border-color 0.2s;
}

.form-group__error {
  display: none;
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 4px;
}

/* :has() magic - style parent based on input state! */

/* Valid state */
.form-group:has(input:valid:not(:placeholder-shown)) {
  --color: #10b981;
}

.form-group:has(input:valid:not(:placeholder-shown)) .form-group__label {
  color: var(--color);
}

.form-group:has(input:valid:not(:placeholder-shown)) .form-group__input {
  border-color: var(--color);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='%2310b981' viewBox='0 0 20 20'%3E%3Cpath d='M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  background-size: 20px;
}

/* Invalid state - only after interaction */
.form-group:has(input:invalid:not(:placeholder-shown):not(:focus)) {
  --color: #ef4444;
}

.form-group:has(input:invalid:not(:placeholder-shown):not(:focus)) .form-group__label {
  color: var(--color);
}

.form-group:has(input:invalid:not(:placeholder-shown):not(:focus)) .form-group__input {
  border-color: var(--color);
}

.form-group:has(input:invalid:not(:placeholder-shown):not(:focus)) .form-group__error {
  display: block;
}
```

**Result:** Zero JavaScript for form validation styling. Parent `.form-group` changes based on child input state.

## Modal Focus Trap

```css
/* Scroll lock when modal is open */
body:has(.modal[open]) {
  overflow: hidden;
}

/* Dim background */
body:has(.modal[open])::before {
  content: "";
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
  animation: fade-in 0.2s ease;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
```

```html
<body>
  <main>...</main>
  <dialog class="modal">
    <h2>Modal Title</h2>
    <p>Content here</p>
  </dialog>
</body>
```

No JavaScript needed for the overlay effect.

## Table Row Highlighting

```css
/* Highlight row when cell is hovered */
tr:has(td:hover) {
  background-color: #f0f9ff;
}

/* Highlight row when containing a focused input */
tr:has(input:focus) {
  background-color: #fafafa;
}

/* Style figure based on content */
figure:has(figcaption) img {
  border-radius: 8px 8px 0 0;
}

figure:not(:has(figcaption)) img {
  border-radius: 8px;
}
```

## Card Layout Variants

```css
/* Card with image */
.card:has(.card__image) {
  display: grid;
  grid-template-rows: auto 1fr;
}

.card:has(.card__image) .card__content {
  padding: 16px;
}

/* Horizontal card when image exists */
.card:has(.card__image).card--horizontal {
  grid-template-columns: 200px 1fr;
  grid-template-rows: auto;
}

/* Card without image */
.card:not(:has(.card__image)) {
  padding: 20px;
}

/* Card with icon */
.card:has(.card__icon) {
  padding-top: 48px;
  position: relative;
}

.card:has(.card__icon) .card__icon {
  position: absolute;
  top: -24px;
  left: 24px;
}
```

## Select Previous Sibling

```css
/* Style label when following input is focused */
label:has(+ input:focus) {
  color: #3b82f6;
}

/* Style previous heading when following paragraph is hovered */
h1:has(+ p:hover),
h2:has(+ p:hover),
h3:has(+ p:hover) {
  color: #3b82f6;
}

/* Icon color when input is focused */
.icon:has(+ .input:focus) {
  color: #3b82f6;
}

/* Previous item when dropdown inside is open */
.nav-item:has(.dropdown[open]) {
  background: #f5f5f5;
}
```

## Nested Selection

```css
/* Header when nav contains active link */
header:has(nav a.active) {
  border-bottom: 2px solid #3b82f6;
}

/* Article when comments exist */
.article:has(.comments .comment) .comments-count {
  display: inline;
}

/* Section when any item is selected */
section:has(.item.selected) {
  background: #fafafa;
}

/* List when item is being dragged */
.list:has(.item.dragging) {
  opacity: 0.5;
}
```

## Quantity Queries

```css
/* List with more than 4 items */
.list:has(:nth-child(4):last-child),
.list:has(:nth-child(n+5)) {
  column-count: 2;
}

/* Exactly one item (center it) */
.gallery:has(.card:only-child) {
  justify-content: center;
}

/* Too many items (trigger compact mode) */
.menu:has(:nth-child(n+7)) .menu-item {
  font-size: 0.875rem;
  padding: 8px;
}
```

## Error State Detection

```css
/* Form has any invalid fields */
form:has(input:invalid:not(:placeholder-shown)) .btn[type="submit"] {
  opacity: 0.5;
  pointer-events: none;
  cursor: not-allowed;
}

/* Section with errors */
.section:has(.error) {
  border: 1px solid #ef4444;
  background: #fef2f2;
}

/* Input group when any is empty */
.input-group:has(input:placeholder-shown) .btn {
  background: #e5e5e5;
}
```

## Browser Support

| Browser | Version | Date |
|---------|---------|------|
| Chrome | 105+ | Aug 2022 |
| Safari | 15.4+ | Mar 2022 |
| Firefox | 121+ | Dec 2023 |
| Edge | 105+ | Aug 2022 |
| iOS Safari | 15.4+ | Mar 2022 |
| Android Chrome | 105+ | Aug 2022 |

**Feature Query:**
```css
@supports selector(:has(*)) {
  /* :has() supported */
  .parent:has(.child) { ... }
}

@supports not selector(:has(*)) {
  /* Fallback: JS or alternative selectors */
  .parent.has-child { ... }
}
```

## Performance Guidelines

| ✅ Good | ❌ Avoid |
|---------|----------|
| Direct children | Deep nesting |
| Simple selectors | Complex chains |
| Single :has() | Multiple chained |
| State-based | Continuous re-evaluation |

```css
/* Fast - direct child, simple */
.card:has(> img) { }

/* Slow - deep, complex */
.container:has(.list .item .content:hover) { }

/* Very slow - chained :has */
article:has(h2:has(+ p:has(strong))) { }
```

## Common Patterns Cheatsheet

```css
/* Parent styling based on child state */
.field:has(input:focus)
.field:has(input:invalid)
.field:has(select[multiple])

/* Sibling reverse selection */
label:has(+ input)
dt:has(+ dd)
h2:has(+ p)

/* Quantity queries */
.grid:has(:nth-child(n+5))
.list:has(:only-child)

/* Empty/hidden handling */
.group:has(.item:hidden)
section:has(:empty)

/* State changes */
body:has(.modal)
nav:has(.active)
figure:has(figcaption)

/* Error detection */
form:has(:invalid:not(:placeholder-shown))
```

## Real-World Example: Multi-Step Form

```css
/* Progress indicator */
.steps { display: flex; gap: 8px; }

.step {
  width: 32px;
  height: 4px;
  background: #e5e5e5;
  border-radius: 2px;
}

/* Active step based on form state */
form:has([data-step="1"] .step-content) ~ .steps .step:nth-child(1),
form:has([data-step="2"] .step-content) ~ .steps .step:nth-child(2),
form:has([data-step="3"] .step-content) ~ .steps .step:nth-child(3) {
  background: #3b82f6;
}

/* Completed steps */
form:has([data-step="2"] .step-content) ~ .steps .step:nth-child(1),
form:has([data-step="3"] .step-content) ~ .steps .step:nth-child(1),
form:has([data-step="3"] .step-content) ~ .steps .step:nth-child(2) {
  background: #10b981;
}
```

---
*Learned: 2026-02-22 | 15-min sprint*
# CSS :is() and :where() — Quick Reference

## What
- `:is()` — Group selectors, specificity = highest argument
- `:where()` — Group selectors, specificity = 0 (always)
- Both reduce repetition, clean up complex selectors
- Supported: Chrome 88+, Firefox 78+, Safari 14+ (2021+)

## The Difference

| Pseudo-class | Specificity | Use Case |
|-------------|-------------|----------|
| `:is()` | Matches highest specificity argument | Grouping without losing cascade control |
| `:where()` | Always 0 | Utility classes, resets, safe overrides |

## :is() — Smart Grouping

### Before (Repetitive)
```css
h1 span,
h2 span,
h3 span,
.title span {
  color: var(--accent);
}
```

### After (Compact)
```css
:is(h1, h2, h3, .title) span {
  color: var(--accent);
}
```

### Nested :is()
```css
:is(header, footer, aside) :is(h1, h2, h3) {
  /* header h1, header h2... footer h1, footer h2... etc */
  font-family: var(--heading-font);
}
```

### Specificity Note
```css
/* Specificity = 0,1,0 (class) — matches .title */
:is(h1, .title) span { }

/* Even though h1 is 0,0,1, .title is 0,1,0 */
/* So the whole block has 0,1,0 specificity */
```

## :where() — Zero-Specificity Grouping

### Utility Class Pattern
```css
/* Specificity: 0,0,0 — can be overridden by any element selector */
:where(.text-center) {
  text-align: center;
}

:where(.m-0) {
  margin: 0;
}

:where(.p-4) {
  padding: 1rem;
}
```

### Why it matters
```html
<p class="text-center">Centered</p>
```

```css
/* This now wins (0,0,1 vs 0,0,0) */
p {
  text-align: left;
}

/* If .text-center wasn't wrapped in :where(), */
/* it would have 0,1,0 and beat the p selector */
```

### Perfect for Resets
```css
/* Zero specificity means easy overrides */
:where(*, *::before, *::after) {
  box-sizing: border-box;
}

:where(ul, ol) {
  margin: 0;
  padding: 0;
  list-style: none;
}

:where(h1, h2, h3, h4, h5, h6) {
  margin: 0;
  font-weight: var(--heading-weight);
}
```

## Forgiving Selector List

Both `:is()` and `:where()` are **forgiving** — invalid selectors don't break the whole rule:

```css
/* Works even if :not-yet-supported is invalid */
:is(.valid, :not-yet-supported, .also-valid) {
  color: red;
}

/* Standard grouping would FAIL entirely */
.valid, :not-yet-supported, .also-valid {
  /* Invalid selector list fails completely */
}
```

## Practical Patterns

### Component Variants
```css
/* Button variants — no extra specificity */
.btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
}

/* Same specificity as .btn (0,1,0) */
:where(.btn-primary, .btn-secondary) {
  font-weight: 500;
}

.btn-primary { background: blue; }
.btn-secondary { background: gray; }
```

### Complex Nesting Cleanup
```css
/* Messy */
nav ul li a:hover,
nav ul li a:focus,
.sidebar ul li a:hover,
.sidebar ul li a:focus { }

/* Cleaner with :is() */
:is(nav, .sidebar) ul li a:is(:hover, :focus) { }
```

### Safe Global Overrides
```css
/* Low risk — easy to override later */
:where(:any-link) {
  text-decoration: none;
}

/* Later override still works */
.footer a {
  text-decoration: underline;
}
```

## Specificity Comparison

```css
/* 0,1,0 (class) — .title wins */
:is(h1, .title) { }

/* 0,0,0 — can be beaten by element selector */
:where(h1, .title) { }

/* Specificity: 0,2,0 (two classes) */
:is(.title, .heading) :is(.subheading, .subtitle) { }
```

## Common Mistakes

```css
/* ❌ :where() for base styles that need strength */
:where(.card) { border: 1px solid gray; }

/* Any later .border-none { border: none; } will win ✗ */

/* ✅ :is() for styles that should have power */
:is(.card) { border: 1px solid gray; }

/* ✅ :where() for true utilities/overrides */
:where(.border-none) { border: none; }
```

## Browser Fallback

```css
/* Progressive enhancement */
.card h2,
.card h3 {
  color: var(--heading);
}

.card :is(h2, h3) {
  /* Modern browsers use this (but doesn't increase specificity much) */
  color: var(--heading);
}
```

## One-Liner

`:is()` groups selectors while keeping the highest specificity of any argument — use it for cleaner components. `:where()` groups with zero specificity — use it for utility classes and resets that should never win specificity battles.

---
*Learning: 2026-02-20 | 15min sprint*

# CSS Pattern: Custom Properties for Theming

**Pattern:** CSS variables for dynamic, maintainable design systems

## The Core Concept

```css
:root {
  /* Semantic tokens */
  --color-primary: #0d6efd;
  --color-primary-hover: #0b5ed7;
  --color-text: #212529;
  --color-text-muted: #6c757d;
  --color-bg: #ffffff;
  --color-border: #dee2e6;
  
  /* Spacing scale */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 32px;
  
  /* Typography */
  --font-sans: system-ui, sans-serif;
  --font-mono: ui-monospace, monospace;
  --text-sm: 14px;
  --text-base: 16px;
  --text-lg: 18px;
  
  /* Radii */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
}
```

## Why Custom Properties Win

| CSS Preprocessor | CSS Custom Properties |
|------------------|----------------------|
| Compile-time only | Runtime dynamic |
| Can't change with JS | `element.style.setProperty()` |
| One theme per build | Multiple themes, one file |
| Sourcemap required | Native browser devtools |

## Dynamic Theme Switching

```css
/* Light (default) */
:root {
  --color-bg: #ffffff;
  --color-text: #212529;
  --color-border: #dee2e6;
}

/* Dark */
[data-theme="dark"] {
  --color-bg: #1a1a1a;
  --color-text: #e9ecef;
  --color-border: #495057;
}
```

```javascript
// Toggle theme
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
}

// On load
const saved = localStorage.getItem('theme') || 'light';
setTheme(saved);

// No page flash: set in <head> before body renders
```

## Component-Level Overrides

```css
.alert {
  --alert-bg: #fff3cd;
  --alert-border: #ffc107;
  --alert-text: #856404;
  
  background: var(--alert-bg);
  border: 1px solid var(--alert-border);
  color: var(--alert-text);
  padding: var(--space-3);
  border-radius: var(--radius-md);
}

.alert--error {
  --alert-bg: #f8d7da;
  --alert-border: #dc3545;
  --alert-text: #721c24;
}

.alert--success {
  --alert-bg: #d4edda;
  --alert-border: #28a745;
  --alert-text: #155724;
}
```

```html
<div class="alert">Warning message</div>
<div class="alert alert--error">Error message</div>
<div class="alert alert--success">Success message</div>
```

## Computed Values with calc()

```css
:root {
  --space-unit: 8px;
  --space-1: var(--space-unit);
  --space-2: calc(var(--space-unit) * 2);
  --space-3: calc(var(--space-unit) * 3);
  --space-4: calc(var(--space-unit) * 4);
  
  /* Derived colors */
  --color-primary-light: color-mix(in srgb, var(--color-primary) 20%, white);
  --color-primary-dark: color-mix(in srgb, var(--color-primary) 80%, black);
}
```

## JavaScript Integration

```javascript
// Get value
getComputedStyle(document.documentElement)
  .getPropertyValue('--color-primary'); // " #0d6efd"

// Set value
document.documentElement.style.setProperty('--color-primary', '#ff0000');

// Set on specific element (scoped)
const card = document.querySelector('.card');
card.style.setProperty('--card-bg', '#f0f0f0');
```

## Fallback Values

```css
.button {
  /* Uses --btn-bg if set, otherwise falls back to --color-primary */
  background: var(--btn-bg, var(--color-primary));
  
  /* Ultimate fallback */
  color: var(--btn-text, white);
}
```

## Scope Strategies

| Scope | Use Case |
|-------|----------|
| `:root` | Global theme tokens |
| `.component` | Component variants |
| `[data-theme]` | Dark/light modes |
| Inline style | One-off dynamic values |

## Browser Support

| Feature | Support |
|---------|---------|
| Basic custom properties | ~97% (all modern) |
| `color-mix()` | ~95% |
| `@property` (typed) | ~90% |

## Best Practices

1. **Name semantically** — `--color-error` not `--color-red`
2. **Two layers** — primitive tokens + semantic tokens
3. **Avoid deep nesting** — 2-3 levels max
4. **Document with `@property`** for type safety:

```css
@property --color-primary {
  syntax: '<color>';
  inherits: true;
  initial-value: #0d6efd;
}
```

5. **No massive variable lists** — Group by purpose

---
*Learned: 2026-02-20* | *Time: ~10 min*

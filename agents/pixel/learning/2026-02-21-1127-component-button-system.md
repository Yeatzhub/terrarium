# Component Design System: Button

Production-ready button architecture. Covers 6 variants, 5 states, 4 sizes, accessibility, and dark mode.

## Anatomy

```
┌─────────────────────────────┐
│  [icon]  Label  [icon]   │
└─────────────────────────────┘
   ↑padding↑    ↑gap↑
```

- Min touch target: 44×44px (iOS HIG)
- Min tap target: 48×48px (Material Design)
- Recommended: 40–48px height

## CSS Architecture

```css
/* Base */
.btn {
  --btn-bg: var(--color-primary, #0066ff);
  --btn-text: var(--color-on-primary, #ffffff);
  --btn-border: transparent;
  --btn-shadow: 0 1px 2px rgba(0,0,0,0.1);
  
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px 20px;
  min-height: 44px;
  border: 1px solid var(--btn-border);
  border-radius: 8px;
  background: var(--btn-bg);
  color: var(--btn-text);
  font-family: system-ui, sans-serif;
  font-weight: 500;
  font-size: 1rem;
  line-height: 1.5;
  cursor: pointer;
  transition: 
    background-color 0.2s ease,
    transform 0.1s ease,
    box-shadow 0.2s ease;
  box-shadow: var(--btn-shadow);
}

/* States */
.btn:hover:not(:disabled) {
  filter: brightness(1.1);
}

.btn:active:not(:disabled) {
  transform: scale(0.98);
}

.btn:focus-visible {
  outline: 2px solid var(--color-focus, #005fcc);
  outline-offset: 2px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  filter: grayscale(0.5);
}
```

## Variants

```css
/* Filled (default) */
.btn--filled {
  --btn-bg: var(--color-primary);
  --btn-text: var(--color-on-primary);
}

/* Outlined */
.btn--outlined {
  --btn-bg: transparent;
  --btn-text: var(--color-primary);
  --btn-border: currentColor;
}

/* Ghost (subtle) */
.btn--ghost {
  --btn-bg: transparent;
  --btn-text: var(--color-on-surface);
  --btn-border: transparent;
}
.btn--ghost:hover:not(:disabled) {
  --btn-bg: var(--color-surface-container);
}

/* Text (link style) */
.btn--text {
  --btn-bg: transparent;
  --btn-text: var(--color-primary);
  --btn-border: transparent;
  --btn-shadow: none;
  padding: 4px 8px;
  min-height: auto;
  text-decoration: underline;
  text-underline-offset: 2px;
}

/* Destructive */
.btn--destructive {
  --btn-bg: var(--color-error, #dc2626);
  --btn-text: var(--color-on-error, #ffffff);
}
.btn--destructive.btn--outlined {
  --btn-bg: transparent;
  --btn-text: var(--color-error);
}

/* Elevated */
.btn--elevated {
  --btn-shadow: 
    0 2px 4px rgba(0,0,0,0.1),
    0 8px 8px rgba(0,0,0,0.05);
}
```

## Sizes

```css
.btn--sm {
  padding: 6px 12px;
  min-height: 32px;
  font-size: 0.875rem;
  gap: 4px;
}

.btn--md {
  padding: 10px 20px;
  min-height: 44px;
  font-size: 1rem;
  gap: 8px;
}

.btn--lg {
  padding: 14px 28px;
  min-height: 56px;
  font-size: 1.125rem;
  gap: 12px;
}

.btn--icon {
  padding: 10px;
  aspect-ratio: 1;
}
```

## Complete HTML Example

```html
<!-- Filled -->
<button class="btn btn--filled">Save</button>

<!-- Outlined -->
<button class="btn btn--outlined">Cancel</button>

<!-- With icon -->
<button class="btn btn--filled">
  <svg class="btn__icon" aria-hidden="true">...upload icon...</svg>
  Upload File
</button>

<!-- Icon only -->
<button class="btn btn--filled btn--icon" aria-label="Close">
  <svg aria-hidden="true">...close icon...</svg>
</button>

<!-- Loading state -->
<button class="btn btn--filled" disabled>
  <span class="btn__spinner" aria-hidden="true">⏳</span>
  <span class="sr-only">Loading</span>
  Saving...
</button>

<!-- Button group -->
<div class="btn-group" role="group" aria-label="Actions">
  <button class="btn btn--outlined">Cancel</button>
  <button class="btn btn--filled">Submit</button>
</div>
```

## Supporting CSS

```css
/* Screen reader only */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Button group */
.btn-group {
  display: flex;
  gap: 12px;
}

/* Spinner animation */
.btn__spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

## Dark Mode

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-primary: #60a5fa;
    --color-on-primary: #ffffff;
    --color-surface-container: #2d2d2d;
    --color-on-surface: #e5e5e5;
    --color-error: #f87171;
    --color-on-error: #ffffff;
  }
  
  .btn {
    --btn-shadow: 0 1px 2px rgba(0,0,0,0.3);
  }
}
```

## Component Tokens (Design System)

```css
:root {
  /* Primary */
  --btn-primary-bg: var(--color-primary);
  --btn-primary-text: var(--color-on-primary);
  
  /* Secondary/Outlined */
  --btn-outlined-bg: transparent;
  --btn-outlined-text: var(--color-primary);
  --btn-outlined-border: var(--color-outline);
  
  /* Disabled */
  --btn-disabled-opacity: 0.5;
  
  /* Focus ring */
  --btn-focus-ring: 2px solid var(--color-focus);
  --btn-focus-offset: 2px;
  
  /* Animation */
  --btn-transition-duration: 0.2s;
  --btn-transition-easing: ease;
  
  /* Sizing */
  --btn-padding-x: 20px;
  --btn-padding-y: 10px;
  --btn-min-height: 44px;
  --btn-radius: 8px;
}
```

## Accessibility Checklist

| Requirement | Implementation |
|-------------|----------------|
| Keyboard focus | Native :focus-visible |
| Disabled state | `:disabled` + opacity |
| Loading state | `aria-busy="true"` + disabled |
| Icon-only | `aria-label` required |
| Color contrast | 4.5:1 minimum |
| Motion | Respect prefers-reduced-motion |

## Common Mistakes

| ❌ Bad | ✅ Good |
|--------|---------|
| `div role="button"` | Native `<button>` element |
| Custom focus rings | `:focus-visible` for keyboard only |
| `cursor: pointer` only | Real `:disabled` state |
| Margin inside button | Gap between icon/text |
| Fixed width | `min-width` + flexible content |

## React Component (Sketch)

```jsx
function Button({
  children,
  variant = 'filled',
  size = 'md',
  disabled = false,
  loading = false,
  iconLeft,
  iconRight,
  ...props
}) {
  const classes = [
    'btn',
    `btn--${variant}`,
    `btn--${size}`,
    loading && 'btn--loading',
  ].filter(Boolean).join(' ');
  
  return (
    <button
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading}
      {...props}
    >
      {loading && <Spinner />}
      {iconLeft && !loading && iconLeft}
      {children}
      {iconRight && iconRight}
    </button>
  );
}
```

---
*Learned: 2026-02-21 | 15-min sprint*

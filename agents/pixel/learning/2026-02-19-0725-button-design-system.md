# Button Component: Design System Anatomy

**Type:** Component specification

## Core Structure

```
Button
├── Base (shape, font, cursor)
├── Size (sm, md, lg)
├── Variant (primary, secondary, ghost, danger)
├── State (default, hover, active, disabled, loading)
└── Icon (left, right, only)
```

## Size Scale

| Name | Height | Padding | Font | Icon |
|------|--------|---------|------|------|
| sm | 32px | 12px 16px | 14px | 16px |
| md | 40px | 16px 24px | 16px | 20px |
| lg | 48px | 20px 32px | 18px | 24px |

## Variant Tokens (CSS Variables)

```css
:root {
  /* Primary */
  --btn-primary-bg: #0d6efd;
  --btn-primary-hover: #0b5ed7;
  --btn-primary-text: #fff;
  
  /* Secondary */
  --btn-secondary-bg: #6c757d;
  --btn-secondary-hover: #5c636a;
  --btn-secondary-text: #fff;
  
  /* Ghost */
  --btn-ghost-bg: transparent;
  --btn-ghost-hover: rgba(0,0,0,0.05);
  --btn-ghost-text: #212529;
  
  /* Danger */
  --btn-danger-bg: #dc3545;
  --btn-danger-hover: #bb2d3b;
  --btn-danger-text: #fff;
}
```

## State Behaviors

```css
.btn {
  position: relative;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  transition: all 150ms ease;
  cursor: pointer;
  
  /* Hover */
  &:hover:not(:disabled) {
    transform: translateY(-1px);
    filter: brightness(1.1);
  }
  
  /* Active */
  &:active:not(:disabled) {
    transform: translateY(0);
    filter: brightness(0.95);
  }
  
  /* Focus */
  &:focus-visible {
    outline: 2px solid var(--btn-primary-bg);
    outline-offset: 2px;
  }
  
  /* Disabled */
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}
```

## Loading State

```css
.btn--loading {
  color: transparent;
  pointer-events: none;
  
  &::after {
    content: "";
    position: absolute;
    width: 1em;
    height: 1em;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
```

## Accessibility Checklist

- [ ] `cursor: pointer` on hover
- [ ] Focus visible styles
- [ ] `aria-busy="true"` when loading
- [ ] Disabled state prevents click + has `aria-disabled="true"`
- [ ] Icon-only buttons have `aria-label`
- [ ] 44px minimum touch target on mobile
- [ ] Color contrast ≥ 4.5:1

## Common Anti-Patterns to Avoid

| ❌ Bad | ✅ Good |
|--------|---------|
| `cursor: default` on button | `cursor: pointer` |
| Disabled without visual dimming | Clear opacity change |
| Breaking layout on loading | Reserve space for spinner |
| Inconsistent border-radius | Token-based radius |
| Hardcoded colors | CSS variable tokens |

## Implementation Example

```html
<button class="btn btn--primary btn--md" type="button">
  Save Changes
</button>

<button class="btn btn--ghost btn--sm" disabled>
  Cancel
</button>

<button class="btn btn--primary btn--md btn--loading" aria-busy="true">
  Saving...
</button>
```

---
*Learned: 2026-02-19* | *Time: ~12 min* | *Reference: WCAG 2.1 + Material Design + Carbon Design System*

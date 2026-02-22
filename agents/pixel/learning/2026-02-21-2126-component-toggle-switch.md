# Component Design System: Toggle Switch

Accessible, animated toggle switches without JS. Pure CSS with checkbox input foundation. Covers 4 sizes, 8 variants, keyboard control.

## Anatomy

```
┌─────────────────────────────────────┐
│ Label text              ╔═══╗       │
│ Description text        ║ ● ║       │ ← Track + Thumb
│                         ╚═══╝       │
└─────────────────────────────────────┘
```

## Core Structure

```html
<label class="toggle" for="airplane-mode">
  <span class="toggle__label">Airplane Mode</span>
  <span class="toggle__description">Disable all wireless connections</span>
  
  <span class="toggle__control">
    <input
      type="checkbox"
      id="airplane-mode"
      class="toggle__input"
      role="switch"
      aria-checked="false"
    />
    <span class="toggle__track" aria-hidden="true">
      <span class="toggle__thumb"></span>
    </span>
  </span>
</label>
```

## Complete CSS

```css
/* Root container */
.toggle {
  --toggle-width: 48px;
  --toggle-height: 28px;
  --toggle-padding: 4px;
  --toggle-thumb: calc(var(--toggle-height) - (var(--toggle-padding) * 2));
  --toggle-duration: 0.2s;
  
  --toggle-track-off: #e5e5e5;
  --toggle-track-on: #10b981;
  --toggle-thumb-bg: white;
  --toggle-focus: #005fcc;
  
  display: grid;
  grid-template-columns: 1fr auto;
  grid-template-rows: auto auto;
  gap: 4px 16px;
  align-items: center;
  cursor: pointer;
  padding: 12px 0;
  user-select: none;
}

/* Label text */
.toggle__label {
  grid-column: 1;
  grid-row: 1;
  font-weight: 500;
  font-size: 1rem;
  color: #111;
}

/* Description text */
.toggle__description {
  grid-column: 1;
  grid-row: 2;
  font-size: 0.875rem;
  color: #666;
}

/* Control wrapper */
.toggle__control {
  grid-column: 2;
  grid-row: 1 / 3;
  position: relative;
}

/* Native checkbox - visually hidden but accessible */
.toggle__input {
  position: absolute;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  z-index: 1;
  margin: 0;
}

/* Visual track */
.toggle__track {
  display: block;
  width: var(--toggle-width);
  height: var(--toggle-height);
  background: var(--toggle-track-off);
  border-radius: 9999px;
  position: relative;
  transition: background var(--toggle-duration) ease;
}

/* Visual thumb */
.toggle__thumb {
  display: block;
  width: var(--toggle-thumb);
  height: var(--toggle-thumb);
  background: var(--toggle-thumb-bg);
  border-radius: 50%;
  position: absolute;
  top: var(--toggle-padding);
  left: var(--toggle-padding);
  transition: transform var(--toggle-duration) cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

/* Checked state */
.toggle__input:checked + .toggle__track {
  background: var(--toggle-track-on);
}

.toggle__input:checked + .toggle__track .toggle__thumb {
  transform: translateX(calc(var(--toggle-width) - var(--toggle-height)));
}

/* Focus state */
.toggle__input:focus-visible + .toggle__track {
  outline: 2px solid var(--toggle-focus);
  outline-offset: 2px;
}

/* Disabled state */
.toggle__input:disabled {
  cursor: not-allowed;
}

.toggle__input:disabled + .toggle__track {
  opacity: 0.5;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .toggle__track,
  .toggle__thumb {
    transition: none;
  }
}
```

## Sizes

```css
/* Small - Compact UI */
.toggle--sm {
  --toggle-width: 36px;
  --toggle-height: 20px;
  --toggle-padding: 2px;
}

/* Medium (default) */
.toggle--md {
  --toggle-width: 48px;
  --toggle-height: 28px;
  --toggle-padding: 4px;
}

/* Large - Touch friendly */
.toggle--lg {
  --toggle-width: 60px;
  --toggle-height: 36px;
  --toggle-padding: 4px;
}

/* Extra Large - Accessibility */
.toggle--xl {
  --toggle-width: 72px;
  --toggle-height: 44px;
  --toggle-padding: 4px;
}
```

## Variants

```css
/* Default (Green) */
.toggle { --toggle-track-on: #10b981; }

/* Primary (Blue) */
.toggle--primary { --toggle-track-on: #3b82f6; }

/* Danger (Red) */
.toggle--danger { --toggle-track-on: #ef4444; }

/* Warning (Orange) */
.toggle--warning { --toggle-track-on: #f97316; }

/* Purple */
.toggle--purple { --toggle-track-on: #8b5cf6; }

/* Pink */
.toggle--pink { --toggle-track-on: #ec4899; }

/* Dark mode support */
@media (prefers-color-scheme: dark) {
  .toggle {
    --toggle-track-off: #3a3a3a;
    --toggle-track-on: #34d399;
    --toggle-thumb-bg: #2d2d2d;
  }
  .toggle__label { color: #e5e5e5; }
  .toggle__description { color: #999; }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .toggle__track {
    border: 2px solid currentColor;
  }
  .toggle__input:checked + .toggle__track {
    border-color: var(--toggle-track-on);
  }
}
```

## With Icons

```css
.toggle__thumb::before {
  content: "";
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

/* Unchecked - X icon */
.toggle__input:not(:checked) + .toggle__track .toggle__thumb::before {
  content: "✕";
  color: #999;
}

/* Checked - Check icon */
.toggle__input:checked + .toggle__track .toggle__thumb::before {
  content: "✓";
  color: var(--toggle-track-on);
}
```

## Labeled Positions

```html
<!-- Label on left (default) -->
<label class="toggle">
  <span class="toggle__label">Notifications</span>
  <span class="toggle__control">...</span>
</label>

<!-- Label on right -->
<label class="toggle toggle--label-right">
  <span class="toggle__control">...</span>
  <span class="toggle__label">Dark Mode</span>
</label>
```

```css
.toggle--label-right {
  grid-template-columns: auto 1fr;
}

.toggle--label-right .toggle__control {
  grid-column: 1;
}

.toggle--label-right .toggle__label {
  grid-column: 2;
}
```

## Group / List Pattern

```html
<fieldset class="toggle-group">
  <legend class="toggle-group__legend">Settings</legend>
  
  <label class="toggle toggle--bordered">...</label>
  <label class="toggle toggle--bordered">...</label>
  <label class="toggle toggle--bordered">...</label>
</fieldset>
```

```css
.toggle-group {
  border: none;
  padding: 0;
  margin: 0;
}

.toggle-group__legend {
  font-weight: 600;
  margin-bottom: 12px;
  padding: 0;
}

.toggle--bordered {
  border-bottom: 1px solid #e5e5e5;
  padding: 16px;
  margin: 0 -16px;
}

.toggle--bordered:last-child {
  border-bottom: none;
}
```

## JavaScript Enhancement

```javascript
// Optional: Update aria-checked for older AT
class ToggleSwitch {
  constructor(element) {
    this.element = element;
    this.input = element.querySelector('.toggle__input');
    
    this.input.addEventListener('change', () => {
      this.input.setAttribute('aria-checked', this.input.checked);
      this.element.dispatchEvent(new CustomEvent('toggle', {
        detail: { checked: this.input.checked }
      }));
    });
  }
  
  get checked() { return this.input.checked; }
  set checked(value) { 
    this.input.checked = value;
    this.input.setAttribute('aria-checked', value);
  }
  
  toggle() {
    this.checked = !this.checked;
    return this.checked;
  }
}

// Usage
const toggle = new ToggleSwitch(document.querySelector('.toggle'));
toggle.addEventListener('toggle', e => {
  console.log('Toggled:', e.detail.checked);
});
```

## Touch Targets

```css
/* Ensure minimum 44px touch target */
@media (pointer: coarse) {
  .toggle {
    padding: 8px 0; /* Extra vertical space */
  }
  
  .toggle__control::after {
    content: '';
    position: absolute;
    inset: -12px;
    z-index: 0;
  }
}
```

## Common Mistakes

| ❌ Bad | ✅ Good |
|--------|---------|
| `div` with click handler | Native checkbox, label wrapped |
| Custom `:focus` styles | Use `:focus-visible` |
| Positioning thumb with `left` | Use `translateX` for GPU |
| `transition: all` | Specific properties only |
| No `role="switch"` | Include for screen readers |

## Accessibility Checklist

| Requirement | Implementation |
|-------------|----------------|
| Keyboard | Native checkbox (Tab/Space) |
| Screen reader | `role="switch"` + `aria-checked` |
| Focus visible | `:focus-visible` outline |
| Reduced motion | Disable animation |
| High contrast | Border added |
| Touch target | 44px minimum |

---
*Learned: 2026-02-21 | 15-min sprint*

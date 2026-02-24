# Toggle Switch Component

A reusable, accessible toggle switch for design systems.

## HTML Structure

```html
<label class="toggle">
  <input type="checkbox" class="toggle__input" aria-describedby="toggle-hint">
  <span class="toggle__track">
    <span class="toggle__thumb"></span>
  </span>
  <span class="toggle__label">Enable notifications</span>
</label>
<span id="toggle-hint" class="toggle__hint">Receive alerts for new messages</span>
```

## CSS (CSS-First, No JS Required)

```css
.toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
}

.toggle__input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle__track {
  position: relative;
  width: 44px;
  height: 24px;
  background: var(--color-neutral-300);
  border-radius: 999px;
  transition: background 150ms ease;
}

.toggle__thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 150ms ease;
}

/* Checked state */
.toggle__input:checked + .toggle__track {
  background: var(--color-primary);
}

.toggle__input:checked + .toggle__track .toggle__thumb {
  transform: translateX(20px);
}

/* Focus state */
.toggle__input:focus-visible + .toggle__track {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Disabled state */
.toggle__input:disabled + .toggle__track {
  opacity: 0.5;
  cursor: not-allowed;
}
```

## Design Tokens

```css
:root {
  --toggle-size-sm: 36px / 20px;  /* track / thumb */
  --toggle-size-md: 44px / 24px;  /* default */
  --toggle-size-lg: 52px / 28px;
  
  --toggle-transition: 150ms ease;
  --toggle-track-radius: 999px;
}
```

## Accessibility Checklist

- ✅ Native `<input type="checkbox">` — keyboard accessible by default
- ✅ Focus-visible styling (not just focus)
- ✅ `aria-describedby` for hint text
- ✅ Label text is always visible (not hidden in the switch)
- ✅ Disabled state visual + cursor

## States Summary

| State | Visual |
|-------|--------|
| Default | Gray track, thumb left |
| Checked | Primary color track, thumb right |
| Focus | Ring outline |
| Disabled | 50% opacity |
| Hover | Slightly darker track |
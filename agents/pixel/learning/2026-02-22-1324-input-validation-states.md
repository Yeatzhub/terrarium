# Input Field with Validation States — Component

A form input with clear, accessible validation feedback.

## HTML Structure

```html
<div class="field">
  <label class="field__label" for="email">
    Email address
    <span class="field__required" aria-hidden="true">*</span>
  </label>
  <div class="field__input-wrapper">
    <input 
      type="email" 
      id="email" 
      class="field__input"
      aria-describedby="email-error email-hint"
      aria-required="true"
    >
    <span class="field__icon" aria-hidden="true"></span>
  </div>
  <span class="field__hint" id="email-hint">We'll never share your email</span>
  <span class="field__error" id="email-error" role="alert">
    Please enter a valid email address
  </span>
</div>
```

## CSS (All States)

```css
.field {
  --field-border: var(--color-neutral-300);
  --field-bg: var(--color-surface);
  --field-text: var(--color-text);
  --field-radius: 8px;
  --field-height: 48px;
  
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.field__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--field-text);
}

.field__required {
  color: var(--color-error);
  margin-left: 0.25rem;
}

.field__input-wrapper {
  position: relative;
}

.field__input {
  width: 100%;
  height: var(--field-height);
  padding: 0 1rem;
  background: var(--field-bg);
  border: 1.5px solid var(--field-border);
  border-radius: var(--field-radius);
  font-size: 1rem;
  transition: border-color 150ms, box-shadow 150ms;
}

/* Focus state */
.field__input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-alpha);
}

/* Error state */
.field--error {
  --field-border: var(--color-error);
}

.field--error .field__input {
  padding-right: 2.75rem; /* Space for icon */
}

.field--error .field__icon::after {
  content: "⚠️"; /* Or SVG */
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
}

/* Success state */
.field--success {
  --field-border: var(--color-success);
}

.field--success .field__icon::after {
  content: "✓";
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-success);
}

/* Disabled state */
.field__input:disabled {
  background: var(--color-neutral-100);
  cursor: not-allowed;
  opacity: 0.6;
}

.field__hint {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.field__error {
  font-size: 0.75rem;
  color: var(--color-error);
  display: none;
}

.field--error .field__error {
  display: block;
}
```

## State Summary

| State | Border | Icon | Message |
|-------|--------|------|---------|
| Default | Gray | — | Hint (optional) |
| Focus | Primary + ring | — | Hint |
| Error | Red | ⚠️ | Error message |
| Success | Green | ✓ | Hint |
| Disabled | Gray | — | Hint |

## Accessibility Checklist

- ✅ `<label>` with `for` attribute matching input `id`
- ✅ `aria-required="true"` for required fields
- ✅ `aria-describedby` links hint and error
- ✅ `role="alert"` on error (announces to screen readers)
- ✅ Error shown via class, not hidden content
- ✅ Focus ring visible (not just color change)

## Design Tokens

```css
:root {
  --field-height-sm: 40px;
  --field-height-md: 48px;
  --field-height-lg: 56px;
  
  --field-radius-sm: 6px;
  --field-radius-md: 8px;
  --field-radius-lg: 12px;
  
  --field-border-default: var(--neutral-300);
  --field-border-focus: var(--primary-500);
  --field-border-error: var(--error-500);
  --field-border-success: var(--success-500);
}
```

## Pro Tip

Always validate on blur, not on input. Validating while typing feels nagging. Validate on blur, re-validate on submit.
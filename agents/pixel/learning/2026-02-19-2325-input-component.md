# Component: Input Field Anatomy

**Type:** Form component specification

## Core Structure

```
Input Field
├── Label (always visible)
├── Input Container (border, focus ring)
│   ├── Prefix (optional: icon, $, +)
│   ├── Input Element
│   └── Suffix (optional: icon, unit, clear)
├── Helper Text (hint or error)
└── Character Count (optional)
```

## CSS Foundation

```css
/* Base tokens */
:root {
  --input-bg: #ffffff;
  --input-border: #dee2e6;
  --input-border-hover: #adb5bd;
  --input-border-focus: #0d6efd;
  --input-border-error: #dc3545;
  --input-text: #212529;
  --input-placeholder: #6c757d;
  --input-radius: 6px;
  --input-padding: 12px 16px;
  --input-height: 44px;
  --input-font: 16px/1.5 system-ui;
}

/* Input wrapper */
.input-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.input-field__label {
  font-size: 14px;
  font-weight: 500;
  color: #495057;
}

/* The input container */
.input-field__container {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 12px;
  height: var(--input-height);
  background: var(--input-bg);
  border: 2px solid var(--input-border);
  border-radius: var(--input-radius);
  transition: border-color 0.15s, box-shadow 0.15s;
}

.input-field__container:hover {
  border-color: var(--input-border-hover);
}

.input-field__container:focus-within {
  border-color: var(--input-border-focus);
  box-shadow: 0 0 0 3px rgba(13, 110, 253, 0.15);
}

/* The actual input */
.input-field__input {
  flex: 1;
  border: none;
  background: transparent;
  font: var(--input-font);
  color: var(--input-text);
  outline: none;
  padding: 0;
}

.input-field__input::placeholder {
  color: var(--input-placeholder);
}

/* Prefix/suffix */
.input-field__prefix,
.input-field__suffix {
  color: #6c757d;
  font-size: 16px;
  flex-shrink: 0;
}
```

## States

### Error State

```css
.input-field--error .input-field__container {
  border-color: var(--input-border-error);
  background: #fff5f5;
}

.input-field--error .input-field__container:focus-within {
  box-shadow: 0 0 0 3px rgba(220, 53, 69, 0.15);
}

.input-field__error {
  font-size: 14px;
  color: var(--input-border-error);
  display: flex;
  align-items: center;
  gap: 6px;
}
```

### Disabled State

```css
.input-field--disabled .input-field__container {
  background: #e9ecef;
  border-color: #dee2e6;
  cursor: not-allowed;
  opacity: 0.6;
}

.input-field--disabled .input-field__input {
  cursor: not-allowed;
}
```

### Read-only State

```css
.input-field--readonly .input-field__container {
  background: #f8f9fa;
  border-color: #e9ecef;
}
```

## HTML Structure

```html
<div class="input-field input-field--error">
  <label class="input-field__label" for="email">
    Email Address
  </label>
  <div class="input-field__container">
    <span class="input-field__prefix" aria-hidden="true">
      ✉️
    </span>
    <input 
      type="email"
      id="email"
      class="input-field__input"
      placeholder="you@example.com"
      aria-invalid="true"
      aria-describedby="email-error"
      autocomplete="email"
    />
  </div>
  <span class="input-field__error" id="email-error">
    <svg aria-hidden="true" width="16" height="16">...</svg>
    Please enter a valid email
  </span>
</div>
```

## Accessibility Checklist

| Requirement | Implementation |
|-------------|----------------|
| Label association | `for` matches `id` |
| Error announcement | `aria-invalid` + `aria-describedby` |
| Focus visible | Clear ring, not just border color |
| Placeholder vs label | Placeholder hints, label describes |
| Autocomplete | `autocomplete` attribute for password managers |
| Touch target | 44px minimum height |
| Color contrast | 4.5:1 for text, 3:1 for borders |

## Variants

### With Clear Button

```css
.input-field__clear {
  opacity: 0;
  transition: opacity 0.15s;
}

.input-field__container:hover .input-field__clear,
.input-field__input:not(:placeholder-shown) ~ .input-field__clear {
  opacity: 1;
}
```

### Textarea Adaptation

```css
.input-field__container--textarea {
  height: auto;
  min-height: 100px;
  padding: 12px;
}

.input-field__container--textarea .input-field__input {
  min-height: 80px;
  resize: vertical;
}
```

### Compact Size

```css
.input-field--sm .input-field__container {
  height: 36px;
  padding: 0 10px;
}

.input-field--sm .input-field__input {
  font-size: 14px;
}
```

## Validation UX

```javascript
// Real-time validation (after first blur)
input.addEventListener('blur', validate);

// Clear error on input
input.addEventListener('input', () => {
  input.classList.remove('input-field--error');
  input.removeAttribute('aria-invalid');
});

// Show error
function showError(input, message) {
  input.closest('.input-field').classList.add('input-field--error');
  input.setAttribute('aria-invalid', 'true');
  document.getElementById(input.getAttribute('aria-describedby'))
    .textContent = message;
}
```

## Common Anti-Patterns

| ❌ Avoid | ✅ Do |
|----------|-------|
| Placeholder as label | Visible label always |
| Red text only for error | Border + icon + text |
| Error on every keystroke | Validate on blur, clear on input |
| Disabled via HTML attr | Use class + aria-disabled |
| Small tap targets | 44px minimum |
| Floating labels only | Static label + floating as bonus |

---
*Learned: 2026-02-19* | *Time: ~12 min*

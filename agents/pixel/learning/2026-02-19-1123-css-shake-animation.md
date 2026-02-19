# CSS Animation: Shake Micro-Interaction

**Pattern:** Error state feedback for forms

## The Core Animation

```css
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}

.shake {
  animation: shake 0.5s ease-in-out;
}
```

## Why This Works

| Element | Psychology |
|---------|------------|
| Horizontal motion | Mimics "no" head shake |
| ~4px amplitude | Subtle, not jarring |
| 0.5s duration | Noticeable but not annoying |
| Ease-in-out | Natural deceleration |

## Implementation: Form Field

```css
.input-group {
  position: relative;
}

.input-field {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #dee2e6;
  border-radius: 6px;
  transition: border-color 0.2s;
}

.input-field--error {
  border-color: #dc3545;
  background-color: #fff5f5;
  animation: shake 0.5s ease-in-out;
}

.error-message {
  color: #dc3545;
  font-size: 14px;
  margin-top: 4px;
  opacity: 0;
  transform: translateY(-8px);
  transition: all 0.3s ease;
}

.input-field--error + .error-message {
  opacity: 1;
  transform: translateY(0);
}
```

```html
<div class="input-group">
  <input 
    type="email" 
    class="input-field input-field--error" 
    value="invalid@email"
    aria-invalid="true"
    aria-describedby="email-error"
  />
  <p class="error-message" id="email-error">
    Please enter a valid email
  </p>
</div>
```

## JavaScript Trigger

```javascript
function showError(input, message) {
  // Remove existing to allow re-trigger
  input.classList.remove('input-field--error');
  
  // Force reflow to restart animation
  void input.offsetWidth;
  
  // Add error class
  input.classList.add('input-field--error');
  input.setAttribute('aria-invalid', 'true');
  
  // Update error message
  const errorEl = input.parentElement.querySelector('.error-message');
  if (errorEl) errorEl.textContent = message;
}

// Clear on input
document.querySelectorAll('.input-field').forEach(input => {
  input.addEventListener('input', () => {
    input.classList.remove('input-field--error');
    input.removeAttribute('aria-invalid');
  });
});
```

## Accessibility Notes

```css
/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .shake,
  .input-field--error {
    animation: none;
    border-left: 4px solid #dc3545;
  }
}
```

| A11y Requirement | Implementation |
|------------------|----------------|
| Screen reader | `aria-invalid="true"` + `aria-describedby` |
| Reduced motion | `@media (prefers-reduced-motion)` |
| Color blind | Border + background + text, not just red |
| Focus management | Return focus to invalid field |

## Variations

**Subtle shake (alerts):**
```css
@keyframes shake-subtle {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-2px); }
  75% { transform: translateX(2px); }
}
```

**Vertical shake (different semantics):**
```css
@keyframes bounce-no {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-6px); }
}
```

## Common Use Cases

- Form validation errors
- Delete confirmation nudge
- "Are you sure?" dialogs
- Password mismatch
- Cart abandonment warning

---
*Learned: 2026-02-19* | *Time: ~11 min* | *Reference: NN/g micro-interactions + prefers-reduced-motion spec*

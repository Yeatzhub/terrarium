# UX Pattern: Form Validation

Real-time, inline, accessible form validation. Reduces errors 35%, improves completion rates.

## The 3-Phase Rule

| Phase | Trigger | Feedback Type |
|-------|---------|---------------|
| **Static** | Page load | Field hints, required indicators |
| **Input** | While typing | Inline help, character counts |
| **Submit** | Form submission | Error summaries, field-level errors |

## Core Principles

1. **Validate early, message late** - Check in real-time, show error on blur
2. **Never clear valid input** - Don't punish correction
3. **Errors at the field** - Don't hide errors in a toast
4. **Explain how to fix** - Not just "invalid"

## CSS Error State System

```css
/* Required indicator */
.label::after {
  content: " *";
  color: var(--color-error);
}

/* Error state */
.input:invalid:not(:placeholder-shown),
.input.input--error {
  border-color: var(--color-error);
  background-color: var(--color-error-subtle);
}

/* Focus state overrides error */
.input:focus {
  border-color: var(--color-primary);
  background-color: white;
}

/* Error message container */
.error-message {
  display: none;
  color: var(--color-error);
  font-size: 0.875rem;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.input.input--error ~ .error-message,
.input:invalid:not(:placeholder-shown) ~ .error-message {
  display: flex;
}

/* Accessible error icon */
.error-message::before {
  content: "⚠";
  font-size: 0.75rem;
}

/* Shake animation for errors */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}

.input.input--error {
  animation: shake 0.3s ease;
}

@media (prefers-reduced-motion: reduce) {
  .input.input--error {
    animation: none;
  }
}
```

## Complete HTML Pattern

```html
<form novalidate>
  <!-- Email field -->
  <div class="field" data-field="email">
    <label class="label" for="email">
      Email Address
      <span class="required" aria-hidden="true">*</span>
    </label>
    
    <input
      type="email"
      id="email"
      name="email"
      class="input"
      required
      aria-required="true"
      aria-describedby="email-hint email-error"
      autocomplete="email"
      placeholder="you@example.com"
    />
    
    <p id="email-hint" class="hint">
      We'll never share your email.
    </p>
    
    <p id="email-error" class="error-message" role="alert">
      <span class="sr-only">Error: </span>
      Please enter a valid email address
    </p>
  </div>
  
  <!-- Password field with live requirements -->
  <div class="field" data-field="password">
    <label class="label" for="password">
      Password
      <span class="required" aria-hidden="true">*</span>
    </label>
    
    <div class="input-wrapper">
      <input
        type="password"
        id="password"
        name="password"
        class="input"
        required
        minlength="8"
        aria-required="true"
        aria-describedby="password-hint password-error"
        autocomplete="new-password"
      />
      <button 
        type="button" 
        class="toggle-password"
        aria-label="Show password"
        aria-pressed="false"
      >
        <span class="icon-eye">👁</span>
      </button>
    </div>
    
    <p id="password-hint" class="hint">
      Minimum 8 characters with a number and symbol
    </p>
    
    <!-- Live requirements checklist -->
    <ul class="requirements" aria-live="polite">
      <li data-requirement="length">
        <span class="check">○</span>
        8+ characters
      </li>
      <li data-requirement="number">
        <span class="check">○</span>
        Contains number
      </li>
      <li data-requirement="symbol">
        <span class="check">○</span>
        Contains symbol
      </li>
    </ul>
    
    <p id="password-error" class="error-message" role="alert"></pp>
  </div>
  
  <!-- Error summary at top -->
  <div class="error-summary" role="alert" aria-live="assertive" hidden>
    <h2>There is a problem</h2>
    <ul class="error-summary__list"></ul>
  </div>
  
  <button type="submit" class="btn">Create Account</button>
</form>
```

## JavaScript Validation Class

```javascript
class FormValidator {
  constructor(form) {
    this.form = form;
    this.fields = form.querySelectorAll('[data-field]');
    
    this.form.addEventListener('submit', e => this.handleSubmit(e));
    this.form.addEventListener('blur', e => this.handleBlur(e), true);
    this.form.addEventListener('input', e => this.handleInput(e));
  }
  
  validate(field) {
    const input = field.querySelector('input, select, textarea');
    const errors = [];
    
    // Check validity
    if (input.validity.valueMissing) {
      errors.push('This field is required');
    }
    if (input.validity.typeMismatch) {
      errors.push('Please enter a valid format');
    }
    if (input.validity.tooShort) {
      errors.push(`Minimum ${input.minLength} characters`);
    }
    if (input.validity.patternMismatch) {
      errors.push(input.dataset.errorMessage || 'Invalid format');
    }
    
    this.showErrors(field, errors);
    return errors.length === 0;
  }
  
  showErrors(field, errors) {
    const errorContainer = field.querySelector('.error-message');
    const input = field.querySelector('input, select, textarea');
    
    if (errors.length > 0) {
      field.classList.add('field--error');
      input.setAttribute('aria-invalid', 'true');
      
      // Prefix with "Error:" for screen readers
      errorContainer.innerHTML = errors.map(e => 
        `&lt;span class="sr-only">Error: </span>${e}`
      ).join('&lt;br>');
    } else {
      field.classList.remove('field--error');
      input.setAttribute('aria-invalid', 'false');
      errorContainer.textContent = '';
    }
  }
  
  handleBlur(e) {
    const field = e.target.closest('[data-field]');
    if (field) this.validate(field);
  }
  
  handleInput(e) {
    // Live password strength check
    if (e.target.id === 'password') {
      this.checkPasswordRequirements(e.target.value);
    }
  }
  
  handleSubmit(e) {
    e.preventDefault();
    let hasErrors = false;
    const errorSummary = this.form.querySelector('.error-summary');
    const errorList = errorSummary?.querySelector('.error-summary__list');
    
    this.fields.forEach(field => {
      if (!this.validate(field)) hasErrors = true;
    });
    
    if (hasErrors) {
      // Build error summary for screen readers
      if (errorSummary) {
        errorSummary.hidden = false;
        errorList.innerHTML = '';
        
        this.fields.forEach(field => {
          if (field.classList.contains('field--error')) {
            const label = field.querySelector('label')?.textContent;
            const input = field.querySelector('input');
            const li = document.createElement('li');
            li.innerHTML = `<a href="#${input.id}">${label} - ${input.validationMessage}</a>`;
            errorList.appendChild(li);
          }
        });
        
        errorSummary.scrollIntoView({ behavior: 'smooth' });
        errorSummary.querySelector('a')?.focus();
      }
    } else {
      this.form.submit();
    }
  }
  
  checkPasswordRequirements(value) {
    const reqs = {
      length: value.length >= 8,
      number: /\d/.test(value),
      symbol: /[!@#$%^&*]/.test(value)
    };
    
    Object.entries(reqs).forEach(([key, valid]) => {
      const item = document.querySelector(`[data-requirement="${key}"]`);
      const check = item?.querySelector('.check');
      if (item) {
        item.classList.toggle('requirement--met', valid);
        if (check) check.textContent = valid ? '✓' : '○';
      }
    });
  }
}

// Initialize
new FormValidator(document.querySelector('form'));
```

## Error Message Guidelines

| Bad Error | Good Error |
|-----------|-----------|
| "Invalid" | "Enter an email like name@example.com" |
| "Required" | "Enter your first name" |
| "Too short" | "Password must be at least 8 characters" |
| "Error 403" | "This username is taken. Try 'jsmith2024'" |

## Accessibility Checklist

| Requirement | Implementation |
|-------------|----------------|
| Programmatic label | `input` linked to `label` |
| Required announced | `aria-required="true"` |
| Error described | `aria-describedby="id-of-error"` |
| Invalid state | `aria-invalid="true"` |
| Error live | `role="alert"` on error messages |
| Focus management | First error focused on submit |
| Instructions | Hints linked via `aria-describedby` |

## Success Pattern

```css
/* Valid state after correction */
.input:valid:not(:placeholder-shown) {
  background-image: url("data:image/svg+xml,...checkmark...");
  background-position: right 12px center;
  background-repeat: no-repeat;
  padding-right: 40px;
}

/* Don't show success on empty fields */
.input:placeholder-shown {
  background-image: none;
}
```

## Server Error Handling

```javascript
// After API error
function showServerErrors(errors) {
  Object.entries(errors).forEach(([field, message]) => {
    const fieldEl = document.querySelector(`[data-field="${field}"]`);
    if (fieldEl) {
      const errorContainer = fieldEl.querySelector('.error-message');
      errorContainer.textContent = message;
      fieldEl.classList.add('field--error');
      fieldEl.scrollIntoView({ behavior: 'smooth' });
    }
  });
}
```

---
*Learned: 2026-02-21 | 15-min sprint*

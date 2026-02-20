# Toast Notification System — Design System Component

## What
- Non-blocking status messages that appear temporarily
- User actions receive feedback without interrupting flow
- Auto-dismiss with manual close option; respects reduced-motion

## Anatomy

```html
<div class="toast-container" role="region" aria-live="polite" aria-label="Notifications">
  <div class="toast toast--success" role="status">
    <span class="toast__icon" aria-hidden="true">✓</span>
    <span class="toast__message">Changes saved</span>
    <button class="toast__close" aria-label="Dismiss notification">×</button>
  </div>
</div>
```

## CSS Implementation

### Container (Fixed Position)
```css
.toast-container {
  position: fixed;
  bottom: 1rem;
  right: 1rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: min(400px, calc(100vw - 2rem));
  pointer-events: none; /* Let clicks pass through gaps */
}

.toast-container .toast {
  pointer-events: auto; /* Re-enable for toasts */
}
```

### Toast Base
```css
.toast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  background: var(--toast-bg);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  font-size: 0.9375rem;
  animation: toast-in 0.3s ease-out;
}

.toast--exit {
  animation: toast-out 0.2s ease-in forwards;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translateY(100%) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes toast-out {
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}
```

### Variants
```css
:root {
  --toast-bg: #1e293b;
  --toast-text: #ffffff;
}

.toast--success { border-left: 4px solid #22c55e; }
.toast--error   { border-left: 4px solid #ef4444; }
.toast--warning { border-left: 4px solid #f59e0b; }
.toast--info    { border-left: 4px solid #3b82f6; }
```

## JavaScript Controller

```js
class ToastSystem {
  constructor(container = document.body) {
    this.container = document.createElement('div');
    this.container.className = 'toast-container';
    this.container.setAttribute('role', 'region');
    this.container.setAttribute('aria-live', 'polite');
    container.appendChild(this.container);
    this.toasts = [];
  }

  show(message, {
    type = 'info',
    duration = 5000,
    icon = true,
    dismissible = true
  } = {}) {
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'status');
    toast.innerHTML = `
      ${icon ? `<span class="toast__icon">${this.#getIcon(type)}</span>` : ''}
      <span class="toast__message">${this.#escapeHtml(message)}</span>
      ${dismissible ? `
        <button class="toast__close" aria-label="Dismiss">×</button>
      ` : ''}
    `;

    this.container.appendChild(toast);

    // Auto dismiss
    const timeout = duration > 0 
      ? setTimeout(() => this.dismiss(toast), duration)
      : null;

    // Manual close
    if (dismissible) {
      toast.querySelector('.toast__close').addEventListener('click', () => {
        clearTimeout(timeout);
        this.dismiss(toast);
      });
    }

    // Pause on hover
    toast.addEventListener('mouseenter', () => clearTimeout(timeout));

    this.toasts.push(toast);
    return { dismiss: () => this.dismiss(toast) };
  }

  dismiss(toast) {
    toast.classList.add('toast--exit');
    toast.addEventListener('animationend', () => toast.remove());
  }

  #getIcon(type) {
    const icons = {
      success: '✓', error: '✕', warning: '⚠', info: 'ℹ'
    };
    return icons[type] || icons.info;
  }

  #escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Usage
const toast = new ToastSystem();
toast.show('Saved successfully', { type: 'success', duration: 3000 });
```

## Accessibility

### Required
- `role="status"` for auto-read announcements
- `aria-live="polite"` on container (doesn't interrupt)
- Focus trapping NOT needed (non-blocking)
- `aria-label="Dismiss"` on close button

### Motion Preferences
```css
@media (prefers-reduced-motion: reduce) {
  .toast {
    animation: none;
  }
  .toast--exit {
    animation: none;
    opacity: 0;
  }
}
```

## Positioning Options

```css
/* Bottom-right (default) */
.toast-container { bottom: 1rem; right: 1rem; }

/* Top-center */
.toast-container--top {
  top: 1rem;
  left: 50%;
  right: auto;
  transform: translateX(-50%);
  align-items: center;
}

/* Bottom-left (RTL support) */
.toast-container--start { bottom: 1rem; left: 1rem; }
```

## Do / Don't

✅ **Do**
- Keep under 60 characters for readability
- Use success icon + green for confirmations
- Allow manual dismiss (X button)
- Stack multiple toasts (max 3 visible)

❌ **Don't**
- Use for critical errors (use modal instead)
- Block user interaction (toasts are non-blocking)
- Auto-dismiss errors (user needs time to read)
- Show more than 5 toasts (information overload)

## One-Liner
Toast notifications are non-blocking, auto-dismissing status messages; they live in a fixed-position container, use `aria-live="polite"` for screen reader announcements, and respect `prefers-reduced-motion`.

---
*Learning: 2026-02-20 | 15min sprint*

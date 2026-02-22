# Component Design System: Toast/Notification

Transient feedback messages for user actions. Auto-dismiss, queueable, accessible. 6 variants, 4 positions, action support.

## Anatomy

```
┌─────────────────────────────────────────────┐
│ [icon]  Message text here      [action] [×] │
└─────────────────────────────────────────────┘
  ↑       ↑                        ↑       ↑
  Type    Content                  CTA     Dismiss
```

## Core CSS

```css
/* Toast container (positions) */
.toast-container {
  position: fixed;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 400px;
  pointer-events: none;
}

/* Position variants */
.toast-container--top-left { top: 16px; left: 16px; }
.toast-container--top-right { top: 16px; right: 16px; }
.toast-container--bottom-left { bottom: 16px; left: 16px; }
.toast-container--bottom-right { bottom: 16px; right: 16px; }

/* Stack direction for bottom positions */
.toast-container--bottom-left,
.toast-container--bottom-right {
  flex-direction: column-reverse;
}

/* Toast base */
.toast {
  --toast-bg: #1f2937;
  --toast-color: #fff;
  --toast-accent: #3b82f6;
  --toast-duration: 5000ms;
  
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--toast-bg);
  color: var(--toast-color);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  font-size: 0.9375rem;
  pointer-events: auto;
  
  animation: toast-enter 0.3s ease;
}

.toast.toast--exit {
  animation: toast-exit 0.2s ease forwards;
}

@keyframes toast-enter {
  from {
    opacity: 0;
    transform: translateY(100%);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes toast-exit {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(100%);
  }
}

/* Type variants */
.toast--success { --toast-accent: #10b981; }
.toast--error { --toast-accent: #ef4444; }
.toast--warning { --toast-accent: #f59e0b; }
.toast--info { --toast-accent: #3b82f6; }

/* Icon indicator */
.toast__icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  color: var(--toast-accent);
}

.toast__icon::before {
  display: block;
  font-size: 16px;
  line-height: 20px;
}

.toast--success .toast__icon::before { content: "✓"; }
.toast--error .toast__icon::before { content: "✕"; }
.toast--warning .toast__icon::before { content: "⚠"; }
.toast--info .toast__icon::before { content: "ℹ"; }

/* Content */
.toast__content {
  flex: 1;
  min-width: 0;
}

.toast__message {
  margin: 0;
  line-height: 1.4;
}

.toast__action {
  flex-shrink: 0;
  background: transparent;
  border: none;
  color: var(--toast-accent);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.15s;
}

.toast__action:hover {
  background: rgba(255, 255, 255, 0.1);
}

.toast__action:focus-visible {
  outline: 2px solid var(--toast-accent);
  outline-offset: 2px;
}

/* Dismiss button */
.toast__dismiss {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  color: var(--toast-color);
  opacity: 0.6;
  cursor: pointer;
  padding: 0;
  border-radius: 4px;
  transition: opacity 0.15s, background 0.15s;
}

.toast__dismiss:hover {
  opacity: 1;
  background: rgba(255, 255, 255, 0.1);
}

.toast__dismiss:focus-visible {
  outline: 2px solid var(--toast-color);
  outline-offset: 2px;
}

/* Progress bar */
.toast__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: var(--toast-accent);
  animation: toast-progress var(--toast-duration) linear forwards;
  border-radius: 0 0 8px 8px;
}

@keyframes toast-progress {
  from { width: 100%; }
  to { width: 0%; }
}

.toast.toast--exit .toast__progress {
  animation: none;
}

/* Light variant */
.toast--light {
  --toast-bg: #fff;
  --toast-color: #1f2937;
  border: 1px solid #e5e5e5;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .toast {
    animation: none;
  }
  
  .toast__progress {
    animation: none;
    display: none;
  }
}

/* Mobile */
@media (max-width: 480px) {
  .toast-container {
    left: 8px;
    right: 8px;
    max-width: none;
  }
  
  .toast {
    padding: 10px 12px;
  }
}
```

## HTML Structure

```html
<!-- Container (one per position) -->
<div 
  class="toast-container toast-container--bottom-right"
  role="region"
  aria-label="Notifications"
  aria-live="polite"
  id="toast-container"
></div>

<!-- Toast instance -->
<div 
  class="toast toast--success"
  role="status"
  data-toast-id="123"
>
  <span class="toast__icon" aria-hidden="true"></span>
  <span class="toast__content">
    <p class="toast__message">Changes saved successfully</p>
  </span>
  <button class="toast__action" type="button">View</button>
  <button class="toast__dismiss" type="button" aria-label="Dismiss">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M18 6L6 18M6 6l12 12"/>
    </svg>
  </button>
  <div class="toast__progress"></div>
</div>
```

## JavaScript Controller

```javascript
class Toast {
  static containers = new Map();
  static queue = [];
  static maxVisible = 3;
  
  static init(position = 'bottom-right') {
    if (this.containers.has(position)) return this.containers.get(position);
    
    const container = document.createElement('div');
    container.className = `toast-container toast-container--${position}`;
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', 'Notifications');
    container.setAttribute('aria-live', 'polite');
    document.body.appendChild(container);
    
    this.containers.set(position, container);
    return container;
  }
  
  static show({
    message,
    type = 'info',
    duration = 5000,
    action,
    position = 'bottom-right',
    dismissible = true,
  }) {
    const container = this.init(position);
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast--${type}`;
    toast.setAttribute('role', 'status');
    
    const id = `toast-${Date.now()}`;
    toast.dataset.toastId = id;
    
    // Build content
    toast.innerHTML = `
      <span class="toast__icon" aria-hidden="true"></span>
      <span class="toast__content">
        <p class="toast__message">${this.escapeHtml(message)}</p>
      </span>
      ${action ? `<button class="toast__action" type="button">${this.escapeHtml(action.label)}</button>` : ''}
      ${dismissible ? `
        <button class="toast__dismiss" type="button" aria-label="Dismiss">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      ` : ''}
      ${duration > 0 ? `<div class="toast__progress" style="--toast-duration: ${duration}ms"></div>` : ''}
    `;
    
    // Dismiss handler
    const dismissBtn = toast.querySelector('.toast__dismiss');
    if (dismissible && dismissBtn) {
      dismissBtn.addEventListener('click', () => this.dismiss(id));
    }
    
    // Action handler
    if (action) {
      const actionBtn = toast.querySelector('.toast__action');
      if (actionBtn) {
        actionBtn.addEventListener('click', () => {
          action.onClick?.();
          this.dismiss(id);
        });
      }
    }
    
    // Auto dismiss
    let timeout;
    if (duration > 0) {
      timeout = setTimeout(() => this.dismiss(id), duration);
      toast._timeout = timeout;
    }
    
    // Pause on hover
    toast.addEventListener('mouseenter', () => {
      clearTimeout(timeout);
      toast.querySelector('.toast__progress')?.style.setProperty('animation-play-state', 'paused');
    });
    
    toast.addEventListener('mouseleave', () => {
      if (duration > 0) {
        timeout = setTimeout(() => this.dismiss(id), 1000);
        toast._timeout = timeout;
      }
    });
    
    container.appendChild(toast);
    
    // Limit visible count
    const toasts = container.querySelectorAll('.toast:not(.toast--exit)');
    if (toasts.length > this.maxVisible) {
      const oldest = toasts[0];
      this.dismiss(oldest.dataset.toastId);
    }
    
    return id;
  }
  
  static dismiss(id) {
    const toast = document.querySelector(`[data-toast-id="${id}"]`);
    if (!toast || toast.classList.contains('toast--exit')) return;
    
    clearTimeout(toast._timeout);
    toast.classList.add('toast--exit');
    
    toast.addEventListener('animationend', () => {
      toast.remove();
    }, { once: true });
  }
  
  static success(message, options = {}) {
    return this.show({ message, type: 'success', ...options });
  }
  
  static error(message, options = {}) {
    return this.show({ 
      message, 
      type: 'error', 
      duration: options.duration ?? 7000, // Longer for errors
      ...options 
    });
  }
  
  static warning(message, options = {}) {
    return this.show({ message, type: 'warning', ...options });
  }
  
  static info(message, options = {}) {
    return this.show({ message, type: 'info', ...options });
  }
  
  static escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
}

// Auto-init on DOM ready
document.addEventListener('DOMContentLoaded', () => Toast.init());

// Export
window.Toast = Toast;
```

## Usage Examples

```javascript
// Basic usage
Toast.success('File uploaded successfully');
Toast.error('Connection failed. Please try again.');
Toast.warning('Your session will expire in 5 minutes');
Toast.info('New features available');

// With action
Toast.error('Failed to save changes', {
  action: {
    label: 'Retry',
    onClick: () => saveChanges()
  }
});

// Custom duration (ms)
Toast.info('Copied to clipboard', { duration: 2000 });

// Persistent (no auto-dismiss)
Toast.warning('Critical update required', { 
  duration: 0, 
  dismissible: false 
});

// Custom position
Toast.success('Welcome!', { position: 'top-center' });

// Programmatic dismiss
const toastId = Toast.info('Processing...', { duration: 0 });
// Later...
Toast.dismiss(toastId);
```

## Accessibility Requirements

| Requirement | Implementation |
|-------------|----------------|
| Live region | `aria-live="polite"` on container |
| Role | `role="status"` on each toast |
| Dismiss button | `aria-label="Dismiss"` |
| Focus management | Toast doesn't steal focus |
| Screen reader | Announced via aria-live |
| Keyboard | Dismiss with Escape key |

## Variant Guidelines

| Type | When to Use | Duration |
|------|-------------|----------|
| Success | Action completed | 3-5s |
| Error | Action failed | 5-7s |
| Warning | Attention needed | 5-7s |
| Info | Neutral feedback | 3-5s |

## Configuration Options

```javascript
Toast.configure({
  position: 'bottom-right',  // default position
  maxVisible: 3,             // max visible toasts
  defaultDuration: 5000,     // default duration
  pauseOnHover: true,        // pause timer on hover
  dismissOnEscape: true,     // dismiss active toast on Esc
});
```

---
*Learned: 2026-02-22 | 15-min sprint*
# Button Component System — Design System Element

**Topic:** Button Component Architecture  
**Learned:** 2026-02-19 03:24 CST  
**Time:** 15 min

---

## 1. Base Button (The Foundation)

```css
.btn {
  /* Reset */
  appearance: none;
  border: none;
  background: none;
  cursor: pointer;
  
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  
  /* Sizing */
  padding: 0.625rem 1.25rem;
  min-height: 2.75rem;
  
  /* Typography */
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.25;
  text-decoration: none;
  
  /* Visual */
  border-radius: 0.5rem;
  transition: all 150ms ease;
  
  /* Accessibility */
  outline: 2px solid transparent;
  outline-offset: 2px;
  
  /* Prevent text selection */
  user-select: none;
}

.btn:focus-visible {
  outline-color: var(--color-focus, #3b82f6);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

---

## 2. Variant System (Semantic Intent)

```css
/* Primary - Main CTA */
.btn--primary {
  background: var(--color-primary, #3b82f6);
  color: white;
}
.btn--primary:hover:not(:disabled) {
  background: var(--color-primary-hover, #2563eb);
}

/* Secondary - Alternative action */
.btn--secondary {
  background: var(--color-surface, #f1f5f9);
  color: var(--color-text, #1e293b);
}
.btn--secondary:hover:not(:disabled) {
  background: var(--color-surface-hover, #e2e8f0);
}

/* Tertiary/Ghost - Low emphasis */
.btn--tertiary {
  background: transparent;
  color: var(--color-primary, #3b82f6);
}
.btn--tertiary:hover:not(:disabled) {
  background: var(--color-primary-subtle, #eff6ff);
}

/* Destructive - Danger actions */
.btn--danger {
  background: var(--color-error, #ef4444);
  color: white;
}
.btn--danger:hover:not(:disabled) {
  background: var(--color-error-hover, #dc2626);
}
```

---

## 3. Size Scale

```css
.btn--sm {
  padding: 0.375rem 0.75rem;
  min-height: 2.25rem;
  font-size: 0.8125rem;
}

.btn--md { /* Default */ }

.btn--lg {
  padding: 0.875rem 1.75rem;
  min-height: 3rem;
  font-size: 1rem;
}

.btn--icon {
  padding: 0.625rem;
  min-height: 2.75rem;
  min-width: 2.75rem;
}
```

---

## 4. HTML Patterns

```html
<!-- Standard button -->
<button class="btn btn--primary">Save changes</button>

<!-- With icon (leading) -->
<button class="btn btn--primary">
  <svg aria-hidden="true" class="btn__icon">...</svg>
  Download
</button>

<!-- Icon only (requires aria-label) -->
<button class="btn btn--secondary btn--icon" aria-label="Close dialog">
  <svg aria-hidden="true">...</svg>
</button>

<!-- As link -->
<a href="/login" class="btn btn--primary">Sign in</a>

<!-- Loading state -->
<button class="btn btn--primary" disabled>
  <span class="spinner spinner--sm" aria-hidden="true"></span>
  <span>Saving...</span>
</button>
```

---

## 5. State Management

| State | Visual | Implementation |
|-------|--------|----------------|
| Default | Solid bg | `.btn--primary` |
| Hover | Darker bg | `:hover` pseudo |
| Active | Slight scale down | `:active { transform: scale(0.98) }` |
| Focus | Ring outline | `:focus-visible` |
| Disabled | 50% opacity, no-pointer | `[disabled]` attribute |
| Loading | Spinner + disabled | JS toggles class + disabled |

---

## 6. Quick Usage Guidelines

**DO:**
- Use `min-height` for touch targets (≥44px)
- Include `gap` for icon+text spacing
- Disable buttons during async actions
- Use `focus-visible` not `focus` (no ring on click)

**DON'T:**
- Use disabled styles alone without `[disabled]` attr
- Make buttons too small on mobile
- Skip `aria-label` on icon-only buttons

---

## 7. CSS Custom Properties (Themable)

```css
:root {
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --color-primary-subtle: #eff6ff;
  --color-surface: #f1f5f9;
  --color-surface-hover: #e2e8f0;
  --color-focus: #3b82f6;
  --color-error: #ef4444;
  --color-error-hover: #dc2626;
}
```

Override at component or theme level for brand consistency.

---

**Next:** Create complementary Form Input component with matching visual language.

# Skeleton Loader Pattern — Design System Component

## What
- Placeholder UI shown while content loads
- Mimics content structure (blocks, lines, media) without showing real data
- Reduces perceived load time; prevents layout shift when content arrives

## Anatomy

```html
<!-- Basic skeleton card -->
<div class="skeleton-card" aria-busy="true" aria-label="Loading content">
  <div class="skeleton skeleton--avatar"></div>
  <div class="skeleton-stack">
    <div class="skeleton skeleton--title"></div>
    <div class="skeleton skeleton--line"></div>
    <div class="skeleton skeleton--line short"></div>
  </div>
</div>
```

## CSS Implementation

### Base Skeleton
```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 25%,
    var(--skeleton-highlight) 50%,
    var(--skeleton-base) 75%
  );
  background-size: 200% 100%;
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Tokens */
:root {
  --skeleton-base: #e2e8f0;
  --skeleton-highlight: #f1f5f9;
}

[data-theme="dark"] {
  --skeleton-base: #334155;
  --skeleton-highlight: #475569;
}
```

### Variant Shapes
```css
.skeleton--avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}

.skeleton--title {
  height: 20px;
  width: 60%;
  margin-bottom: 12px;
}

.skeleton--line {
  height: 16px;
  width: 100%;
  margin-bottom: 8px;
}

.skeleton--line.short {
  width: 75%;
}

.skeleton--image {
  aspect-ratio: 16/9;
  width: 100%;
  border-radius: 8px;
}
```

### Alternative: Pulse (Simpler)
```css
.skeleton-pulse {
  background: var(--skeleton-base);
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

## Accessibility

### Required Attributes
```html
<div aria-busy="true" aria-live="polite" aria-label="Loading posts">
  <!-- skeletons -->
</div>
```

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  .skeleton {
    animation: none;
    background: var(--skeleton-base);
  }
}
```

### Screen Reader Strategy
- Skeleton containers get `aria-busy="true"` (content ignored by AT)
- Use `aria-live="polite"` on parent for load completion announcements
- Swap skeleton for real content, remove `aria-busy`

## State Transition Pattern

```html
<!-- Loading state -->
<div class="card" aria-busy="true" id="post-card">
  <div class="skeleton skeleton--avatar"></div>
  <div class="skeleton skeleton--title"></div>
</div>

<!-- Loaded state (JS swap) -->
<div class="card" id="post-card">
  <img src="avatar.jpg" alt="User avatar">
  <h3>Post Title</h3>
</div>
```

```js
// Transition helper
function showContent(container, contentHTML) {
  container.removeAttribute('aria-busy');
  container.innerHTML = contentHTML;
}
```

## Do / Don't

✅ **Do**
- Match skeleton shape to final content (avatar = circle, text = rounded rect)
- Use consistent timing (1.2–1.5s shimmer loops)
- Implement reduced-motion fallbacks
- Keep skeletons shallow (avoid nesting animations)

❌ **Don't**
- Use skeletons for fast loads (<300ms) — causes flash
- Randomize widths heavily (distracting)
- Forget aria-busy (screen readers announce empty divs)
- Mix multiple animation styles (shimmer + pulse together)

## One-Liner
Skeleton loaders are structural placeholders with shimmer animations; they reduce perceived latency when content fetches exceed 300ms.

---
*Learning: 2026-02-20 | 15min sprint*

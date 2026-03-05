# Skeleton Loading — CSS Pattern

A shimmer-loading skeleton screen that shows content structure before data loads.

## The Pattern

```css
.skeleton {
  background: linear-gradient(
    90deg,
    var(--skeleton-base) 0%,
    var(--skeleton-shine) 50%,
    var(--skeleton-base) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

:root {
  --skeleton-base: #e0e0e0;
  --skeleton-shine: #f0f0f0;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --skeleton-base: #2a2a2a;
    --skeleton-shine: #3a3a3a;
  }
}
```

## Common Shapes

```css
/* Text line */
.skeleton--text {
  height: 1em;
  width: 100%;
  margin-bottom: 0.5rem;
}

.skeleton--text-short {
  width: 60%;
}

/* Avatar */
.skeleton--avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
}

/* Button */
.skeleton--button {
  height: 40px;
  width: 120px;
  border-radius: 8px;
}

/* Card */
.skeleton--card {
  height: 200px;
  border-radius: 12px;
}
```

## Complete Example: User Card

```html
<div class="user-card user-card--loading">
  <div class="skeleton skeleton--avatar"></div>
  <div class="user-card__info">
    <div class="skeleton skeleton--text" style="width: 140px;"></div>
    <div class="skeleton skeleton--text skeleton--text-short"></div>
  </div>
</div>
```

```css
.user-card {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  background: var(--surface);
  border-radius: 12px;
}

.user-card__info {
  flex: 1;
}
```

## Reduced Motion

Always respect user preferences:

```css
@media (prefers-reduced-motion: reduce) {
  .skeleton {
    animation: none;
    background: var(--skeleton-base);
  }
}
```

## Accessibility

Skeletons are decorative loading states. Add ARIA attributes:

```html
<div class="user-card" role="status" aria-label="Loading user profile">
  <div class="skeleton skeleton--avatar"></div>
  ...
</div>
```

When loading completes:
```html
<div class="user-card" aria-live="polite">
  <!-- Real content -->
</div>
```

## Best Practices

| Do | Don't |
|----|-------|
| Match skeleton to real content shape | Use generic placeholders |
| Use subtle shimmer (low contrast) | Fast, distracting animations |
| Show realistic proportions | Wrong aspect ratios |
| Remove immediately when loaded | Keep skeleton visible too long |

## Performance Tip

Skeletons should be lightweight CSS animations (no JS). Reserve JS for:
- Fetching data
- Swapping skeleton ↔ real content
- Error states

## CSS-Only Fade Transition

```css
.user-card--loading {
  opacity: 1;
  transition: opacity 200ms ease;
}

.user-card--loaded {
  opacity: 0;
}

.user-card:not(.user-card--loading) .skeleton {
  display: none;
}
```

Swap classes with JS when data arrives.
# UX Pattern: Skeleton Screens

Loading placeholder that mimics content structure. Reduces perceived wait time vs spinners. Hot in mobile-first design.

## Why Skeleton > Spinners

| Spinner | Skeleton |
|---------|----------|
| Empty space | Content preview |
| "System working" | "Content loading" |
| 2-3s feels slow | Up to 8s acceptable |

**Rule of thumb:** Skeleton for >1s loads, spinner for <1s.

## Anatomy of a Skeleton Card

```
┌─────────────────────────────┐
│ ▓▓▓▓▓▓▓▓ (avatar)           │  ← Circle placeholder
│                             │
│ ████████████                │  ← Title (bold, shorter)
│ ████████████████████████    │  ← Subtitle (longer)
│                             │
│ ██████████████████████████  │  ← Body lines
│ ██████████████████████████  │  ← Body lines
│ ████████████                │  ← Last line short
└─────────────────────────────┘
```

## Pure CSS Skeleton (No JS)

```html
<!-- Card Skeleton -->
<div class="skeleton-card" role="status" aria-label="Loading content">
  <div class="skeleton-avatar"></div>
  <div class="skeleton-title"></div>
  <div class="skeleton-text"></div>
  <div class="skeleton-text"></div>
  <div class="skeleton-text short"></div>
</div>
```

```css
.skeleton-card {
  --skeleton-bg: #e5e5e5;
  --skeleton-shine: #f0f0f0;
  
  padding: 20px;
  border-radius: 12px;
  background: white;
}

/* Base shimmer effect */
.skeleton-avatar,
.skeleton-title,
.skeleton-text {
  background: linear-gradient(
    90deg,
    var(--skeleton-bg) 0%,
    var(--skeleton-shine) 50%,
    var(--skeleton-bg) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  margin-bottom: 16px;
}

.skeleton-title {
  height: 16px;
  width: 80%;
  margin-bottom: 8px;
  margin-top: 0;
}

.skeleton-text {
  height: 12px;
  width: 100%;
  margin-bottom: 8px;
}

.skeleton-text.short {
  width: 60%;
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

/* Respect user preference */
@media (prefers-reduced-motion: reduce) {
  .skeleton-avatar,
  .skeleton-title,
  .skeleton-text {
    animation: none;
  }
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .skeleton-card {
    --skeleton-bg: #3a3a3a;
    --skeleton-shine: #4a4a4a;
    background: #2d2d2d;
  }
}
```

## Table Skeleton

```html
<div class="skeleton-table" role="status" aria-label="Loading table">
  <div class="skeleton-row header">
    <div class="skeleton-cell" style="flex: 2;"></div>
    <div class="skeleton-cell" style="flex: 1;"></div>
    <div class="skeleton-cell" style="flex: 1;"></div>
  </div>
  <div class="skeleton-row">
    <div class="skeleton-cell" style="flex: 2;"></div>
    <div class="skeleton-cell" style="flex: 1;"></div>
    <div class="skeleton-cell" style="flex: 1;"></div>
  </div>
  <!-- Repeat rows -->
</div>
```

```css
.skeleton-table {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.skeleton-row {
  display: flex;
  gap: 16px;
}

.skeleton-cell {
  height: 12px;
  background: #e5e5e5;
  border-radius: 4px;
  animation: shimmer 1.5s infinite;
  background-size: 200% 100%;
  background: linear-gradient(
    90deg,
    var(--skeleton-bg) 0%,
    var(--skeleton-shine) 50%,
    var(--skeleton-bg) 100%
  );
  background-size: 200% 100%;
}

.skeleton-row.header .skeleton-cell {
  height: 14px;
  opacity: 0.6;
}
```

## JS Integration (React Hook)

```javascript
// Custom hook for skeleton visibility
function useSkeleton(delay = 200) {
  const [showSkeleton, setShowSkeleton] = useState(false);
  
  useEffect(() => {
    const timer = setTimeout(() => setShowSkeleton(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);
  
  return showSkeleton;
}

// Usage
function Card({ data, loading }) {
  const showSkeleton = useSkeleton(200);
  
  if (loading && showSkeleton) return <CardSkeleton />;
  if (!data) return null;
  
  return <Card data={data} />;
}
```

## Animation Timing Rules

| Duration | Effect |
|----------|--------|
| 1.0s | Too fast, jarring |
| **1.5s** | **Default sweet spot** |
| 2.0s+ | Feels sluggish |

- Direction: left→right (LTR languages)
- Easing: Linear (shimmer must be constant)
- Loop: Infinite until data loads

## Accessibility Checklist

```html
<!-- Required -->
<div role="status" aria-label="Loading [content type]">
  <!-- skeleton elements -->
</div>

<!-- When done loading -->
<div role="status" aria-live="polite">
  Content loaded
</div>
```

- Never use `aria-hidden` on skeletons
- Announce load completion for screen readers
- Support `prefers-reduced-motion`

## Common Mistakes

| ❌ Bad | ✅ Good |
|--------|---------|
| Random shapes | Actual content proportions |
| No animation | Subtle shimmer |
| Too many skeletons | Match expected content count |
| White only | Dark mode support |
| Skeleton → blank → content | Skeleton → content (crossfade) |

## Transition to Content

```css
.skeleton-content {
  opacity: 1;
  transition: opacity 0.2s ease;
}

.skeleton-content.loaded {
  opacity: 0;
  pointer-events: none;
}

.real-content {
  opacity: 0;
  transition: opacity 0.2s ease 0.1s; /* Delay start */
}

.real-content.visible {
  opacity: 1;
}
```

## When NOT to Use

- Content loads <200ms (just show spinner)
- User action required first (skeletons imply auto-load)
- Error states (show error, not skeleton)
- Empty states (show "No items" message)

---
*Learned: 2026-02-21 | 15-min sprint*

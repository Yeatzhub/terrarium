# UX Pattern: Skeleton Loading States

**Pattern:** Placeholder UI for perceived performance

## The Problem

| Traditional Loading | Skeleton Loading |
|---------------------|------------------|
| Spinner covers screen | Structure-aware placeholders |
| "Is this broken?" | Content shape preview |
| Sudden pop-in | Gradual content reveal |
| 3+ seconds feels slow | Feels faster |

## Core Concept

Show gray placeholder blocks that match the **layout structure** of final content. Animate as shimmer or pulse.

## CSS Implementation

### Shimmer Animation

```css
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.skeleton {
  background: linear-gradient(
    90deg,
    #e0e0e0 25%,
    #f0f0f0 50%,
    #e0e0e0 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}

/* Shapes */
.skeleton--text {
  height: 1em;
  margin-bottom: 0.5em;
}

.skeleton--text:last-child {
  width: 80%;
}

.skeleton--avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
}

.skeleton--image {
  width: 100%;
  padding-top: 56.25%; /* 16:9 aspect ratio */
}

.skeleton--title {
  height: 1.5em;
  width: 60%;
  margin-bottom: 1em;
}

.skeleton--card {
  height: 120px;
}
```

### Alternative: Pulse Animation

```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.skeleton--pulse {
  animation: pulse 2s ease-in-out infinite;
  background: #e0e0e0;
}
```

## Complete Card Example

```html
<!-- Loading State -->
<div class="card card--loading">
  <div class="card__header">
    <div class="skeleton skeleton--avatar"></div>
    <div class="card__meta">
      <div class="skeleton skeleton--text"></div>
      <div class="skeleton skeleton--text" style="width: 60%"></div>
    </div>
  </div>
  <div class="skeleton skeleton--title"></div>
  <div class="skeleton skeleton--text"></div>
  <div class="skeleton skeleton--text"></div>
  <div class="skeleton skeleton--text" style="width: 40%"></div>
</div>
```

```css
.card--loading {
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.card__header {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.card__meta {
  flex: 1;
}

/* Final loaded state */
.card:not(.card--loading) .skeleton {
  display: none;
}
```

## When to Use

| ✅ Use Skeletons | ❌ Use Spinners |
|------------------|-----------------|
| Loading content in layout | Full page load |
| Known content structure | Unknown/variable content |
| Lists, feeds, cards | File upload/processing |
| < 4 seconds load time | Heavy operations |
| User expects content | One-time operations |

## Implementation Strategy

```javascript
// React Pattern
function Card({ title, author, content, loading }) {
  if (loading) {
    return (
      <div className="card card--loading">
        <div className="skeleton skeleton--title"></div>
        {Array(3).fill().map((_, i) => (
          <div key={i} className="skeleton skeleton--text"></div>
        ))}
      </div>
    );
  }
  
  return <div className="card">{/* actual content */}</div>;
}
```

```javascript
// Vanilla JS — Swap classes
function showSkeleton(container) {
  container.classList.add('skeleton-container');
  container.innerHTML = container.dataset.skeletonMarkup;
}

function hideSkeleton(container, content) {
  container.classList.remove('skeleton-container');
  container.innerHTML = content;
}
```

## Accessibility

```css
@media (prefers-reduced-motion: reduce) {
  .skeleton {
    animation: none;
    background: #e0e0e0;
  }
}
```

```html
<div 
  role="status" 
  aria-live="polite" 
  aria-label="Loading content"
  class="card card--loading"
>
  <!-- skeletons -->
</div>
```

| Requirement | Why |
|-------------|-----|
| `role="status"` | Announces as status update |
| `aria-live="polite"` | Doesn't interrupt |
| `aria-label` | Context for screen readers |
| Reduced motion | Stop animation for vestibular issues |

## Best Practices

1. **Match layout exactly** — same padding, margins, element spacing
2. **Use appropriate shapes** — circles for avatars, rectangles for text
3. **Randomize widths** — never all 100%, looks like a bar code
4. **Limit simultaneous** — 3-5 on screen max
5. **Fade transition** — smooth to content, not abrupt

## Common Mistakes

| ❌ Mistake | ✅ Fix |
|------------|--------|
| All same width | Vary widths (60-100%) |
| Generic gray blocks | Match layout structure |
| No skeleton for images | Preserve aspect ratio |
| Shimmer on everything | Still on lists, pulse on isolated |
| Infinite skeleton | Timeout to error state after 10s |

## Performance Note

Use `will-change: opacity` or `will-change: background-position` on animated skeletons:

```css
.skeleton {
  will-change: background-position;
}

@media (prefers-reduced-motion: reduce) {
  .skeleton {
    will-change: auto;
  }
}
```

---
*Learned: 2026-02-19* | *Time: ~12 min* | *Reference: Luke Wroblewski on skeletons + Nielsen Norman Group*

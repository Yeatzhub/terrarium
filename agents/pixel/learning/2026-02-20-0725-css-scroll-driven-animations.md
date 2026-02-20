# CSS Scroll-Driven Animations — Quick Reference

## What
- Animate elements based on **scroll position** — no JavaScript
- Two types: scroll progress (timeline) & view progress (element enters viewport)
- Supported: Chrome 115+, Edge 115+, Firefox nightly, Safari 2024+

## Core Concepts

### 1. Scroll Progress Timeline
Tracks entire page/document scroll:
```css
html {
  scroll-timeline: --page-scroll block;
}

.progress-bar {
  animation: grow-progress auto linear;
  animation-timeline: --page-scroll;
}

@keyframes grow-progress {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
```

### 2. View Progress Timeline
Tracks element entering/leaving viewport:
```css
.card {
  animation: fade-in-up auto linear both;
  animation-timeline: view();
  animation-range: entry 25% cover 50%;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(100px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

## Animation Range (Key!)
Controls when animation runs relative to viewport:

| Range | Meaning |
|-------|---------|
| `entry` | Element enters viewport (0% = bottom edge hits bottom, 100% = fully in) |
| `exit` | Element leaves viewport |
| `cover` | Element crosses viewport (0% = enters, 100% = exits) |
| `contain` | Element fully contained in viewport |

### Range Syntax
```css
/* Start at entry 0%, end at cover 50% */
animation-range: entry 0% cover 50%;

/* Shorthand: start when 25% visible, end at center */
animation-range: entry 25% cover 50%;
```

## Practical Patterns

### Reading Progress Bar
```css
.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 4px;
  background: var(--accent);
  transform-origin: left;
  animation: grow auto linear;
  animation-timeline: scroll();
}

@keyframes grow {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
```

### Image Reveal (Cover Flow Style)
```css
.reveal-image {
  opacity: 0;
  clip-path: inset(0 100% 0 0);
  animation: reveal auto linear;
  animation-timeline: view();
  animation-range: entry 0% cover 40%;
}

@keyframes reveal {
  to {
    opacity: 1;
    clip-path: inset(0 0 0 0);
  }
}
```

### Sticky Header Shrink
```css
.header {
  animation: header-shrink auto linear;
  animation-timeline: scroll();
  animation-range: 0 200px;
}

@keyframes header-shrink {
  to {
    padding: 0.5rem 1rem;
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(10px);
  }
}
```

### Horizontal Scroll Section
```css
.horizontal-section {
  overflow-x: auto;
  scroll-timeline: --horizontal inline;
}

.scrolling-content {
  animation: slide auto linear;
  animation-timeline: --horizontal;
}
```

## JavaScript Fallback / Enhancement
```js
// Check support
if (!CSS.supports('animation-timeline', 'scroll()')) {
  // Load polyfill or use IntersectionObserver fallback
  import('https://flackr.github.io/scroll-timeline/dist/scroll-timeline.js');
}
```

## Key Properties Summary
```css
/* Define timeline on scroll container */
scroll-timeline: --name block|inline;

/* Use on animated element */
animation-timeline: scroll() | view() | --named-timeline;
animation-range: entry 0% cover 50%; /* optional */
```

## Performance Notes
✅ Runs on compositor thread (no main thread blocking)  
✅ No event listeners = no memory leaks  
✅ Respects `prefers-reduced-motion` automatically  

## Common Mistakes
❌ Forgetting `overflow: visible` on parent (blocks intersection)  
❌ Setting `animation-fill-mode: forwards` without proper range  
❌ Using with `position: fixed` on animation target (timeline confusion)

## One-Liner
`animation-timeline: view()` + `@keyframes` = declarative scroll animations that run at 60fps without JavaScript.

---
*Learning: 2026-02-20 | 15min sprint*

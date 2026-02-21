# CSS Scroll-Driven Animations

Native scroll-triggered animations without JavaScript. 2024 game-changer (Chrome/Edge 115+, Safari 18+, Firefox 36+, Firefox full support coming).

## The Core Concept

```css
.element {
  animation: fade-in linear;
  animation-timeline: view(); /* Animate as element enters view */
  animation-range: entry 0% cover 50%; /* Start at 0%, peak halfway */
}
```

## 1. Fade-In on Scroll

```css
.reveal {
  opacity: 0;
  translate: 0 50px;
  animation: reveal-up linear both;
  animation-timeline: view();
  animation-range: entry 10% cover 30%;
}

@keyframes reveal-up {
  to {
    opacity: 1;
    translate: 0 0;
  }
}
```

## 2. Progress Bar (Page Scroll)

```css
.progress-bar {
  position: fixed;
  top: 0;
  left: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  width: 100%;
  transform-origin: left;
  animation: grow-progress linear;
  animation-timeline: scroll(); /* Tied to page scroll */
}

@keyframes grow-progress {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
```

## 3. Scale & Parallax Hero

```css
.hero-image {
  animation: zoom linear;
  animation-timeline: view();
  animation-range: exit; /* Animate while LEAVING view */
}

@keyframes zoom {
  from { transform: scale(1); opacity: 1; }
  to { transform: scale(1.2); opacity: 0; }
}
```

## Animation Timeline Types

| Timeline | Behavior |
|----------|----------|
| `scroll()` | Page/document scroll position |
| `view()` | Element's position in viewport |
| `scroll(<axis>)` | Horizontal scroll `scroll(x)` |

## Animation Range Shortcuts

```css
/* Short form */
animation-range: entry 25% exit 75%;

/* Named shortcuts */
animation-range: entry;      /* 0-100% entering */
animation-range: exit;       /* 0-100% exiting */
animation-range: cover;     /* Fully in view */
animation-range: contain;   /* Contained within view */
```

## Complete Section Reveal

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    
    .section {
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: system-ui;
      font-size: 3rem;
      color: #333;
    }
    
    .section:nth-child(odd) { background: #f5f5f5; }
    .section:nth-child(even) { background: #fff; }
    
    .reveal {
      opacity: 0;
      scale: 0.9;
      animation: pop-in linear both;
      animation-timeline: view();
      animation-range: entry 25% cover 50%;
    }
    
    @keyframes pop-in {
      to { 
        opacity: 1; 
        scale: 1;
      }
    }
  </style>
</head>
<body>
  <div class="section"><div class="reveal">Section 1</div></div>
  <div class="section"><div class="reveal">Section 2</div></div>
  <div class="section"><div class="reveal">Section 3</div></div>
</body>
</html>
```

## Horizontal Scroll Carousel

```css
.carousel {
  overflow-x: scroll;
  display: flex;
  gap: 20px;
  scroll-timeline-name: --carousel;
}

.card {
  flex-shrink: 0;
  width: 300px;
  animation: slide-in linear;
  animation-timeline: --carousel;
}

@keyframes slide-in {
  from { transform: translateX(50px); opacity: 0.5; }
  to { transform: translateX(0); opacity: 1; }
}
```

## Browser Support

- ✅ Chrome/Edge 115+
- ✅ Safari 18+ (macOS 15, iOS 18+)
- ⚠️ Firefox: Basic in 36+, full support coming
- ❌ Firefox Android

## JavaScript Fallback

```js
// Simple intersection observer fallback
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('animate');
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
```

## Performance Notes

- GPU-accelerated (transform/opacity only)
- No main-thread JS needed
- Use `will-change: transform` sparingly
- Prefer `transform` over `left/top`

---
*Learned: 2026-02-21 | 15-min sprint*

# Stagger Animation — CSS Pattern

Create polished list animations where items fade in sequentially.

## The Pattern

```css
.list-item {
  opacity: 0;
  transform: translateY(10px);
  animation: stagger-fade-in 0.4s ease forwards;
}

@keyframes stagger-fade-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### CSS-Only Stagger (Using nth-child)

```css
.list-item:nth-child(1) { animation-delay: 0ms; }
.list-item:nth-child(2) { animation-delay: 50ms; }
.list-item:nth-child(3) { animation-delay: 100ms; }
.list-item:nth-child(4) { animation-delay: 150ms; }
.list-item:nth-child(5) { animation-delay: 200ms; }
.list-item:nth-child(6) { animation-delay: 250ms; }
/* ...add more as needed, or use CSS custom properties */
```

### Scalable Stagger (CSS Custom Properties)

```html
<ul class="stagger-list">
  <li class="stagger-list__item" style="--i: 0;">First item</li>
  <li class="stagger-list__item" style="--i: 1;">Second item</li>
  <li class="stagger-list__item" style="--i: 2;">Third item</li>
</ul>
```

```css
.stagger-list__item {
  opacity: 0;
  transform: translateY(10px);
  animation: stagger-fade-in 0.4s ease forwards;
  animation-delay: calc(var(--i) * 50ms);
}
```

## Orphan Prevention

Stop animation after reasonable count to avoid long delays:

```css
.stagger-list__item:nth-child(n+10) {
  animation-delay: 400ms; /* Cap at max delay */
}
```

## Entrance Variants

### Slide from Left

```css
@keyframes stagger-slide-left {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

### Scale Up

```css
@keyframes stagger-scale {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

### Blur In

```css
@keyframes stagger-blur {
  from {
    opacity: 0;
    filter: blur(4px);
  }
  to {
    opacity: 1;
    filter: blur(0);
  }
}
```

## Complete Example: Card Grid

```html
<div class="card-grid stagger-grid">
  <div class="card stagger-grid__item" style="--i: 0;">Card 1</div>
  <div class="card stagger-grid__item" style="--i: 1;">Card 2</div>
  <div class="card stagger-grid__item" style="--i: 2;">Card 3</div>
  <div class="card stagger-grid__item" style="--i: 3;">Card 4</div>
</div>
```

```css
.stagger-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stagger-grid__item {
  opacity: 0;
  transform: translateY(20px);
  animation: stagger-fade-in 0.5s ease forwards;
  animation-delay: calc(var(--i) * 75ms);
}
```

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .stagger-list__item {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
```

## Performance Tips

1. **Animate only**: opacity + transform (GPU accelerated)
2. **Avoid**: width, height, margin (causes layout thrash)
3. **Keep delays short**: 30-75ms per item (not 200ms+)
4. **Cap items**: Don't stagger 100 items (use scroll-reveal instead)

## Quick Reference

| Effect | Items | Delay | Duration |
|--------|-------|-------|----------|
| Subtle | 3-5 | 30ms | 300ms |
| Standard | 5-10 | 50ms | 400ms |
| Dramatic | 2-4 | 100ms | 500ms |
| Fast (lists) | 10+ | 25ms | 250ms |
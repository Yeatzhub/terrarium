# CSS Effect: Glassmorphism Card

**Pattern:** Frosted glass overlay effect

## The Core Styles

```css
.glass-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
}
```

## Key Ingredients

| Property | Purpose | Value |
|----------|---------|-------|
| `background` | Semi-transparent tint | `rgba(255,255,255,0.15)` |
| `backdrop-filter: blur()` | Frosted glass effect | 8–20px typical |
| `border` | Glass edge highlight | Low opacity white |
| `border-radius` | Soft modern corners | 12–24px |
| `box-shadow` | Depth + grounding | Soft diffused shadow |

## Full Example

```css
/* Container needs something to blur */
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.glass-card {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem;
  color: #fff;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  box-shadow: 
    0 4px 30px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.glass-card h2 {
  margin: 0 0 0.5rem;
  font-weight: 600;
}

.glass-card p {
  margin: 0 0 1.5rem;
  opacity: 0.9;
}
```

```html
<div class="app">
  <div class="glass-card">
    <h2>Welcome Back</h2>
    <p>Sign in to continue</p>
    <form><!-- form content --></form>
  </div>
</div>
```

## Dark Variant

```css
.glass-card--dark {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
}
```

## Browser Support

| Feature | Support | Fallback |
|---------|---------|----------|
| `backdrop-filter` | ~95% | Solid color background |
| `-webkit-` prefix | Safari | Required |

```css
/* Fallback for older browsers */
@supports not (backdrop-filter: blur(12px)) {
  .glass-card {
    background: rgba(255, 255, 255, 0.85);
    color: #333;
  }
  
  .glass-card--dark {
    background: rgba(30, 30, 30, 0.95);
    color: #fff;
  }
}
```

## Fine-Tuning Tips

**Blur amount:**
- 8px = subtle, content still readable
- 12px = balanced default
- 20px+ = heavy frost, more abstract

**Background opacity:**
- 0.05–0.15 = light, airy
- 0.2–0.35 = stronger, more opaque
- Match to background contrast

**Border brightness:**
- 0.1–0.2 = subtle edge
- 0.3–0.5 = stronger glass feel
- Inset shadow adds depth: `inset 0 1px 0 rgba(255,255,255,0.2)`

## Common Use Cases

- Login/signup overlays on video/gradients
- Modal dialogs
- Navigation bars on scroll
- Cards over hero images
- Floating toolbars

## Gotchas

1. **Z-index stacking** — `backdrop-filter` creates new stacking context
2. **Overflow hidden** — Parent `overflow: hidden` clips the blur
3. **Performance** — Large areas on mobile: use sparingly
4. **Color contrast** — Ensure text is readable over blurred content

---
*Learned: 2026-02-19* | *Time: ~10 min*

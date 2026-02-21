# CSS Glassmorphism Card Pattern

Modern, ethereal UI cards with frosted glass effect. Hot in 2024-2025.

## The Core CSS

```css
.glass-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px); /* Safari */
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 
    0 4px 30px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}
```

## Required Conditions

Works **only** when:
- Container has `background` (image, gradient, or solid color)
- Element has low opacity background (`rgba` with alpha < 0.5)

## Complete Example

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body {
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      font-family: system-ui, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .glass-card {
      background: rgba(255, 255, 255, 0.15);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(255, 255, 255, 0.25);
      border-radius: 20px;
      padding: 32px;
      max-width: 320px;
      color: white;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .glass-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
    }
  </style>
</head>
<body>
  <div class="glass-card">
    <h2>Frosted Glass</h2>
    <p>Content stays readable with depth.</p>
  </div>
</body>
</html>
```

## Quick Tweaks

| Effect | Change |
|--------|--------|
| More frosted | Higher `blur(20px+)` |
| Dark glass | Use `rgba(0,0,0,0.3)` |
| Subtle border | Lower alpha to `0.1` |
| Performance | Skip on `prefers-reduced-motion` |

## Browser Support

- ✅ Chrome/Edge 76+
- ✅ Safari 9+ (with `-webkit-`)
- ✅ Firefox 103+
- ❌ Firefox Android <103, IE

## Fallback

```css
@supports not (backdrop-filter: blur(16px)) {
  .glass-card {
    background: rgba(255, 255, 255, 0.95);
    color: #333;
  }
}
```

## Use Cases

- Modal overlays
- Floating navigation bars
- Login screens on backgrounds
- Dashboard widgets

---
*Learned: 2026-02-21 | 15-min sprint*

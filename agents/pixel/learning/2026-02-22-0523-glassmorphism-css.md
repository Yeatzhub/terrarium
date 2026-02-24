# Glassmorphism CSS Pattern

A modern glass effect with proper fallbacks and accessibility.

## The Pattern

```css
.glass {
  /* Fallback for unsupported browsers */
  background: rgba(255, 255, 255, 0.8);
  
  /* Modern glass effect */
  @supports (backdrop-filter: blur(1px)) {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(12px) saturate(180%);
    -webkit-backdrop-filter: blur(12px) saturate(180%);
  }
  
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  box-shadow: 
    0 4px 30px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}
```

## Dark Mode Variant

```css
.glass--dark {
  background: rgba(0, 0, 0, 0.6);
  
  @supports (backdrop-filter: blur(1px)) {
    background: rgba(0, 0, 0, 0.25);
    backdrop-filter: blur(12px) saturate(150%);
  }
  
  border-color: rgba(255, 255, 255, 0.1);
}
```

## Accessibility Notes

1. **Contrast**: Glass surfaces need 4.5:1 contrast ratio for text
2. **Motion**: Respect `prefers-reduced-motion`:
   ```css
   @media (prefers-reduced-motion: reduce) {
     .glass { backdrop-filter: none; background: rgba(255,255,255,0.95); }
   }
   ```
3. **Fallback**: Always provide solid fallback via `@supports`

## When to Use

✅ Over images, gradients, or video backgrounds
✅ Modal overlays, cards, navigation bars
❌ Over solid flat backgrounds (pointless blur)
❌ Small UI elements (blur is expensive)

## Performance Tip

`backdrop-filter` triggers GPU acceleration. Limit to 3-4 elements visible at once.
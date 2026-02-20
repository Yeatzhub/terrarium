# CSS Pattern: Aspect Ratio

**Pattern:** Intrinsic sizing for responsive media

## The Core Property

```css
.responsive-container {
  aspect-ratio: 16 / 9;
  /* or aspect-ratio: 1; for square */
  /* or aspect-ratio: 3 / 4; for portrait */
}
```

## The Old Way vs. The New Way

| Old (Hack) | New (Native) |
|------------|--------------|
| `padding-top: 56.25%` on pseudo-element | `aspect-ratio: 16 / 9` |
| Magic numbers | Readable, declarative |
| Extra wrapper required | Single property |

## Practical Examples

### Video Container

```css
.video-wrapper {
  position: relative;
  aspect-ratio: 16 / 9;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

.video-wrapper iframe,
.video-wrapper video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
```

```html
<div class="video-wrapper">
  <iframe src="..." frameborder="0"></iframe>
</div>
```

### Image Card with Fixed Ratio

```css
.card__image {
  aspect-ratio: 4 / 3;
  width: 100%;
  object-fit: cover;
  border-radius: 8px 8px 0 0;
}
```

```html
<article class="card">
  <img class="card__image" src="photo.jpg" alt="..." />
  <div class="card__content">
    <h3>Card Title</h3>
  </div>
</article>
```

### Square Avatar

```css
.avatar {
  width: 48px;
  aspect-ratio: 1;
  border-radius: 50%;
  object-fit: cover;
}
```

## Common Ratios Reference

| Ratio | CSS Value | Use Case |
|-------|-----------|----------|
| Square | `1` or `1 / 1` | Avatars, icons, thumbnails |
| Standard HD | `16 / 9` | Videos, hero images |
| Photo | `4 / 3` | Cards, galleries |
| Portrait Photo | `3 / 4` | Product shots, portraits |
| Ultra-wide | `21 / 9` | Cinematic video |
| Vertical Video | `9 / 16` | Stories, mobile video |
| Classic | `5 / 4` | Frames, art |

## Fallback for Older Browsers

```css
.container {
  aspect-ratio: 16 / 9;
}

/* Fallback using padding hack */
@supports not (aspect-ratio: 1) {
  .container {
    position: relative;
    height: 0;
    padding-bottom: 56.25%; /* 9 / 16 * 100 */
  }
  
  .container > * {
    position: absolute;
    inset: 0;
  }
}
```

## With max-width Behavior

```css
.image-container {
  max-width: 800px;
  width: 100%;
  aspect-ratio: 16 / 9;
}

/* Height auto-maintains the ratio as width scales */
```

## Combined with object-fit

```css
.gallery__item {
  aspect-ratio: 1;
  overflow: hidden;
}

.gallery__item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  /* or object-fit: contain; to see full image */
}
```

## Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 88+ |
| Firefox | 89+ |
| Safari | 15+ (14 partial) |
| Edge | 88+ |

~95% global support. Safe to use with fallback.

## Gotchas

1. **With flex/grid children** — Works, but child needs `width: 100%` or `height: 100%` to fill
2. **min/max dimension** — `aspect-ratio` respects `min-height`, `max-width`, etc.
3. **Height specified** — If you set `height`, aspect-ratio is ignored
4. **Images with srcset** — Still works; aspect-ratio prevents layout shift

## When to Use

| ✅ Use | ❌ Skip |
|--------|---------|
| Video embeds | When natural aspect varies |
| Card images | When content dictates height |
| Hero sections | If content must always be visible |
| Placeholder boxes | Inline text wrapping |

## Performance Benefit

```html
<!-- Without aspect-ratio: layout shift on load -->
<img src="photo.jpg" style="width: 100%;">

<!-- With aspect-ratio: no CLS -->
<img src="photo.jpg" style="width: 100%; aspect-ratio: 16 / 9;">
```

Prevents **Cumulative Layout Shift (CLS)** — improves Core Web Vitals.

---
*Learned: 2026-02-19* | *Time: ~9 min* | *Reference: MDN + web.dev on CLS*

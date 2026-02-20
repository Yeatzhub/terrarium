# CSS Pattern: Container Queries

**Pattern:** Component-based responsive design (not viewport-based)

## The Problem with Media Queries

```css
/* Media query: depends on viewport */
@media (min-width: 768px) {
  .card { display: flex; }
}
/* ❌ Breaks in narrow sidebars or wide modals */
```

**Container queries respond to the PARENT container, not the screen.**

## The Core Syntax

```css
/* 1. Define a container */
.card-container {
  container-type: inline-size;
  container-name: card;
}

/* 2. Query the container */
@container card (min-width: 400px) {
  .card { display: flex; }
}
```

## Complete Example

```css
/* Container setup */
.card-wrapper {
  container: card / inline-size;
  /* shorthand: name / type */
}

/* Base: vertical layout */
.card {
  padding: 1rem;
  border: 1px solid #dee2e6;
  border-radius: 8px;
}

.card__image {
  width: 100%;
  aspect-ratio: 16 / 9;
}

/* Wide container: horizontal */
@container card (min-width: 500px) {
  .card {
    display: flex;
    gap: 1.5rem;
  }
  
  .card__image {
    width: 150px;
    aspect-ratio: 1;
    flex-shrink: 0;
  }
}

/* Extra wide: more space */
@container card (min-width: 700px) {
  .card__image { width: 200px; }
}
```

```html
<!-- Same component, different layouts -->
<aside class="card-wrapper" style="width: 280px;">
  <article class="card">...vertical...</article>
</aside>

<main class="card-wrapper">
  <article class="card">...horizontal...</article>
</main>
```

## Container Types

| Type | Queries | Use When |
|------|---------|----------|
| `inline-size` | Width only | Most cases (cards, grids) |
| `size` | Width + height | Need height awareness |
| `normal` | None | Default (no query) |

```css
.card-wrapper {
  container-type: inline-size; /* width-based */
}

.banner-wrapper {
  container-type: size; /* needs explicit height */
}
```

## Container Units

- `cqi` = % of container inline size (width in horizontal writing)
- `cqb` = % of container block size (height)
- `cqmin` / `cqmax` = smaller/larger of cqi/cqb

```css
@container (min-width: 400px) {
  .card {
    padding: 3cqi; /* 3% of container width */
    font-size: clamp(14px, 2cqi, 20px);
  }
}
```

## Browser Support

| Browser | Version |
|---------|---------|
| Chrome/Edge | 105+ |
| Firefox | 110+ |
| Safari | 16+ |

~90% global support.

## Fallback Strategy

```css
/* Mobile-first base */
.card { padding: 1rem; }

@supports (container-type: inline-size) {
  .card-wrapper { container-type: inline-size; }
  
  @container (min-width: 500px) {
    .card { display: flex; }
  }
}

@supports not (container-type: inline-size) {
  /* Media query fallback */
  @media (min-width: 768px) {
    .card { display: flex; }
  }
}
```

## When to Use

| ✅ Use Container Queries | ❌ Keep Media Queries |
|---------------------------|----------------------|
| Card components | Page breakpoints |
| Reusable widgets | Typography sizing |
| Sidebar content | Navigation menus |
| Dashboard blocks | Footer visibility |

---
*Learned: 2026-02-19* | *Time: ~10 min*

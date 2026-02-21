# CSS Pattern: Container Queries

Component-driven responsive design. Elements respond to their container, not the viewport. 2022+ standard, now widely supported.

## The Problem with Media Queries

```css
/* Media query: responds to full SCREEN width */
@media (min-width: 768px) {
  .card { display: flex; }
}
/* Breaks when card is in a sidebar that's 200px wide */
```

## The Solution

```css
/* Define container */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

/* Query the CONTAINER size */
@container card (min-width: 400px) {
  .card { 
    display: flex;
    flex-direction: row;
  }
}
```

## Quick Start Pattern

```css
/* Step 1: Opt-in container on parent */
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.product-card {
  container-type: inline-size;  /* Required */
  container-name: product;      /* Optional name */
}

/* Step 2: Style based on container space */
@container product (min-width: 350px) {
  .product-card__content {
    padding: 24px;
  }
  .product-card__title {
    font-size: 1.25rem;
  }
}

@container product (min-width: 500px) {
  .product-card {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 20px;
  }
}
```

## Complete Card Component Example

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    * { margin: 0; box-sizing: border-box; }
    body { font-family: system-ui; padding: 40px; }
    
    /* Demo layout */
    .demo-layout {
      display: grid;
      grid-template-columns: 1fr 300px;
      gap: 40px;
    }
    
    /* Container wrapper */
    .card-container {
      container-type: inline-size;
      container-name: card;
    }
    
    /* Base card styles */
    .card {
      background: white;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .card__image {
      width: 100%;
      aspect-ratio: 16/9;
      background: linear-gradient(45deg, #667eea, #764ba2);
    }
    
    .card__content {
      padding: 16px;
    }
    
    .card__title { font-size: 1.1rem; margin-bottom: 8px; }
    .card__text { color: #666; font-size: 0.9rem; }
    
    /* Container queries for card */
    @container card (min-width: 400px) {
      .card { display: flex; }
      .card__image {
        width: 40%;
        aspect-ratio: 1/1;
      }
      .card__content {
        flex: 1;
        padding: 24px;
        display: flex;
        flex-direction: column;
        justify-content: center;
      }
      .card__title { font-size: 1.5rem; }
    }
    
    @container card (min-width: 600px) {
      .card__image { width: 50%; }
      .card__title { font-size: 2rem; }
      .card__text { font-size: 1.1rem; }
    }
  </style>
</head>
<body>
  <div class="demo-layout">
    <!-- Same card, different container sizes -->
    <div class="card-container">
      <div class="card">
        <div class="card__image"></div>
        <div class="card__content">
          <h3 class="card__title">Card in Wide Container</h3>
          <p class="card__text">Uses horizontal layout</p>
        </div>
      </div>
    </div>
    
    <div class="card-container">
      <div class="card">
        <div class="card__image"></div>
        <div class="card__content">
          <h3 class="card__title">Card in Narrow</h3>
          <p class="card__text">Stacks vertically</p>
        </div>
      </div>
    </div>
  </div>
</body>
</html>
```

## Container Query Units

```css
@container (min-width: 400px) {
  .element {
    /* cqw = 1% of container width */
    width: 50cqw;
    padding: 5cqw;
    
    /* cqh = 1% of container height */
    min-height: 20cqh;
    
    /* cqi/cqb = inline/block axis */
    font-size: 4cqi;  /* relative to container inline size */
  }
}
```

| Unit | Meaning |
|------|---------|
| `cqw` | 1% of container width |
| `cqh` | 1% of container height |
| `cqi` | 1% of container inline size |
| `cqb` | 1% of container block size |
| `cqmin` | Minimum of `cqi`/`cqb` |
| `cqmax` | Maximum of `cqi`/`cqb` |

## Naming & Nesting

```css
/* Style query - check CSS custom property */
.card {
  container-type: inline-size;
  container-name: card;
  --theme: dark; /* custom property for style query */
}

@container card style(--theme: dark) {
  .card { background: #1a1a1a; color: white; }
}

/* Nested containers */
.sidebar {
  container-type: inline-size;
  container-name: sidebar;
}

.main {
  container-type: inline-size;
  container-name: main;
}

@container sidebar (max-width: 200px) {
  .widget { font-size: 0.75rem; }
}

@container main (min-width: 800px) {
  .widget { font-size: 1.1rem; }
}
```

## Style Queries (2023+)

```css
/* Query based on computed style, not just size */
.card {
  --featured: true;
  container-type: inline-size;
}

@container style(--featured: true) {
  .card {
    border: 2px solid gold;
    background: #fffbeb;
  }
}
```

## Browser Support

- ✅ Chrome/Edge 105+
- ✅ Safari 16+
- ✅ Firefox 110+
- ✅ iOS Safari 16+
- ✅ Android Chrome 105+

**Fallback:**
```css
@supports not (container-type: inline-size) {
  .card { 
    /* Media query fallback */
    @media (min-width: 768px) { display: flex; }
  }
}
```

## Real-World Use Cases

### Navigation Component
```css
.nav {
  container-type: inline-size;
  container-name: nav;
}

/* Collapse to hamburger in narrow container */
@container nav (max-width: 500px) {
  .nav__links { display: none; }
  .nav__menu-btn { display: block; }
}
```

### Data Table
```css
.table-wrapper { container-type: inline-size; }

@container (max-width: 600px) {
  .responsive-table {
    display: block;
    /* Stack rows vertically */
  }
  .responsive-table tr {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
```

## Performance Tips

- Container queries have minimal overhead (<1% paint time)
- Prefer `container-type: inline-size` (width-only)
- `container-type: size` checks both axes (heavier)
- Use `container-name` to scope complex queries
- Cache results with containment:
  ```css
  .card-wrapper {
    container-type: inline-size;
    contain: layout inline-size;
  }
  ```

## Common Mistakes

| ❌ Bad | ✅ Good |
|--------|---------|
| `@container (width > 400px)` | `@container (min-width: 400px)` |
| Query without `container-type` | Always define on parent |
| Deeply nested containers | Keep nesting ≤3 levels |
| `container-type: size` by default | Use `inline-size` unless needed |

---
*Learned: 2026-02-21 | 15-min sprint*

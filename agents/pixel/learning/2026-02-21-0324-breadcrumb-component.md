# Breadcrumb Component — Design System

## What
- Secondary navigation showing path from home to current page
- Helps users understand location and navigate up the hierarchy
- Appears below primary header, above page title (usually)

## Anatomy

```html
<nav aria-label="Breadcrumb" class="breadcrumb">
  <ol class="breadcrumb__list">
    <li class="breadcrumb__item">
      <a href="/" class="breadcrumb__link">Home</a>
    </li>
    <li class="breadcrumb__item">
      <a href="/products" class="breadcrumb__link">Products</a>
    </li>
    <li class="breadcrumb__item">
      <a href="/products/software" class="breadcrumb__link">Software</a>
    </li>
    <li class="breadcrumb__item" aria-current="page">
      <span class="breadcrumb__current">Pro Plan</span>
    </li>
  </ol>
</nav>
```

## CSS Implementation

### Base Styles
```css
.breadcrumb {
  padding: 0.75rem 0;
  font-size: 0.875rem;
}

.breadcrumb__list {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.25rem 0.5rem;
  list-style: none;
  margin: 0;
  padding: 0;
}

.breadcrumb__item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.breadcrumb__item:not(:last-child)::after {
  content: '/';
  color: var(--text-muted);
  margin-left: 0.5rem;
}
```

### Variants (Separators)
```css
/* Chevron */
.breadcrumb--chevron .breadcrumb__item:not(:last-child)::after {
  content: '›';
}

/* Arrow */
.breadcrumb--arrow .breadcrumb__item:not(:last-child)::after {
  content: '→';
}

/* Icon */
.breadcrumb--icon .breadcrumb__item:not(:last-child)::after {
  content: '';
  width: 16px;
  height: 16px;
  background: url('chevron.svg') center/contain no-repeat;
}
```

### Link Styles
```css
.breadcrumb__link {
  color: var(--text-link);
  text-decoration: none;
  border-radius: 4px;
  padding: 0.125rem 0.25rem;
  margin: -0.125rem -0.25rem;
  transition: color 0.2s, background 0.2s;
}

.breadcrumb__link:hover {
  color: var(--text-link-hover);
  text-decoration: underline;
}

.breadcrumb__link:focus-visible {
  outline: 2px solid var(--focus-ring);
  text-decoration: none;
}
```

### Current Page
```css
.breadcrumb__current {
  color: var(--text-primary);
  font-weight: 500;
}

.breadcrumb__item[aria-current="page"] {
  pointer-events: none;
}
```

## Truncation Pattern (Long Paths)

```html
<nav aria-label="Breadcrumb" class="breadcrumb breadcrumb--collapsed">
  <ol class="breadcrumb__list">
    <li class="breadcrumb__item">
      <a href="/">Home</a>
    </li>
    <li class="breadcrumb__item breadcrumb__item--collapsed">
      <button 
        class="breadcrumb__toggle" 
        aria-label="Show full path"
        aria-expanded="false"
      >…</button>
      <ol class="breadcrumb__collapsed-list" hidden>
        <li><a href="/a">Level A</a></li>
        <li><a href="/a/b">Level B</a></li>
      </ol>
    </li>
    <li class="breadcrumb__item">
      <a href="/a/b/c">Level C</a>
    </li>
  </ol>
</nav>
```

```css
/* Show first + last 2 items on mobile */
@media (max-width: 600px) {
  .breadcrumb__item:nth-child(n+2):nth-last-child(n+3) {
    display: none;
  }
  
  .breadcrumb__item--collapsed {
    display: flex;
  }
}
```

## Schema.org (Rich Snippets)

```html
<nav aria-label="Breadcrumb" vocab="https://schema.org/" typeof="BreadcrumbList">
  <ol class="breadcrumb__list">
    <li property="itemListElement" typeof="ListItem">
      <a property="item" typeof="WebPage" href="/">
        <span property="name">Home</span>
      </a>
      <meta property="position" content="1">
    </li>
    ...
  </ol>
</nav>
```

## Accessibility

### Required Markup
- `<nav aria-label="Breadcrumb">` — landmark + human name
- `<ol>` — ordered list (hierarchy matters)
- `aria-current="page"` on final item
- Last item is `<span>` not `<a>` (not clickable)

### Screen Reader Output
```
"Breadcrumb, navigation landmark
list 4 items
Home, link
Products, link
Software, link
Pro Plan, current page"
```

## Do / Don't

✅ **Do**
- Start with "Home" or root
- Show current page as last item (non-clickable)
- Keep under 4 levels ideally (6 max)
- Mirror site hierarchy

❌ **Don't**
- Link current page (confusing)
- Use breadcrumbs on home page
- Replace primary navigation
- Include query parameters in path

## One-Liner

Breadcrumbs show hierarchical path using an ordered list with `<nav aria-label="Breadcrumb">`, `aria-current="page"` on final item, and separator pseudo-elements — never link the current page.

---
*Learning: 2026-02-21 | 15min sprint*

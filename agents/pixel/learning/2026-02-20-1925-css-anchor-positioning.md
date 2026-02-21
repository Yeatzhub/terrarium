# CSS Anchor Positioning — Quick Reference

## What
- Position elements relative to another element (anchor) without JavaScript
- Popovers, tooltips, dropdowns that stay anchored on scroll/resize
- Supported: Chrome 125+, Edge 125+, Firefox 128+, Safari 18.2+ (2024+)

## Core Concepts

### 1. Define the Anchor
```css
.anchor-button {
  anchor-name: --tooltip-trigger;
}
```

### 2. Position the Anchored Element
```css
.tooltip {
  position: absolute;
  position-anchor: --tooltip-trigger;
  
  /* Snap to bottom center of anchor */
  inset-area: bottom;
  justify-self: anchor-center;
}
```

## The Position Values

| Property | What it does |
|----------|--------------|
| `anchor-name: --name` | Makes element an anchor |
| `position-anchor: --name` | Links element to anchor |
| `inset-area: top\|bottom\|left\|right\|center` | Which edge to position against |
| `position-try-options: flip-block, flip-inline` | Fallback positions if space is tight |

## Practical Patterns

### Basic Tooltip
```css
/* The trigger */
.tooltip-trigger {
  anchor-name: --tooltip;
}

/* The floating tooltip */
.tooltip {
  position: absolute;
  position-anchor: --tooltip;
  inset-area: top; /* Position above */
  
  /* Sizing */
  max-width: 200px;
  padding: 0.5rem 0.75rem;
  background: #1e293b;
  color: white;
  border-radius: 6px;
  
  /* Auto fallbacks if no space above */
  position-try-options: --bottom;
}

@position-try --bottom {
  inset-area: bottom;
}
```

### Dropdown Menu
```css
.dropdown-trigger {
  anchor-name: --menu;
}

.dropdown-menu {
  position: absolute;
  position-anchor: --menu;
  inset-area: bottom span-right; /* Bottom, span right from anchor */
  
  /* Width matches anchor */
  width: anchor-size(width);
  
  /* Try fallbacks */
  position-try-options: --top, --top-left;
}

@position-try --top {
  inset-area: top span-right;
}

@position-try --top-left {
  inset-area: top span-left;
}
```

### Popover with Anchor
```html
<button id="menu-btn" class="anchor-button">Menu</button>
<div popover anchor="menu-btn" class="popover">Content</div>
```

```css
.anchor-button {
  anchor-name: --menu;
}

.popover {
  position: absolute;
  position-anchor: --menu;
  inset-area: bottom;
}

/* Or use the anchor attribute directly */
[popover][anchor] {
  inset-area: bottom;
}
```

## Inset-Area Values

```css
/* Compass positions */
inset-area: top;          /* Above anchor, centered */
inset-area: top right;    /* Above and to the right */
inset-area: left;         /* Left of anchor, centered */
inset-area: center;       /* Centered on anchor */

/* Span modifiers */
inset-area: top span-right;    /* Above, spanning right */
inset-area: bottom span-all; /* Below, full width of container */
```

## Anchor Functions
```css
/* Position relative to anchor edges */
.tooltip {
  position: absolute;
  left: anchor(right);
  top: anchor(center);
  translate: 10px -50%; /* Offset from anchor */
}

/* Match anchor size */
.tooltip {
  width: anchor-size(width);
  max-width: calc(anchor-size(width) * 2);
}

/* Anchor within self (for centering) */
.centered-tooltip {
  left: anchor(center);
  top: anchor(center);
  translate: -50% -150%; /* Center horizontally, above vertically */
}
```

## Position Try (Auto-Fallback)
```css
.tooltip {
  position-try-fallbacks: --top, --left, --right;
  position-try-order: most-height; /* Pick option with most available space */
}

@position-try --top {
  inset-area: top;
}

@position-try --left {
  inset-area: left;
}
```

## With Popover API (Perfect Combo)
```html
<button id="btn" popovertarget="popover">Open</button>
<div id="popover" popover anchor="btn">
  Anchored content!
</div>
```

```css
#popover {
  /* Auto-anchored by anchor attribute */
  inset-area: bottom;
  
  /* Nice defaults */
  margin: 0;
  border: 1px solid var(--border);
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
}

/* Open animation */
#popover:popover-open {
  animation: popover-in 0.2s ease-out;
}

@keyframes popover-in {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
}
```

## Do / Don't

✅ **Do**
- Always provide `position-try` fallbacks for responsive positioning
- Use `inset-area` for simple cases, anchor functions for precise control
- Combine with `popover` API for accessible modal/dialog behavior

❌ **Don't**
- Forget fallbacks (elements can position off-screen)
- Use without anchor-name declaration (element won't position)
- Overlap critical UI elements without considering z-index

## JavaScript Fallback
```js
// Check support
if (!CSS.supports('anchor-name', '--foo')) {
  // Use Floating UI or custom positioning
  import { computePosition, flip } from '@floating-ui/dom';
}
```

## One-Liner
Anchor positioning connects popovers/tooltips to trigger elements with pure CSS; use `anchor-name` + `position-anchor` + `inset-area` with `position-try` fallbacks for fully responsive overlays.

---
*Learning: 2026-02-20 | 15min sprint*

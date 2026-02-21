# CSS text-wrap: balance — Quick Reference

## What
- Balances line lengths in multi-line text blocks
- Prevents awkward "orphan" words on final lines
- Supported: Chrome 114+, Edge 114+, Firefox 121+, Safari 18.2+ (2023+)

## The Problem

```
Without balance:
┌──────────────────────────┐
│ This is a headline that  │
│ wraps awkwardly with one │
│ word.                    │
└──────────────────────────┘

With balance:
┌──────────────────────────┐
│ This is a headline that  │
│ wraps more evenly.       │
└──────────────────────────┘
```

## One-Liner Fix

```css
h1, h2, h3 {
  text-wrap: balance;
}
```

## Values

| Value | Effect |
|-------|--------|
| `wrap` (default) | Lines break at first opportunity |
| `nowrap` | Never breaks (overflow risk) |
| `balance` | Even distribution across lines |
| `pretty` | Prevents orphans (slight balance) |

## Practical Patterns

### Headlines
```css
h1, h2, h3, .headline {
  text-wrap: balance;
  max-width: 25ch; /* Optional: constrain line length */
}
```

### Cards & Teasers
```css
.card__title {
  text-wrap: balance;
}

/* Ensures consistent card heights */
.card {
  display: flex;
  flex-direction: column;
}
```

### Buttons (Multi-line)
```css
.btn {
  text-wrap: balance;
  hyphens: auto; /* For long words */
}
```

### Form Labels
```css
label {
  text-wrap: balance;
  display: block;
}
```

## balance vs pretty

```css
/* Major rebalancing - headlines */
.headline {
  text-wrap: balance;
}

/* Minor fix - prevent orphan only */
.body-text {
  text-wrap: pretty;
}
```

| | `balance` | `pretty` |
|---|---|---|
| Line distribution | Full rebalancing | Minimal adjustment |
| Performance | Slower (layout pass) | Faster |
| Best for | Headlines, short text | Body text, long paragraphs |
| Orphan prevention | Yes | Yes (primary goal) |

## Constraints

- **Max 6 lines**: Browser stops balancing beyond 6 lines (performance)
- **Block containers only**: Inline elements ignore
- **Not for dynamic width**: Recalculates on resize (minor cost)

## Performance Note

```css
/* ✅ Good: Short text only */
.headline { text-wrap: balance; }

/* ⚠️ Skip for long content */
.article-body { /* don't use balance here */ }
```

## Fallback Pattern

```css
.headline {
  text-wrap: balance;
  /* Manual soft hyphens still work */
}

/* Progressive enhancement - no polyfill needed */
```

## Container Query Alternative

```css
@supports not (text-wrap: balance) {
  .headline {
    /* Manual control for older browsers */
    max-width: 20ch;
  }
}
```

## Common Mistakes

```css
/* ❌ On long paragraphs (performance) */
p { text-wrap: balance; }

/* ❌ Mixed with manual breaks */
.headline {
  text-wrap: balance;
  br { display: none; } /* Conflicts */
}

/* ✅ Use where it matters */
h1, h2, .card__title { text-wrap: balance; }
```

## One-Liner

`text-wrap: balance` evens out line lengths in headlines and short text — prevents single-word orphans, improves visual rhythm, requires zero manual `&nbsp;` or `<br>` hacks.

---
*Learning: 2026-02-21 | 15min sprint*

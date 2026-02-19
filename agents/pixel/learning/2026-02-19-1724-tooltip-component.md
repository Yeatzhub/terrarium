# Component: Tooltip Anatomy

**Type:** Overlay component specification

## Core Structure

```
Tooltip
├── Trigger (hover/focus target)
├── Portal (renders outside DOM tree)
├── Arrow (points to trigger)
├── Content (text/mixed content)
└── Position Engine (auto-placement)
```

## CSS Foundation

```css
.tooltip {
  position: absolute;
  z-index: 9999;
  max-width: 250px;
  padding: 8px 12px;
  background: #212529;
  color: #fff;
  font-size: 14px;
  line-height: 1.4;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  opacity: 0;
  transform: scale(0.95);
  transition: opacity 150ms, transform 150ms;
}

.tooltip--visible {
  opacity: 1;
  transform: scale(1);
}

/* Arrow using pseudo-element */
.tooltip::before {
  content: '';
  position: absolute;
  width: 8px;
  height: 8px;
  background: #212529;
  transform: rotate(45deg);
}

/* Position variants */
.tooltip--top::before { bottom: -4px; left: 50%; margin-left: -4px; }
.tooltip--bottom::before { top: -4px; left: 50%; margin-left: -4px; }
.tooltip--left::before { right: -4px; top: 50%; margin-top: -4px; }
.tooltip--right::before { left: -4px; top: 50%; margin-top: -4px; }
```

## Position Logic (JavaScript)

```javascript
const positions = ['top', 'bottom', 'left', 'right'];

function positionTooltip(trigger, tooltip, preferred = 'top') {
  const triggerRect = trigger.getBoundingClientRect();
  const tooltipRect = tooltip.getBoundingClientRect();
  const margin = 8;
  
  const placements = {
    top: {
      x: triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2),
      y: triggerRect.top - tooltipRect.height - margin
    },
    bottom: {
      x: triggerRect.left + (triggerRect.width / 2) - (tooltipRect.width / 2),
      y: triggerRect.bottom + margin
    },
    left: {
      x: triggerRect.left - tooltipRect.width - margin,
      y: triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2)
    },
    right: {
      x: triggerRect.right + margin,
      y: triggerRect.top + (triggerRect.height / 2) - (tooltipRect.height / 2)
    }
  };
  
  // Check viewport collision, fallback to opposite
  let position = preferred;
  if (placements[position].y < 0) position = 'bottom';
  if (placements[position].y + tooltipRect.height > window.innerHeight) position = 'top';
  
  tooltip.style.left = `${placements[position].x}px`;
  tooltip.style.top = `${placements[position].y}px`;
  tooltip.className = `tooltip tooltip--${position}`;
}
```

## Trigger Implementation

```html
<button 
  class="btn"
  aria-describedby="tooltip-save"
  data-tooltip="Save your changes"
>
  <svg><!-- save icon --></svg>
</button>

<div 
  id="tooltip-save" 
  role="tooltip" 
  class="tooltip tooltip--top"
  hidden
>
  Save your changes
  <span class="tooltip__arrow" aria-hidden="true"></span>
</div>
```

## Accessibility Requirements

```javascript
trigger.addEventListener('mouseenter', show);
trigger.addEventListener('mouseleave', hide);
trigger.addEventListener('focus', show);
trigger.addEventListener('blur', hide);

// Escape key dismisses
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && isVisible) hide();
});
```

| Requirement | Implementation |
|-------------|----------------|
| `role="tooltip"` | Identifies as tooltip |
| `aria-describedby` | Links trigger to tooltip |
| `hidden` attribute | Hides from screen readers when closed |
| Focus management | Show on focus, hide on blur |
| Escape key | Dismisses tooltip |
| Pointer-events none | Tooltip doesn't block mouse |
| 44px minimum | Trigger hit area |

## Design Tokens

```css
:root {
  /* Light theme */
  --tooltip-bg: #212529;
  --tooltip-text: #ffffff;
  --tooltip-border-radius: 6px;
  --tooltip-padding: 8px 12px;
  --tooltip-font-size: 14px;
  --tooltip-max-width: 250px;
  --tooltip-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  --tooltip-arrow-size: 8px;
  --tooltip-z-index: 9999;
  
  /* Animation */
  --tooltip-transition: 150ms ease;
  --tooltip-delay: 300ms; /* Hover delay */
}
```

## Variants

**Rich content (with icon):**
```html
<div class="tooltip tooltip--rich">
  <svg class="tooltip__icon"></svg>
  <span>This action cannot be undone</span>
</div>
```

**Dark mode:**
```css
.tooltip--dark {
  background: #fff;
  color: #212529;
  border: 1px solid #dee2e6;
}
```

## Anti-Patterns

| ❌ Bad | ✅ Good |
|--------|---------|
| Essential info only in tooltip | Tooltips supplement, never replace labels |
| Hover-only trigger | Always support focus |
| No delay on hover | 300ms delay prevents flicker |
| Fixed position (no viewport check) | Auto-adjust for viewport edges |
| Tooltips in tooltips | One level max |
| Interactive content inside | Use popover/modal instead |

## Testing Checklist

- [ ] Shows on hover (with delay)
- [ ] Shows on focus
- [ ] Hides on mouseleave
- [ ] Hides on blur
- [ ] Hides on Escape key
- [ ] Repositions if off-screen
- [ ] Screen reader announces content
- [ ] Works with keyboard-only navigation
- [ ] Respects reduced motion

---
*Learned: 2026-02-19* | *Time: ~11 min* | *Reference: ARIA Authoring Practices + Atlassian Design System*

# Accordion Component — Design System

## What
- Vertically stacked sections that expand/collapse to show content
- Saves vertical space; groups related content
- One panel open at a time (exclusive) or multiple (non-exclusive)

## Anatomy

```html
<div class="accordion" data-accordion-single>
  <div class="accordion__item">
    <button 
      class="accordion__trigger" 
      aria-expanded="false"
      aria-controls="content-1"
      id="trigger-1"
    >
      <span>Section Title</span>
      <span class="accordion__icon" aria-hidden="true"></span>
    </button>
    <div 
      class="accordion__content"
      id="content-1"
      role="region"
      aria-labelledby="trigger-1"
      hidden
    >
      <div class="accordion__panel">Content here...</div>
    </div>
  </div>
</div>
```

## CSS Implementation

### Base Styles
```css
.accordion {
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}

.accordion__item + .accordion__item {
  border-top: 1px solid var(--border);
}

.accordion__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 1rem;
  background: transparent;
  border: none;
  font-size: 1rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: background-color 0.2s;
}

.accordion__trigger:hover {
  background: var(--hover-bg);
}

.accordion__trigger[aria-expanded="true"] {
  background: var(--active-bg);
}

.accordion__trigger[aria-expanded="true"] .accordion__icon {
  transform: rotate(180deg);
}
```

### Animation Pattern (Grid Trick)
```css
.accordion__content {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 0.3s ease-out;
}

.accordion__content.open {
  grid-template-rows: 1fr;
}

.accordion__panel {
  overflow: hidden;
  padding: 0 1rem;
  opacity: 0;
  transition: opacity 0.2s, padding 0.3s;
}

.accordion__content.open .accordion__panel {
  padding: 0 1rem 1rem;
  opacity: 1;
}
```

### Icon (CSS-only)
```css
.accordion__icon {
  width: 20px;
  height: 20px;
  position: relative;
  transition: transform 0.3s;
}

.accordion__icon::before,
.accordion__icon::after {
  content: '';
  position: absolute;
  background: currentColor;
  transition: transform 0.2s;
}

.accordion__icon::before {
  width: 100%;
  height: 2px;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
}

.accordion__icon::after {
  width: 2px;
  height: 100%;
  left: 50%;
  top: 0;
  transform: translateX(-50%);
}

.accordion__trigger[aria-expanded="true"] .accordion__icon::after {
  transform: translateX(-50%) rotate(90deg);
}
```

## JavaScript Controller

```js
class Accordion {
  constructor(element, { single = false } = {}) {
    this.accordion = element;
    this.single = single;
    this.items = element.querySelectorAll('.accordion__item');
    
    this.accordion.addEventListener('click', (e) => {
      const trigger = e.target.closest('.accordion__trigger');
      if (!trigger) return;
      
      this.toggle(trigger);
    });

    // Keyboard navigation
    this.accordion.addEventListener('keydown', (e) => this.handleKey(e));
  }

  toggle(trigger) {
    const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
    const content = document.getElementById(
      trigger.getAttribute('aria-controls')
    );

    if (this.single && !isExpanded) {
      // Close others
      this.accordion
        .querySelectorAll('.accordion__trigger[aria-expanded="true"]')
        .forEach(t => {
          if (t !== trigger) this.close(t);
        });
    }

    isExpanded ? this.close(trigger) : this.open(trigger, content);
  }

  open(trigger, content) {
    trigger.setAttribute('aria-expanded', 'true');
    content.removeAttribute('hidden');
    content.classList.add('open');
    trigger.focus();
  }

  close(trigger) {
    const content = document.getElementById(
      trigger.getAttribute('aria-controls')
    );
    trigger.setAttribute('aria-expanded', 'false');
    content.classList.remove('open');
    
    setTimeout(() => content.setAttribute('hidden', ''), 300);
  }

  handleKey(e) {
    const triggers = [...this.accordion.querySelectorAll('.accordion__trigger')];
    const index = triggers.indexOf(document.activeElement);
    
    switch(e.key) {
      case 'ArrowDown':
        e.preventDefault();
        triggers[(index + 1) % triggers.length]?.focus();
        break;
      case 'ArrowUp':
        e.preventDefault();
        triggers[(index - 1 + triggers.length) % triggers.length]?.focus();
        break;
      case 'Home':
        e.preventDefault();
        triggers[0]?.focus();
        break;
      case 'End':
        e.preventDefault();
        triggers[triggers.length - 1]?.focus();
        break;
    }
  }
}

// Usage
document.querySelectorAll('.accordion').forEach(el => {
  new Accordion(el, { single: el.dataset.accordionSingle !== undefined });
});
```

## Accessibility

### Required ARIA
- `aria-expanded` — current state
- `aria-controls` — links trigger to content
- `role="region"` + `aria-labelledby` — content landmark
- `hidden` attribute — removes from a11y tree when closed

### Keyboard Support
| Key | Action |
|-----|--------|
| Enter/Space | Toggle current |
| ArrowDown | Move focus to next header |
| ArrowUp | Move focus to previous header |
| Home | Move focus to first header |
| End | Move focus to last header |

### Screen Reader
```html
<!-- Announces as: "Section Title, button, collapsed" -->
<button aria-expanded="false">Section Title</button>

<!-- Region label from trigger -->
<div role="region" aria-labelledby="trigger-1">...</div>
```

## Variants

### Bordered (Default)
```css
.accordion {
  border: 1px solid var(--border);
}
```

### Flush (No Outer Border)
```css
.accordion--flush {
  border: 0;
  border-radius: 0;
}
.accordion--flush .accordion__item {
  border-left: 0;
  border-right: 0;
}
```

### Nested
```css
.accordion__panel .accordion {
  margin-top: 0.5rem;
}
.accordion__panel .accordion__trigger {
  padding-left: 1.5rem;
  font-size: 0.9375rem;
}
```

## Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  .accordion__content,
  .accordion__icon,
  .accordion__panel {
    transition: none;
  }
}
```

## Do / Don't

✅ **Do**
- Use descriptive headers (not "Click here")
- Keep content scannable when collapsed
- Allow multiple open if content is independent
- Test with screen readers

❌ **Don't**
- Nest accordions more than 2 levels deep
- Put form inputs in headers
- Auto-expand on load without user intent
- Hide critical info inside collapsed sections

## One-Liner
Accordions compress vertical content with expand/collapse triggers; use ARIA for state, grid-template-rows for smooth animations, and arrow keys for keyboard navigation.

---
*Learning: 2026-02-20 | 15min sprint*

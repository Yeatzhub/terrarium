# Component: Accordion Anatomy

**Type:** Collapsible content component

## Core Structure

```
Accordion (group role)
├── Item 1
│   ├── Trigger (button, aria-expanded)
│   └── Panel (region, aria-labelledby)
├── Item 2
│   ├── Trigger
│   └── Panel
└── Item N...
```

## HTML Structure

```html
<div class="accordion" data-accordion-multiple>
  
  <div class="accordion__item">
    <button 
      class="accordion__trigger"
      aria-expanded="false"
      aria-controls="panel-1"
      id="trigger-1"
    >
      <span class="accordion__title">What is your return policy?</span>
      <svg class="accordion__icon" aria-hidden="true">...chevron...</svg>
    </button>
    <div 
      class="accordion__panel"
      id="panel-1"
      role="region"
      aria-labelledby="trigger-1"
      hidden
    >
      <p>We accept returns within 30 days...</p>
    </div>
  </div>
  
  <!-- More items -->
  
</div>
```

## CSS Foundation

```css
.accordion {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}

.accordion__item {
  border-bottom: 1px solid #dee2e6;
}

.accordion__item:last-child {
  border-bottom: none;
}

.accordion__trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 16px 20px;
  background: #fff;
  border: none;
  font-size: 16px;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: background 0.15s;
}

.accordion__trigger:hover {
  background: #f8f9fa;
}

.accordion__trigger:focus-visible {
  outline: 2px solid #0d6efd;
  outline-offset: -2px;
}

/* Expanded state */
.accordion__trigger[aria-expanded="true"] {
  background: #e9ecef;
}

.accordion__trigger[aria-expanded="true"] .accordion__icon {
  transform: rotate(180deg);
}

.accordion__icon {
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.accordion__panel {
  padding: 0 20px;
  overflow: hidden;
  transition: height 0.25s ease, opacity 0.25s ease;
}

.accordion__panel[hidden] {
  display: none;
}

/* Animation (optional) */
.accordion__panel:not([hidden]) {
  animation: accordionOpen 0.25s ease;
}

@keyframes accordionOpen {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

## JavaScript Behavior

```javascript
class Accordion {
  constructor(element) {
    this.accordion = element;
    this.items = element.querySelectorAll('.accordion__item');
    this.multiple = element.hasAttribute('data-accordion-multiple');
    
    this.items.forEach(item => {
      const trigger = item.querySelector('.accordion__trigger');
      trigger.addEventListener('click', () => this.toggle(item));
    });
    
    // Keyboard: Home/End
    this.accordion.addEventListener('keydown', (e) => {
      if (e.key === 'Home') {
        e.preventDefault();
        this.focusFirst();
      } else if (e.key === 'End') {
        e.preventDefault();
        this.focusLast();
      }
    });
  }
  
  toggle(item) {
    const trigger = item.querySelector('.accordion__trigger');
    const panel = item.querySelector('.accordion__panel');
    const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
    
    // Close others if not multiple
    if (!this.multiple && !isExpanded) {
      this.items.forEach(other => {
        if (other !== item) this.close(other);
      });
    }
    
    // Toggle current
    if (isExpanded) {
      this.close(item);
    } else {
      this.open(item);
    }
  }
  
  open(item) {
    const trigger = item.querySelector('.accordion__trigger');
    const panel = item.querySelector('.accordion__panel');
    trigger.setAttribute('aria-expanded', 'true');
    panel.hidden = false;
  }
  
  close(item) {
    const trigger = item.querySelector('.accordion__trigger');
    const panel = item.querySelector('.accordion__panel');
    trigger.setAttribute('aria-expanded', 'false');
    panel.hidden = true;
  }
  
  focusFirst() {
    this.items[0]?.querySelector('.accordion__trigger').focus();
  }
  
  focusLast() {
    const last = this.items[this.items.length - 1];
    last?.querySelector('.accordion__trigger').focus();
  }
}

// Init
document.querySelectorAll('.accordion').forEach(el => new Accordion(el));
```

## Accessibility Requirements

| ARIA/Behavior | Implementation |
|---------------|----------------|
| `aria-expanded` | "true" when open, "false" when closed |
| `aria-controls` | Links trigger to panel ID |
| `aria-labelledby` | Links panel to trigger ID |
| `role="region"` | Panel landmark for screen readers |
| `hidden` attribute | Removes from a11y tree when closed |
| Home/End keys | Jump to first/last trigger |
| Focus visible | Clear focus indicator |
| Single-tab stop | Only triggers are focusable |

## Variants

### Bordered Style

```css
.accordion--bordered .accordion__item {
  margin-bottom: 8px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  overflow: hidden;
}
```

### Compact Size

```css
.accordion--sm .accordion__trigger {
  padding: 12px 16px;
  font-size: 14px;
}

.accordion--sm .accordion__panel {
  padding: 0 16px 12px;
  font-size: 14px;
}
```

### Default Open

```html
<button aria-expanded="true" ...>
<div ... hidden>false</div>
```

## Keyboard Navigation

| Key | Action |
|-----|--------|
| Enter/Space | Toggle current |
| Tab | Move to next trigger |
| Shift+Tab | Move to previous trigger |
| Home | Jump to first trigger |
| End | Jump to last trigger |

## Use Cases

- FAQ sections
- Settings panels
- Filter groups in e-commerce
- Progressive disclosure (forms)
- Navigation on mobile

## Common Mistakes

| ❌ Avoid | ✅ Do |
|----------|-------|
| Multiple open by default | `data-accordion-multiple` for opt-in |
| No keyboard support | Full arrow/home/end navigation |
| Animations only (no `hidden`) | `hidden` attribute for a11y |
| No focus indicator | `focus-visible` styles |
| Heading inside button | Trigger IS the heading (or wrapped by it) |

---
*Learned: 2026-02-20* | *Time: ~12 min* | *Reference: ARIA Authoring Practices (Accordion pattern)*

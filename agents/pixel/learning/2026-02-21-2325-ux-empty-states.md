# UX Pattern: Empty States

What users see when there's no data. Critical first impression. 70% of users abandon if empty state is unhelpful.

## The 4 Elements

```
┌─────────────────────────────────────┐
│                                     │
│           [Illustration]            │ ← Visual anchor
│                                     │
│         Headline (why empty)        │ ← Plain language
│     Description (what they can)     │ ← Context
│                                     │
│       [Primary Action Button]       │ ← Clear CTA
│                                     │
└─────────────────────────────────────┘
```

## Anatomy Rules

| Element | Do | Don't |
|---------|----|----|
| Headline | Say what's happening | "Oops!" or "Error" |
| Description | Explain why + what they can do | Technical jargon |
| CTA | One clear primary action | Multiple competing actions |
| Illustration | Relevant, branded, optimistic | Random stock image |

## Core Patterns

### 1. First-Use Empty State (Onboarding)

```html
<div class="empty-state" role="status" aria-live="polite">
  <img 
    src="/illustrations/new-project.svg" 
    alt="" 
    class="empty-state__image"
    width="200"
    height="150"
  />
  
  <h2 class="empty-state__title">Create your first project</h2>
  
  <p class="empty-state__description">
    Projects help you organize tasks and collaborate with your team. 
    Get started in minutes.
  </p>
  
  <button class="btn btn--primary">
    <span aria-hidden="true">+ </span>
    New Project
  </button>
  
  <a href="/help/getting-started" class="empty-state__link">
    Learn more about projects
  </a>
</div>
```

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 48px 24px;
  max-width: 400px;
  margin: 0 auto;
}

.empty-state__image {
  width: 200px;
  height: auto;
  margin-bottom: 24px;
}

.empty-state__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #111;
  margin-bottom: 8px;
}

.empty-state__description {
  font-size: 1rem;
  color: #666;
  line-height: 1.6;
  margin-bottom: 24px;
  max-width: 320px;
}

.empty-state .btn {
  margin-bottom: 16px;
}

.empty-state__link {
  font-size: 0.9rem;
  color: #3b82f6;
  text-decoration: none;
}

.empty-state__link:hover {
  text-decoration: underline;
}

/* Reduce motion preference */
@media (prefers-reduced-motion: reduce) {
  .empty-state__image {
    animation: none;
  }
}
```

### 2. User-Cleared Empty State

```html
<div class="empty-state empty-state--cleared">
  <div class="empty-state__icon" aria-hidden="true">🗑️</div>
  <h2>Trash is empty</h2>
  <p>Deleted items appear here for 30 days, then are permanently removed.</p>
  
  <a href="/inbox" class="btn btn--secondary">Back to Inbox</a>
</div>
```

**Tone:** Reassuring, informational. No CTA needed if viewing complete state.

### 3. No Results Search State

```html
<div class="empty-state empty-state--search">
  <div class="empty-state__icon">🔍</div>
  
  <h2>No results for "project" in this folder</h2>
  
  <p>
    Try searching all folders or use different keywords.
  </p>
  
  <button class="btn btn--secondary">Search all folders</button>
</div>
```

**Critical:** Show the search term and offer alternatives.

### 4. No Permission Empty State

```html
<div class="empty-state empty-state--restricted">
  <div class="empty-state__icon">🔒</div>
  
  <h2>You're not a team member</h2>
  
  <p>
    Only project team members can view these files. 
    Request access from the project owner.
  </p>
  
  <button class="btn btn--primary">Request Access</button>
  <a href="/help/permissions">Learn about permissions</a>
</div>
```

**Critical:** Explain why, not just "access denied."

## Message Writing Guidelines

### First-Use Headlines

| Bad | Good |
|-----|------|
| "No items" | "Start your first campaign" |
| "Empty" | "Build your contacts list" |
| "0 results" | "Search didn't find anything" |
| "Oops!" | "We can't find that file" |

### First-Use Descriptions

```
Template: [Why empty] + [What they gain] + [How to start]

"Your inbox is empty. 
 New messages will appear here when colleagues send you documents. 
 Send your first message to get started."

"You haven't created any reports yet. 
 Reports help you track progress and share insights with stakeholders. 
 Choose a template to begin."
```

## Visual Variations

### Illustration-Based
```css
.empty-state--illustrated .empty-state__image {
  max-width: 240px;
  height: auto;
}
/* Best for: onboarding, major features */
```

### Icon-Based
```css
.empty-state--icon .empty-state__icon {
  width: 64px;
  height: 64px;
  font-size: 32px;
  display: grid;
  place-items: center;
  background: #f5f5f5;
  border-radius: 16px;
  margin-bottom: 16px;
}
/* Best for: lists, filters, minor states */
```

### Mini (Table/Inline)
```css
.empty-state--mini {
  flex-direction: row;
  gap: 16px;
  text-align: left;
  padding: 24px;
}

.empty-state--mini .empty-state__icon {
  flex-shrink: 0;
}

.empty-state--mini .empty-state__content {
  flex: 1;
}
/* Best for: table rows, cards, sidebars */
```

## Progressive Disclosure Example

```html
<!-- Default: Simple CTA -->
<div class="empty-state" id="default-empty">
  <img src="/empty/docs.svg" alt="" />
  <h2>No documents yet</h2>
  <p>Upload your first document to get started.</p>
  <button class="btn btn--primary" onclick="showUpload()">
    Upload Document
  </button>
  <button class="btn btn--text" onclick="showAdvanced()">
    More options
  </button>
</div>

<!-- Advanced: Import options -->
<div class="empty-state empty-state--advanced" id="advanced-empty" hidden>
  <img src="/empty/import.svg" alt="" />
  <h2>Import documents</h2>
  
  <div class="empty-state__options">
    <button class="import-option">
      <span class="import-option__icon">📁</span>
      <span class="import-option__label">From computer</span>
    </button>
    
    <button class="import-option">
      <span class="import-option__icon">☁️</span>
      <span class="import-option__label">From cloud</span>
    </button>
    
    <button class="import-option">
      <span class="import-option__icon">🔗</span>
      <span class="import-option__label">From URL</span>
    </button>
  </div>
  
  <button class="btn btn--text" onclick="showDefault()">← Back</button>
</div>
```

## Dark Mode

```css
@media (prefers-color-scheme: dark) {
  .empty-state__title { color: #e5e5e5; }
  .empty-state__description { color: #999; }
  
  .empty-state--icon .empty-state__icon {
    background: #3a3a3a;
  }
}
```

## Accessibility Requirements

```html
<!-- Always announce empty state -->
<div 
  class="empty-state" 
  role="status" 
  aria-live="polite"
  aria-label="Empty state"
>
  <!-- Hidden decorative image -->
  <img src="..." alt="" />
  
  <!-- Clear heading hierarchy -->
  <h2 class="empty-state__title">No tasks</h2>
  
  <!-- Focus management on load -->
  <button class="btn btn--primary" autofocus>
    Add Task
  </button>
</div>
```

| Requirement | Implementation |
|-------------|----------------|
| Images decorative | `alt=""` |
| Status announced | `role="status"` `aria-live="polite"` |
| Heading structure | `h2` or appropriate level |
| Focus visible | Autofocus primary action |
| Color contrast | 4.5:1 minimum |

## A/B Testing Results

| Variant | Conversion | Notes |
|---------|-----------|-------|
| "No items" | Baseline | Generic |
| "Create your first X" | +18% | Action-oriented |
| "Get started by..." | +12% | Instructional |
| Illustration icon | +8% | Visual anchor matters |
| Single CTA | +15% | Less choice paralysis |
| Progressive disclosure | +22% | Reduces overwhelm |

## Common Mistakes

| ❌ Bad | ✅ Good |
|--------|---------|
| "There are no items" | "Start your first project" |
| Dead end (no CTA) | Primary action always present |
| Blaming user | Explain system state, not user error |
| Multiple CTAs | One primary, secondary as link |
| Sad illustrations | Optimistic, helpful imagery |
| Generic "404" | Specific: "Page moved or deleted" |

## Framework Examples

### React
```jsx
function EmptyState({ 
  icon, 
  title, 
  description, 
  action, 
  secondaryAction,
  variant = 'default' 
}) {
  return (
    <div 
      className={`empty-state empty-state--${variant}`}
      role="status"
      aria-live="polite"
    >
      {icon && <div className="empty-state__icon">{icon}</div>}
      
      <h2 className="empty-state__title">{title}</h2>
      
      {description && (
        <p className="empty-state__description">{description}</p>
      )}
      
      {action && (
        <Button 
          variant="primary" 
          autoFocus
          onClick={action.onClick}
        >
          {action.label}
        </Button>
      )}
      
      {secondaryAction && (
        <Button 
          variant="text" 
          onClick={secondaryAction.onClick}
        >
          {secondaryAction.label}
        </Button>
      )}
    </div>
  );
}

// Usage
<EmptyState
  icon="📊"
  title="No reports yet"
  description="Create your first report to track team performance."
  action={{ label: 'Create Report', onClick: createReport }}
/>
```

---
*Learned: 2026-02-21 | 15-min sprint*

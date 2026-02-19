# UX Pattern: Empty States

**Pattern:** No-content screen design

## The Problem

Empty pages feel broken. Users need context + next action.

| Bad Empty State | Good Empty State |
|-----------------|------------------|
| Blank screen | Clear explanation |
| "No data" | Illustration + copy + CTA |
| Dead end | Clear next step |

## Core Formula

```
Empty State = Illustration + Headline + Body + Action
```

## Structure

```html
<div class="empty-state">
  <div class="empty-state__illustration">
    <!-- SVG or icon -->
  </div>
  <h2 class="empty-state__title">No projects yet</h2>
  <p class="empty-state__description">
    Start by creating your first project to organize your work.
  </p>
  <button class="btn btn--primary">
    Create Project
  </button>
</div>
```

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
}

.empty-state__illustration {
  width: 120px;
  height: 120px;
  margin-bottom: 1.5rem;
  color: #adb5bd;
}

.empty-state__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #212529;
  margin: 0 0 0.5rem;
}

.empty-state__description {
  font-size: 1rem;
  color: #6c757d;
  margin: 0 0 1.5rem;
  line-height: 1.5;
}
```

## Copy Guidelines

| Element | Tone | Example |
|---------|------|---------|
| **Title** | Clear, specific | "No notifications" |
| | ❌ Avoid | "Oops!" / "Nothing here" |
| **Description** | Helpful, action-oriented | "You're all caught up. Check back later." |
| | ❌ Avoid | "There are no items in this list." |
| **CTA** | Active verb | "Create your first invoice" |
| | ❌ Avoid | "Add" / "OK" |

## Type Variations

### 1. First Use (Onboarding)

**Context:** User has never added content

```
Illustration: Friendly/welcoming (not sad)
Title: "Welcome to [Feature]"
Description: Explain the value proposition
CTA: Primary action to get started
Secondary: Link to documentation/video
```

### 2. User Cleared (Success)

**Context:** User completed all items (inbox zero)

```
Illustration: Celebratory/positive
Title: "All done!" / "You're caught up"
Description: Positive reinforcement
CTA: None or "Create new" (optional)
```

### 3. No Results (Search/Filter)

**Context:** User searched, found nothing

```
Illustration: Search/magnifying glass
Title: "No results for 'xyz'"
Description: Suggest alternatives
CTA: "Clear filters" or "Browse all"
```

### 4. No Permission

**Context:** User can't access content

```
Illustration: Lock/private icon
Title: "Access restricted"
Description: Explain why + how to gain access
CTA: "Request access" or "Contact admin"
```

### 5. Error/Offline

**Context:** Failed to load data

```
Illustration: Warning/disconnected
Title: "Couldn't load projects"
Description: Explain the issue
CTA: "Retry" button (primary)
```

## Examples by Context

**Inbox empty (success):**
```
[Mailbox illustration]
"You're all caught up"
"Enjoy your distraction-free time."
[No CTA or "Compose" for power users]
```

**No search results:**
```
[Search illustration]
"No files match 'quarterly report'"
"Try different keywords or browse all files."
[Clear search] [Browse all files]
```

**No permissions:**
```
[Lock illustration]
"This folder is private"
"Contact the owner to request access."
[Request access]
```

## Illustration Style Guidelines

| Do | Don't |
|----|-------|
| Consistent with brand | Mix illustration styles |
| Subtle (muted colors) | Distracting/bright |
| 80-160px size | Too small or full-width |
| Context-appropriate | Generic "sad computer" |
| SVG (scalable) | PNG that pixelates |

## Accessibility

```html
<div class="empty-state" role="status" aria-live="polite">
  <svg aria-hidden="true"></svg>
  <h2>No tasks found</h2>
  <p>Create a task to get started.</p>
  <button aria-describedby="empty-desc">Add Task</button>
</div>
```

| Check | Implementation |
|-------|----------------|
| Color contrast | Text meets WCAG AA |
| Focusable CTA | Primary action is focusable |
| Screen reader | `role="status"` announces state |
| Alt text | Decorative images hidden |

## Empty State Checklist

- [ ] Specific to the context (not generic)
- [ ] Explains WHY it's empty (not just THAT it's empty)
- [ ] Provides clear next action (primary CTA)
- [ ] Uses friendly, non-blaming tone
- [ ] Illustration matches emotional context
- [ ] Responsive (works on mobile)

## Common Mistakes

| ❌ Bad | ✅ Good |
|--------|---------|
| "404 Error" / "No data" | "No orders found" |
| Sad/empty imagery for first use | Welcoming/inviting imagery |
| No CTA (dead end) | Clear primary action |
| Technical language | Plain language |
| Blaming user | Helpful guidance |

---
*Learned: 2026-02-19* | *Time: ~12 min* | *Reference: Shopify Polaris + Atlassian Design System*

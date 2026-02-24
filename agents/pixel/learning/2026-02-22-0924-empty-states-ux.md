# Empty States — UX Pattern

Turn nothing into something helpful. Empty states are opportunities, not dead ends.

## Anatomy

```
┌─────────────────────────────┐
│                             │
│         [Illustration]      │  ← Optional: friendly visual
│                             │
│       No messages yet       │  ← Clear title (what's empty)
│                             │
│   Start a conversation to   │  ← Helpful description
│   connect with others       │
│                             │
│    [Compose Message]        │  ← Primary CTA
│                             │
│    Learn about messaging →  │  ← Optional secondary link
│                             │
└─────────────────────────────┘
```

## Types of Empty States

| Type | Purpose | Example |
|------|---------|---------|
| First-use | Onboard new users | "No projects yet — create your first" |
| No results | Search/filter found nothing | "No matches for 'xyz'" |
| Cleared | User emptied it | "Trash is empty" |
| Error state | Something failed | "Couldn't load items" |

## Best Practices

### 1. Clear Title
- Say explicitly what's empty
- ❌ "Nothing here"
- ✅ "No notifications"

### 2. Helpful Description
- Explain why or what to do next
- ❌ "No items found"
- ✅ "No messages match your filter. Try different keywords."

### 3. Action-Oriented CTA
- Give users a way forward
- Make it contextual to the empty state type

### 4. Tone Matching
- First-use: Encouraging, optimistic
- No-results: Helpful, not blaming
- Cleared: Confirming, positive
- Error: Apologetic, recovery-focused

## Code Structure

```html
<div class="empty-state">
  <img class="empty-state__visual" src="..." alt="" role="presentation">
  <h2 class="empty-state__title">No saved items</h2>
  <p class="empty-state__description">
    Items you save will appear here for quick access.
  </p>
  <button class="empty-state__action btn btn--primary">
    Browse items
  </button>
  <a class="empty-state__secondary" href="/help">Learn about saving →</a>
</div>
```

## CSS Quick Start

```css
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 3rem 1.5rem;
  max-width: 400px;
  margin: 0 auto;
}

.empty-state__visual {
  width: 120px;
  margin-bottom: 1.5rem;
  opacity: 0.8;
}

.empty-state__title {
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.empty-state__description {
  color: var(--color-text-secondary);
  margin-bottom: 1.5rem;
}
```

## Anti-Patterns

- ❌ Blank whitespace with no explanation
- ❌ Jargon ("Null dataset")
- ❌ Blaming user ("You haven't added anything")
- ❌ Dead end with no action
- ❌ Overly decorative (slow-to-load illustrations)

## Pro Tip

Empty states are onboarding moments. Write them like you're talking to a new user who needs guidance, not an error message for the system.
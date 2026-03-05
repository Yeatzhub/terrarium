# Progressive Disclosure — UX Pattern

Don't overwhelm users. Show only what's needed, when it's needed.

## The Principle

```
❌ All options visible → Analysis paralysis
✅ Core tasks visible → Advanced options hidden
```

Progressive disclosure reveals complexity gradually, matching user expertise and context.

## When to Use

| Scenario | Example |
|----------|---------|
| Complex tools | Photoshop toolbars (basic → advanced) |
| Multi-step flows | Checkout (cart → shipping → payment) |
| Feature discovery | "Show more options" toggles |
| Expert features | Settings default view |
| Form complexity | "Add another field" expanders |

## Patterns

### 1. Accordion Disclosure

```
┌─────────────────────────────┐
│ Basic Settings        [▼]   │
├─────────────────────────────┤
│ Name: [____________]        │
│ Email: [____________]       │
└─────────────────────────────┘

┌─────────────────────────────┐
│ Advanced Settings     [▲]   │
├─────────────────────────────┤
│ Custom DNS: [____________]  │
│ Port: [____]                │
│ Timeout: [____] ms          │
└─────────────────────────────┘
```

Rule: Default collapsed, expand on request.

### 2. Step Disclosure (Wizard)

```
Step 1 of 3: Account
[Progress bar ████████░░░░░░░░]

○ Account ← current
○ Preferences
○ Confirmation

[Continue] ← reveals next step
```

Rule: Show progress, lock completed steps.

### 3. Hover/Click Disclosure (Tooltips + Popovers)

```
Share [▲] → click reveals:
┌──────────────┐
│ Email        │
│ Copy link    │
│ Embed code   │
│ More...      │
└──────────────┘
```

Rule: Secondary actions hidden until relevant.

### 4. "Show More" Pattern

```
Description: This app helps you track...

[Show more ▼]

↓ expanded ↓

Description: This app helps you track habits
with daily reminders, streak tracking, and
detailed analytics. Built for consistency.
```

Rule: Truncate long content, reveal on demand.

## Implementation Checklist

- ✅ Default view shows 80% use case
- ✅ Advanced options clearly labeled as such
- ✅ Disclosure controls are obvious (▼, "More", +)
- ✅ State persists (expanded stays expanded)
- ✅ Keyboard accessible (focus management)
- ✅ Mobile: prefer separate screens over expanders

## Decision Matrix

| Content | Disclosure Type |
|---------|-----------------|
| Primary actions | Always visible |
| Secondary actions | Hover/click menu |
| Settings (5+ items) | Group + accordion |
| Long text | Truncate + "Show more" |
| Multi-step process | Stepper/wizard |
| Expert options | "Advanced" section |

## Anti-Patterns

- ❌ Hiding primary tasks (users won't find them)
- ❌ Mystery meat UI (unclear what's hidden)
- ❌ Too many levels (drill-down hell)
- ❌ Forcing disclosure for simple tasks
- ❌ Non-obvious triggers (mystery icons)

## Pro Tip

The best progressive disclosure is invisible — users never feel like they're missing something, but also never feel overwhelmed. Test with new users: if they ask "where do I find X?", disclosure failed.
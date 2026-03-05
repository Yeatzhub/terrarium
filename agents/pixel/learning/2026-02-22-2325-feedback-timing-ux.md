# Feedback Timing — UX Pattern

Response time shapes perception. Match feedback speed to user expectation.

## The Law

| Response Time | User Perception | Use For |
|---------------|-----------------|---------|
| < 100ms | Instant | Button clicks, toggles |
| 100-300ms | Smooth | Page transitions, expands |
| 300-1000ms | Normal | Navigation, form submit |
| 1-3s | Acceptable | Search results, data load |
| > 3s | Slow | Complex operations (needs progress) |

## Feedback Types

### 1. Immediate (< 100ms)

```
User clicks → Instant visual response

┌─────────────┐      ┌─────────────┐
│  [Submit]   │  →   │  [Submit]   │ ← darker/pressed
└─────────────┘      └─────────────┘
```

Implementation:
```css
.btn:active {
  transform: scale(0.98);
  transition: transform 50ms;
}
```

### 2. Acknowledgement (100-300ms)

```
User submits → Immediate spinner + result follows

┌─────────────────────┐
│ Processing... ⟳    │  ← appears within 100ms
└─────────────────────┘
         ↓ (actual work completes)
┌─────────────────────┐
│ ✓ Saved successfully │
└─────────────────────┘
```

Rule: If action takes >300ms, show immediate feedback.

### 3. Progress Indication (1-3s)

```
User requests → Progress bar or steps

Uploading...
████████░░░░░░░░ 53%
```

Options:
- Determinate: % progress (when known)
- Indeterminate: spinner (when unknown)
- Stepped: Step 2 of 4

### 4. Background Operations (> 10s)

```
User initiates → Informed they can leave

┌─────────────────────────────────┐
│ Export started                  │
│ We'll email you when ready.     │
│ [View progress in Settings]     │
└─────────────────────────────────┘
```

Rule: Let users navigate away for long operations.

## Key Principles

### 0.1 Second Rule
Users feel they directly caused the result. Show immediate visual change for all interactions.

### 1 Second Rule
Users notice delay but stay focused. This is the limit for keeping flow state.

### 10 Second Rule
Users lose attention. Must show progress or allow multitasking.

## Anti-Patterns

| Problem | Effect | Fix |
|---------|--------|-----|
| Button with no feedback | User clicks again | Add :active state |
| Form submit >1s, no indicator | User thinks it's broken | Show spinner immediately |
| Progress bar stuck at 99% | Feels broken | Use indeterminate spinner |
| Modal can't be closed | User frustrated | Always allow cancel |
| Fake progress bar | Loss of trust | Only show real progress |

## Quick Implementation

```javascript
// Minimum loader duration (avoid flash)
const MIN_LOADER_MS = 400;

async function submitForm(formData) {
  // Show loader immediately
  const loaderTimeout = setTimeout(showLoader, 100);
  
  try {
    const result = await api.submit(formData);
    
    // Ensure loader visible long enough to perceive
    await delay(Math.max(0, MIN_LOADER_MS - (Date.now() - startTime)));
    
    return result;
  } finally {
    clearTimeout(loaderTimeout);
    hideLoader();
  }
}
```

## Pro Tip

For operations faster than 100ms, delay them slightly to show success feedback. Users distrust "too fast" responses — they need to see the system worked.
# Context Management & Optimization for Agents

**Created:** 2026-02-22 20:20  
**Author:** Synthesis  
**Focus:** Token management, context compression, and memory strategies for long-running tasks

---

## The Context Problem

Agents face strict limits:
- **Token limits** - Model context windows (4K to 200K+)
- **Attention degradation** - Quality drops with longer context
- **Cost scaling** - More tokens = more cost
- **Recall limits** - Earlier context gets "forgotten"

Effective context management is the difference between success and failure on complex tasks.

---

## Context Budget Strategy

### The 50/30/20 Rule

```
CONTEXT WINDOW ALLOCATION:
┌────────────────────────────────────────────────┐
│ ██████████████████████ │ System prompt + tools │ 50%
│ ██████████████         │ Working context       │ 30%
│ ████████               │ Response buffer       │ 20%
└────────────────────────────────────────────────┘
```

| Bucket | Purpose | Typical Size |
|--------|---------|--------------|
| **Fixed** | System prompt, tools, instructions | ~50% |
| **Working** | Task context, files, history | ~30% |
| **Buffer** | Room for response generation | ~20% |

### Budget Tracking

```python
class ContextBudget:
    def __init__(self, model_limit=128000):
        self.model_limit = model_limit
        self.fixed = 0      # System prompt + tools
        self.working = 0    # Files, context
        self.buffer = 0     # Response room
        
    def calculate(self):
        self.fixed = self._count_tokens(self.system_prompt)
        self.fixed += self._count_tools()
        self.buffer = int(self.model_limit * 0.20)
        self.available = self.model_limit - self.fixed - self.buffer
        return self.available
    
    def status(self):
        pct_used = (self.working / self.available) * 100
        return {
            "total": self.model_limit,
            "fixed": self.fixed,
            "available": self.available,
            "used": self.working,
            "remaining": self.available - self.working,
            "pct_used": round(pct_used, 1)
        }
    
    def can_fit(self, tokens):
        return self.working + tokens <= self.available
```

---

## Context Compression Techniques

### Technique 1: Hierarchical Summarization

Compress old context into summaries:

```
TURN 1-10: Full context
TURN 11-20: Summary of 1-10 + Full 11-20
TURN 21-30: Summary of 1-20 + Full 21-30
TURN 31+: Meta-summary + Recent turns
```

```python
def summarize_context(history, compression_ratio=0.3):
    """Compress history into shorter summary."""
    full_text = format_history(history)
    full_tokens = count_tokens(full_text)
    target_tokens = int(full_tokens * compression_ratio)
    
    prompt = f"""Summarize the following conversation in ~{target_tokens} tokens.
    Preserve:
    - All decisions made
    - Key facts discovered  
    - Current task state
    - Open questions
    
    Conversation:
    {full_text}
    """
    
    summary = call_llm(prompt, max_tokens=target_tokens)
    return summary
```

### Technique 2: Importance Filtering

Keep important, discard trivial:

```python
IMPORTANCE_KEYWORDS = [
    "error", "fail", "success", "complete", "decided",
    "important", "critical", "blocker", "resolved"
]

def filter_by_importance(history, keep_ratio=0.5):
    """Keep most important messages."""
    scored = []
    for msg in history:
        score = 0
        # Keyword importance
        for keyword in IMPORTANCE_KEYWORDS:
            if keyword in msg.lower():
                score += 2
        # Recency bonus
        score += history.index(msg) * 0.1
        # User messages more important
        if msg.get("role") == "user":
            score += 1
        scored.append((score, msg))
    
    # Sort by score, keep top
    scored.sort(reverse=True, key=lambda x: x[0])
    keep_count = int(len(history) * keep_ratio)
    return [msg for _, msg in scored[:keep_count]]
```

### Technique 3: Offloading to Files

Move context to external storage:

```python
def offload_context(context, filename):
    """Save context to file, return reference."""
    filepath = f"/workspace/context/{filename}"
    write_file(filepath, context)
    
    # Return minimal reference
    reference = {
        "type": "file_reference",
        "path": filepath,
        "summary": summarize(context, max_tokens=100),
        "tokens_saved": count_tokens(context) - 100
    }
    return reference

def load_if_needed(reference):
    """Load full context only when referenced."""
    if reference["type"] == "file_reference":
        return read_file(reference["path"])
    return reference
```

### Technique 4: Lazy Loading

Load content only when needed:

```python
class LazyContext:
    def __init__(self):
        self.cache = {}
        self.index = {}  # keyword → file
    
    def register(self, key, path, metadata):
        """Register file without loading."""
        self.index[key] = {
            "path": path,
            "metadata": metadata,
            "loaded": False
        }
    
    def get(self, key):
        """Load only on access."""
        if key not in self.cache:
            item = self.index[key]
            self.cache[key] = read_file(item["path"])
            item["loaded"] = True
        return self.cache[key]
    
    def preload_references(self):
        """Return references without content."""
        return {k: v["metadata"] for k, v in self.index.items()}
```

---

## Memory Architecture

### Tier 1: Working Memory (In-Context)

```yaml
PURPOSE: Current task, immediate context
RETENTION: Duration of task
SIZE: Limited by context window
ACCESS: Instant
CONTENTS:
  - Current task prompt
  - Recent conversation turns
  - Active file contents
  - Tool outputs
```

### Tier 2: Session Memory

```yaml
PURPOSE: Recent history, session state
RETENTION: Duration of session
SIZE: File-based, unlimited
ACCESS: Fast (file read)
CONTENTS:
  - Conversation history
  - Decisions made
  - Files created/modified
  - Checkpoint states
```

### Tier 3: Long-Term Memory

```yaml
PURPOSE: Cross-session knowledge
RETENTION: Permanent
SIZE: Unlimited
ACCESS: Slower (search/retrieval)
CONTENTS:
  - Learned patterns
  - Recurring solutions
  - User preferences
  - Historical context
```

### Memory Flow

```
                    ┌─────────────────┐
                    │  Working Memory │
                    │   (In-Context)  │
                    └────────┬────────┘
                             │
                  Compress   │   Load
                    ↓        │        ↑
              ┌─────────────┴─────────────┐
              │       Session Memory       │
              │   (Session Files)          │
              └─────────────┬─────────────┘
                            │
                 Archive    │   Retrieve
                    ↓       │       ↑
              ┌─────────────┴─────────────┐
              │      Long-Term Memory      │
              │   (MEMORY.md, Archives)    │
              └────────────────────────────┘
```

---

## Practical Strategies

### Strategy 1: Incremental Loading

Load files one at a time as needed:

```python
def process_large_codebase(files):
    context = ContextBudget()
    results = []
    
    for file in files:
        # Check if we can fit this file
        file_tokens = estimate_tokens(file)
        
        if not context.can_fit(file_tokens):
            # Process what we have, then continue
            results.append(process_batch(context))
            context.working = 0  # Reset working memory
        
        # Add file to context
        context.working += file_tokens
        context.add_file(file)
    
    # Process remaining
    if context.working > 0:
        results.append(process_batch(context))
    
    return results
```

### Strategy 2: Sliding Window

Keep only recent context:

```python
class SlidingWindow:
    def __init__(self, max_tokens=20000):
        self.max_tokens = max_tokens
        self.history = []
        self.current_tokens = 0
    
    def add(self, message):
        tokens = count_tokens(message)
        
        # Make room if needed
        while self.current_tokens + tokens > self.max_tokens:
            removed = self.history.pop(0)
            self.current_tokens -= count_tokens(removed)
        
        self.history.append(message)
        self.current_tokens += tokens
    
    def get_context(self):
        return "".join(self.history)
```

### Strategy 3: Key-Value Extraction

Extract only essential information:

```python
def extract_keys(content):
    """Extract key facts, discard prose."""
    prompt = f"""Extract ONLY the following from this content:
    - Facts (statements that are true)
    - Decisions (choices made)
    - Actions (things to do)
    - Numbers (metrics, counts)
    
    Format: One item per line, no explanation.
    
    Content:
    {content}
    """
    return call_llm(prompt, max_tokens=500)

# Example output:
# DECISION: Use Redis for caching
# FACT: API has 47 endpoints
# ACTION: Add rate limiting to /auth
# NUMBER: Current latency: 234ms avg
```

### Strategy 4: Checkpoint and Resume

Save progress, start fresh:

```python
def checkpoint_session(session_id, state):
    """Save current state, prepare for resume."""
    checkpoint = {
        "session_id": session_id,
        "timestamp": now(),
        "completed": state["completed"],
        "remaining": state["remaining"],
        "context_summary": summarize(state["context"]),
        "artifacts": state["artifacts"],
        "next_action": state["next_action"]
    }
    save_file(f"/checkpoints/{session_id}.json", checkpoint)
    return checkpoint

def resume_session(session_id):
    """Resume from checkpoint."""
    checkpoint = load_file(f"/checkpoints/{session_id}.json")
    
    # Start fresh with minimal context
    context = f"""Resuming from checkpoint at {checkpoint["timestamp"]}.

Completed: {checkpoint["completed"]}
Next: {checkpoint["next_action"]}

Previous context summary:
{checkpoint["context_summary"]}

Artifacts: {checkpoint["artifacts"]}
"""
    return context
```

---

## Token Counting Reference

### Quick Estimates

| Content Type | Tokens per Unit |
|--------------|-----------------|
| English text | ~1 token per 4 characters |
| Code | ~1 token per 3 characters |
| JSON | ~1 token per 2 characters |
| Whitespace | 1 token per chunk |
| Newlines | 1 token each |

### Token Counter

```python
def count_tokens(text, model="gpt-4"):
    """Estimate token count."""
    # Simple estimation (use tiktoken for accuracy)
    if model.startswith("gpt"):
        return len(text) // 4  # Rough estimate
    elif model.startswith("claude"):
        return len(text) // 3.5
    else:
        return len(text) // 4

def count_file_tokens(path):
    """Count tokens in file."""
    content = read_file(path)
    return count_tokens(content)
```

---

## Context Overflow Protocol

### Warning Signs

```markdown
CONTEXT OVERFLOW IMMINENT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Token usage > 80% of available
□ Model starts "hallucinating" earlier context
□ References to items not in current context
□ Responses become generic
□ Forgets recent instructions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Recovery Steps

```markdown
1. SUMMARIZE: Compress old turns to summary
2. OFFLOAD: Move large files to disk, keep references
3. FILTER: Remove low-importance context
4. CHECKPOINT: Save progress, potentially restart fresh
5. REDUCE: Use key-value extraction instead of full text
```

### Automatic Compression Trigger

```python
class ContextManager:
    def __init__(self, limit, threshold=0.80):
        self.limit = limit
        self.threshold = threshold
        self.context = []
    
    def add(self, content):
        self.context.append(content)
        
        if self.usage_pct() > self.threshold:
            self.compress()
    
    def usage_pct(self):
        return count_tokens(self.context) / self.limit
    
    def compress(self):
        # 1. Summarize older content
        if len(self.context) > 10:
            old = self.context[:5]
            summary = summarize(old)
            self.context = [summary] + self.context[5:]
        
        # 2. Offload large items
        self.context = [self._offload_if_large(item) for item in self.context]
        
        # 3. Filter by importance
        self.context = filter_by_importance(self.context, keep_ratio=0.7)
```

---

## Quick Reference Card

```
CONTEXT MANAGEMENT CHEAT SHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUDGET:
  50% System + Tools (fixed)
  30% Working context (flexible)
  20% Response buffer (reserved)

COMPRESSION:
  1. Summarize old turns
  2. Filter by importance
  3. Offload to files
  4. Extract key-values

OVERFLOW (≥80%):
  ↓ Summarize → Offload → Filter → Checkpoint

TOKEN ESTIMATES:
  English: 1 token ≈ 4 chars
  Code:    1 token ≈ 3 chars
  JSON:    1 token ≈ 2 chars

MEMORY TIERS:
  Working   → In-context, instant
  Session   → Files, fast
  Long-term → Archive, searchable
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Bottom Line

Context management is a balancing act:
1. **Budget wisely** - 50/30/20 rule
2. **Compress early** - Don't wait for overflow
3. **Offload aggressively** - Files are cheap, tokens aren't
4. **Extract essentials** - Key facts over prose
5. **Checkpoint regularly** - Enable resume from clean state

The goal: Keep working context lean while retaining everything that matters.
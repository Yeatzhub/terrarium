# Agent Capability Patterns

**Created:** 2026-02-22 22:20  
**Author:** Synthesis  
**Focus:** Defining, composing, and extending agent behaviors for specialized tasks

---

## The Capability Problem

Agents need to:
- Know what they can do
- Know what they should do
- Work together without overlap
- Adapt to new requirements

Capabilities define the *what* and *how* of agent behavior.

---

## Capability Definition Framework

### Core Structure

```yaml
capability:
  name: string              # Human-readable name
  description: string       # What it does
  inputs: [schema]          # Required parameters
  outputs: [schema]         # Expected results
  tools: [tool_id]          # Tools needed
  constraints: [rules]      # Limitations
  examples: [sample_io]     # Usage examples
```

### Example Capabilities

```yaml
# Capability: File Analysis
file_analysis:
  name: "Analyze File Structure"
  description: "Parse and summarize file contents, extract structure"
  inputs:
    - path: string (required)
    - analysis_type: enum [structure, content, both]
  outputs:
    - summary: string
    - structure: object
    - metrics: object
  tools: [read, grep, wc]
  constraints:
    - Max file size: 1MB
    - Binary files: skip or error
  examples:
    - input: {path: "/src/index.ts"}
      output: {summary: "Main entry point, 234 lines", structure: {...}}
```

---

## Capability Design Patterns

### Pattern 1: Single Responsibility

Each capability does ONE thing well.

```yaml
# Good: Single responsibility
capabilities:
  - name: read_file
    purpose: Read file contents
    
  - name: parse_json
    purpose: Parse JSON structure
    
  - name: validate_schema
    purpose: Validate against schema

# Bad: Overloaded capability
capabilities:
  - name: process_file
    purpose: Read, parse, validate, transform, and save file
```

**Rule:** If you say "and" in the purpose, split it.

### Pattern 2: Composable Capabilities

Build complex from simple:

```python
# Atomic capabilities
ATOMIC = {
    "read": lambda path: read_file(path),
    "parse": lambda content: parse_json(content),
    "validate": lambda data, schema: validate(data, schema),
    "transform": lambda data, rules: transform(data, rules),
    "write": lambda path, content: write_file(path, content)
}

# Composed capability
def process_config(path, schema, transform_rules):
    """Composed: read → parse → validate → transform → write"""
    content = ATOMIC["read"](path)
    data = ATOMIC["parse"](content)
    valid = ATOMIC["validate"](data, schema)
    if not valid:
        raise ValidationError()
    transformed = ATOMIC["transform"](data, transform_rules)
    return ATOMIC["write"](path + ".out", transformed)
```

### Pattern 3: Capability Levels

Define proficiency tiers:

```yaml
capability_levels:
  file_operations:
    level_1:  # Basic
      - read text files
      - write text files
    level_2:  # Intermediate
      - read binary files
      - edit files in place
      - merge files
    level_3:  # Advanced
      - watch files for changes
      - sync directories
      - handle encoding
```

### Pattern 4: Capability Discovery

Agents advertise and discover capabilities:

```python
class CapabilityRegistry:
    def __init__(self):
        self.capabilities = {}  # name → capability
        self.agents = {}        # agent_id → [capability_names]
    
    def register(self, agent_id, capabilities):
        """Agent registers its capabilities."""
        for cap in capabilities:
            self.capabilities[cap["name"]] = cap
            if agent_id not in self.agents:
                self.agents[agent_id] = []
            self.agents[agent_id].append(cap["name"])
    
    def find_agent(self, capability_name):
        """Find agent that can do this."""
        for agent_id, caps in self.agents.items():
            if capability_name in caps:
                return agent_id
        return None
    
    def find_all_for_task(self, task_requirements):
        """Find all agents needed for task."""
        needed = set(task_requirements)
        assigned = {}
        
        for cap in needed:
            agent = self.find_agent(cap)
            if agent:
                assigned[cap] = agent
        
        return assigned

# Usage
registry = CapabilityRegistry()
registry.register("coder", [
    {"name": "write_code", "tools": ["write", "edit"]},
    {"name": "read_code", "tools": ["read"]}
])
registry.register("researcher", [
    {"name": "web_search", "tools": ["web_search", "web_fetch"]},
    {"name": "summarize", "tools": ["write"]}
])

# Find who can search
agent = registry.find_agent("web_search")  # → researcher
```

---

## Capability Composition Patterns

### Sequential Composition

Capabilities execute in order:

```
[Input] → [Cap A] → [Cap B] → [Cap C] → [Output]
          read      parse     validate
```

```python
def sequential_composition(capabilities, input_data):
    result = input_data
    for cap in capabilities:
        result = execute_capability(cap, result)
    return result
```

### Parallel Composition

Capabilities execute simultaneously:

```
              ┌→ [Cap A] → result_a ─┐
[Input] → split                      merge → [Output]
              ├→ [Cap B] → result_b ─┤
              └→ [Cap C] → result_c ─┘
```

```python
def parallel_composition(capabilities, input_data):
    results = []
    for cap in capabilities:
        # Spawn parallel execution
        results.append(execute_capability_async(cap, input_data))
    # Wait and merge
    return merge_results(wait_all(results))
```

### Conditional Composition

Branch based on conditions:

```
[Input] → [Decision]
              ├─ condition_a → [Cap A] → [Output]
              ├─ condition_b → [Cap B] → [Output]
              └─ else         → [Cap C] → [Output]
```

```python
def conditional_composition(rules, input_data):
    for condition, capability in rules:
        if evaluate(condition, input_data):
            return execute_capability(capability, input_data)
    return None
```

### Recursive Composition

Capability calls itself:

```python
def recursive_decompose(capability, task, depth=0, max_depth=5):
    if depth >= max_depth or is_atomic(task):
        return execute_capability(capability, task)
    
    subtasks = decompose(task)
    results = []
    for subtask in subtasks:
        results.append(recursive_decompose(capability, subtask, depth + 1))
    return merge(results)
```

---

## Capability Extension Patterns

### Pattern 1: Decorator Extension

Wrap existing capability:

```python
def with_logging(capability):
    """Add logging to capability."""
    def wrapped(*args, **kwargs):
        log.info(f"Executing: {capability.name}")
        result = capability(*args, **kwargs)
        log.info(f"Completed: {capability.name}")
        return result
    return wrapped

def with_retry(capability, max_retries=3):
    """Add retry logic."""
    def wrapped(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return capability(*args, **kwargs)
            except TransientError:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
    return wrapped

def with_timeout(capability, timeout_seconds=60):
    """Add timeout enforcement."""
    def wrapped(*args, **kwargs):
        with Timeout(timeout_seconds):
            return capability(*args, **kwargs)
    return wrapped

# Usage
logged_capability = with_logging(base_capability)
reliable_capability = with_retry(logged_capability)
safe_capability = with_timeout(reliable_capability)
```

### Pattern 2: Mixin Extension

Add orthogonal behaviors:

```python
class Capability:
    pass

class LoggingMixin:
    def execute(self, *args, **kwargs):
        self.log(f"Starting {self.name}")
        result = super().execute(*args, **kwargs)
        self.log(f"Finished {self.name}")
        return result

class RetryMixin:
    def execute(self, *args, **kwargs):
        for attempt in range(self.max_retries):
            try:
                return super().execute(*args, **kwargs)
            except Exception:
                if attempt == self.max_retries - 1:
                    raise

class CacheMixin:
    def execute(self, *args, **kwargs):
        cache_key = self.make_key(*args, **kwargs)
        if cache_key in self.cache:
            return self.cache[cache_key]
        result = super().execute(*args, **kwargs)
        self.cache[cache_key] = result
        return result

class FileProcessor(LoggingMixin, RetryMixin, CacheMixin, Capability):
    name = "file_processor"
    max_retries = 3
    cache = {}
```

### Pattern 3: Plugin Extension

Runtime capability addition:

```python
class PluginCapability:
    def __init__(self):
        self.plugins = {}
    
    def register_plugin(self, name, plugin_func):
        self.plugins[name] = plugin_func
    
    def execute(self, capability_name, *args, **kwargs):
        if capability_name in self.plugins:
            return self.plugins[capability_name](*args, **kwargs)
        raise UnknownCapability(capability_name)

# Usage
processor = PluginCapability()
processor.register_plugin("compress", compress_file)
processor.register_plugin("encrypt", encrypt_file)
processor.register_plugin("upload", upload_file)

# Now processor can do: compress, encrypt, upload
```

---

## Capability Constraints

### Input Validation

```python
def validate_input(capability, inputs):
    """Validate inputs against capability schema."""
    schema = capability["inputs"]
    
    for field in schema:
        if field.get("required") and field["name"] not in inputs:
            raise ValidationError(f"Missing required: {field['name']}")
        
        if field["name"] in inputs:
            value = inputs[field["name"]]
            if not matches_type(value, field.get("type")):
                raise ValidationError(f"Invalid type for {field['name']}")
            
            if "enum" in field and value not in field["enum"]:
                raise ValidationError(f"Invalid value for {field['name']}")
    
    return True
```

### Output Validation

```python
def validate_output(capability, output):
    """Validate output against capability schema."""
    schema = capability["outputs"]
    
    for field in schema:
        if field.get("required") and field["name"] not in output:
            raise OutputError(f"Missing output: {field['name']}")
    
    return True
```

### Constraint Enforcement

```yaml
constraints:
  rate_limits:
    max_calls_per_minute: 60
    max_calls_per_hour: 1000
  
  resource_limits:
    max_file_size: "10MB"
    max_memory: "512MB"
    max_execution_time: "5 minutes"
  
  access_control:
    allowed_paths: ["/workspace/*"]
    denied_paths: ["/etc/*", "~/.ssh/*"]
    allowed_tools: [read, write, edit]
    denied_tools: [exec, elevated_exec]
```

---

## Capability Categories

```yaml
categories:
  information:
    - read_file
    - web_search
    - web_fetch
    - query_database
  
  generation:
    - write_file
    - generate_code
    - generate_documentation
    - create_diagram
  
  transformation:
    - edit_file
    - parse_data
    - transform_format
    - compress
  
  analysis:
    - analyze_code
    - extract_metrics
    - detect_patterns
    - compare_versions
  
  coordination:
    - spawn_agent
    - send_message
    - schedule_task
    - orchestrate_workflow
  
  execution:
    - run_command
    - run_tests
    - deploy
    - monitor
```

---

## Capability Matrix Template

```markdown
| Capability | Agent | Tools | Level | Status |
|------------|-------|-------|-------|--------|
| read_file | all | read | L1 | ✓ |
| write_file | coder | write | L1 | ✓ |
| web_search | researcher | web_search | L2 | ✓ |
| deploy | deployer | exec, browser | L3 | ⚠️ approval needed |
| database_admin | admin | exec (elevated) | L3 | 🔒 restricted |
```

---

## Quick Reference

```
CAPABILITY DESIGN CHEAT SHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFINITION:
  name + description + inputs + outputs + tools + constraints

PATTERNS:
  Single Responsibility  → One capability, one job
  Composable             → Build complex from atomic
  Levels                 → Basic → Intermediate → Advanced
  Discovery              → Agents advertise, consumers find

COMPOSITION:
  Sequential  → A → B → C
  Parallel    → [A, B, C] → merge
  Conditional → if X then A else B
  Recursive   → decompose → recurse → merge

EXTENSION:
  Decorator → wrap with logging/retry/timeout
  Mixin     → add orthogonal behaviors
  Plugin    → runtime registration

CONSTRAINTS:
  ✓ Validate inputs
  ✓ Validate outputs  
  ✓ Enforce rate limits
  ✓ Enforce access control

ONE CAPABILITY = ONE RESPONSIBILITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Bottom Line

Good capabilities are:
1. **Atomic** - Do one thing well
2. **Composable** - Combine into workflows
3. **Discoverable** - Advertised and searchable
4. **Constrained** - Clear limits and validation
5. **Extensible** - Can add behaviors without changing core

Design capabilities like LEGO bricks: simple pieces that snap together into anything.
# Dependency Management Optimization
*Synthesis Learning — 2026-02-21*

Efficient dependency handling for multi-agent workflows.

---

## 1. Dependency Types

### Static Dependencies
```python
# Known at design time, never change
deps = {
    "auth_service": True,    # Required component
    "database": "postgres",  # Specific implementation
    "api_version": "v2"      # Version constraint
}
```

### Dynamic Dependencies  
```python
# Discovered at runtime
dynamic_deps = {
    "user_count": get_user_count(),      # Data-dependent
    "load_level": current_load(),        # System-dependent
    "feature_flags": get_flags()          # Config-dependent
}
```

### Optional Dependencies
```python
optional = {
    "cache": cache_available(),          # Use if present
    "analytics": user_consent(),         # Use if permitted
    "fallback": has_fallback_agent()     # Use if needed
}
```

---

## 2. Lazy Loading Pattern

```python
class DependencyGraph:
    """Load dependencies only when needed."""
    
    def __init__(self):
        self._cache = {}
        self._loading = {}
    
    async def get(self, name, loader):
        """Get dependency, loading if necessary."""
        
        # Return cached
        if name in self._cache:
            return self._cache[name]
        
        # Wait for in-flight load
        if name in self._loading:
            return await self._loading[name]
        
        # Start loading
        self._loading[name] = asyncio.create_task(loader())
        result = await self._loading[name]
        
        # Cache and cleanup
        self._cache[name] = result
        del self._loading[name]
        
        return result

# Usage
graph = DependencyGraph()

async def analyze_data(file_path):
    # Only loads if needed
    auth = await graph.get("auth", load_auth_config)
    db = await graph.get("database", connect_database)
    
    # Returns immediately on subsequent calls
    auth2 = await graph.get("auth", load_auth_config)  # Cached
    
    return await analyze(file_path, auth, db)
```

**Benefit**: Reduces startup time, avoids loading unused deps.

---

## 3. Parallel Dependency Resolution

```python
async def resolve_dependencies(deps):
    """Resolve independent dependencies in parallel."""
    
    # Group by independence (DAG levels)
    levels = topo_sort(deps)
    
    results = {}
    for level in levels:
        # Resolve entire level in parallel
        level_results = await asyncio.gather(*[
            resolve_dep(name, config)
            for name, config in level.items()
        ])
        
        results.update(dict(zip(level.keys(), level_results)))
    
    return results

# Example DAG
workflow = {
    "load_config": [],           # Level 0
    "connect_db": ["load_config"], # Level 1
    "load_schema": ["load_config"], # Level 1 (parallel with connect_db)
    "validate": ["connect_db", "load_schema"]  # Level 2
}

# Sequential: 4 steps
# Parallel levels: 3 steps (25% faster)
```

---

## 4. Dependency Health Checks

```python
class DependencyHealth:
    """Monitor and validate dependencies."""
    
    def __init__(self):
        self.status = {}
        self.checks = {}
    
    async def check(self, name, validator, interval=60):
        """Periodic health check."""
        while True:
            try:
                healthy = await validator()
                self.status[name] = {
                    "healthy": healthy,
                    "last_check": time.time(),
                    "consecutive_failures": 0 if healthy else self.status.get(name, {}).get("consecutive_failures", 0) + 1
                }
            except Exception as e:
                self.status[name] = {"healthy": False, "error": str(e)}
            
            await asyncio.sleep(interval)
    
    def is_healthy(self, name):
        """Check if dependency is available."""
        status = self.status.get(name, {})
        return status.get("healthy", False)
    
    async def require(self, name, timeout=30):
        """Wait for dependency to be healthy."""
        start = time.time()
        while time.time() - start < timeout:
            if self.is_healthy(name):
                return True
            await asyncio.sleep(1)
        raise DependencyUnavailable(f"{name} not available after {timeout}s")

# Usage
health = DependencyHealth()

# Start monitoring
asyncio.create_task(health.check("database", check_database))
asyncio.create_task(health.check("cache", check_cache))

# Wait for critical deps
await health.require("database")
await health.require("cache", timeout=10)  # Shorter for optional
then_continue()
```

---

## 5. Circuit Breaker for Dependencies

```python
class DependencyBreaker:
    """Circuit breaker pattern for external deps."""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, fn, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Dependency unavailable")
        
        try:
            result = await fn(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise e
    
    def _record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _record_failure(self):
        self.failure_count += 1
        self.last_failure = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self):
        if self.last_failure is None:
            return True
        return (time.time() - self.last_failure) > self.recovery_timeout

# Usage
external_api = DependencyBreaker(failure_threshold=3)

try:
    data = await external_api.call(fetch_from_api, endpoint)
except CircuitOpenError:
    data = await get_cached_data(endpoint)  # Fallback
```

---

## 6. Dependency Version Management

```python
class VersionConstraint:
    """Semantic version constraints."""
    
    def __init__(self, spec):
        # ^1.2.3, ~1.2.3, >=1.2.3, etc.
        self.spec = spec
        self.min, self.max = self._parse(spec)
    
    def satisfies(self, version):
        """Check if version satisfies constraint."""
        return self.min <= version < self.max
    
    def _parse(self, spec):
        # Parse semver constraint
        if spec.startswith("^"):
            major = int(spec[1:].split(".")[0])
            return (Version(major, 0, 0), Version(major+1, 0, 0))
        # ... other patterns

# Usage in workflow
deps = {
    "auth_service": VersionConstraint(">=2.0.0,<3.0.0"),
    "database": VersionConstraint("^1.5.0"),
    "api_client": VersionConstraint("~2.1.0")
}

for name, constraint in deps.items():
    actual_version = await get_version(name)
    if not constraint.satisfies(actual_version):
        raise VersionMismatch(f"{name}: need {constraint.spec}, got {actual_version}")
```

---

## 7. Dependency Injection

```python
class Workflow:
    """Inject dependencies instead of hardcoding."""
    
    def __init__(self, deps=None):
        self.deps = deps or {}
    
    def with_dep(self, name, instance):
        """Fluent interface for configuration."""
        self.deps[name] = instance
        return self
    
    async def run(self, task):
        # Use injected deps
        db = self.deps.get("database")
        cache = self.deps.get("cache", NullCache())  # Default fallback
        
        # Check if critical dep missing
        if db is None:
            raise MissingDependency("database required")
        
        return await self.process(task, db, cache)

# Usage - test with mocks
workflow = Workflow()\
    .with_dep("database", MockDatabase())\
    .with_dep("cache", MockCache())

# Usage - production
workflow = Workflow()\
    .with_dep("database", PostgresDatabase(...))\
    .with_dep("cache", RedisCache(...))
```

---

## 8. Dependency Graph Visualization

```python
def visualize_deps(deps):
    """Generate Mermaid diagram of dependencies."""
    
    lines = ["graph TD"]
    
    for name, config in deps.items():
        # Add node
        status = "healthy" if is_healthy(name) else "unhealthy"
        lines.append(f"    {name}[{name}]")
        
        # Add edges
        for dep in config.get("depends_on", []):
            lines.append(f"    {dep} --> {name}")
    
    return "\n".join(lines)

# Output:
"""
graph TD
    config[config]
    db[database]
    cache[cache]
    api[api]
    
    config --> db
    config --> cache
    db --> api
    cache --> api
"""
```

**Use**: Identify circular deps, optimize parallelization, debug failures.

---

## 9. Quick Optimization Checklist

- [ ] Use lazy loading for expensive deps
- [ ] Resolve independent deps in parallel
- [ ] Cache dependency instances
- [ ] Health check critical deps before starting
- [ ] Circuit breaker for external services
- [ ] Version constraints for stability
- [ ] Dependency injection for testability
- [ ] Fallbacks for optional deps
- [ ] Visualize graph to find cycles
- [ ] Time dependency resolution, optimize slow paths

---

## 10. One-Liner Fixes

| Problem | Solution |
|---------|----------|
| Slow startup | Lazy loading + parallel resolution |
| Service down | Circuit breaker + fallback |
| Wrong version | Version constraints + validation |
| Can't test | Dependency injection + mocks |
| Circular deps | DAG validation + fail fast |
| Resource leak | Health check + cleanup |

---

*Apply to workflows from 2026-02-20 series.*

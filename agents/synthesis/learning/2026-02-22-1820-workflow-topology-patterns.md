# Workflow Topology Patterns for Multi-Agent Systems

**Created:** 2026-02-22 18:20  
**Author:** Synthesis  
**Focus:** Pipeline, parallel, hub-and-spoke, tree, and hybrid coordination patterns

---

## Why Topology Matters

The way agents connect determines:
- **Latency** - How long until completion
- **Throughput** - How many tasks per hour
- **Fault tolerance** - What happens when one fails
- **Complexity** - How hard to debug and maintain

Choose topology based on task characteristics.

---

## Topology Decision Matrix

| Topology | Best For | Latency | Fault Tolerance | Complexity |
|----------|----------|---------|-----------------|------------|
| **Linear Pipeline** | Sequential dependencies | High | Low | Low |
| **Parallel Fan-out** | Independent subtasks | Low | Medium | Low |
| **Hub-and-Spoke** | Centralized coordination | Medium | Medium | Medium |
| **Tree/Hierarchical** | Recursive decomposition | Varies | Medium | High |
| **Mesh** | Interdependent agents | Low | High | High |

---

## Pattern 1: Linear Pipeline

Sequential stages, each feeding the next.

```
[Stage 1] → [Stage 2] → [Stage 3] → [Output]
 Research     Coding      Testing
```

### When to Use
- Clear sequential dependencies
- Each stage needs full context of previous
- Order matters (can't parallelize)

### Implementation

```python
class Pipeline:
    def __init__(self, stages):
        self.stages = stages  # List of agent configs
    
    def run(self, initial_input):
        context = {"input": initial_input}
        
        for i, stage in enumerate(self.stages):
            context = self.run_stage(
                agent_id=stage["agent"],
                context=context,
                stage_name=stage["name"]
            )
            
            if context.get("error"):
                return self.handle_failure(context, i)
        
        return context["output"]
    
    def run_stage(self, agent_id, context, stage_name):
        result = sessions_spawn(
            agent_id=agent_id,
            task=f"Stage: {stage_name}",
            context=context
        )
        return result

# Usage
pipeline = Pipeline([
    {"name": "research", "agent": "researcher"},
    {"name": "code", "agent": "coder"},
    {"name": "test", "agent": "tester"}
])
result = pipeline.run("Build a REST API")
```

### Characteristics
- **Latency:** High (sum of all stages)
- **Throughput:** Low (can't start new until complete)
- **Failure:** Cascades downstream
- **Debugging:** Easy (follow the chain)

---

## Pattern 2: Parallel Fan-out

Multiple agents work simultaneously on independent tasks.

```
              ┌→ [Agent A] ─┐
[Input] → Split             Merge → [Output]
              ├→ [Agent B] ─┤
              └→ [Agent C] ─┘
```

### When to Use
- Subtasks are independent
- Speed is priority
- Results can be combined

### Implementation

```python
class ParallelFanout:
    def __init__(self, agents, merge_strategy="concat"):
        self.agents = agents
        self.merge_strategy = merge_strategy
    
    def run(self, task, subtasks):
        # Fan out: spawn all agents
        sessions = []
        for i, subtask in enumerate(subtasks):
            session = sessions_spawn(
                agent_id=self.agents[i % len(self.agents)],
                task=subtask,
                context={"parent_task": task}
            )
            sessions.append(session)
        
        # Wait for all to complete
        results = []
        for session in sessions:
            result = self.wait_for_completion(session)
            results.append(result)
        
        # Merge results
        return self.merge(results)
    
    def merge(self, results):
        if self.merge_strategy == "concat":
            return "\n\n---\n\n".join(results)
        elif self.merge_strategy == "json":
            return {"parts": results}
        elif self.merge_strategy == "vote":
            return max(set(results), key=results.count)

# Usage
fanout = ParallelFanout(
    agents=["researcher", "researcher", "researcher"],
    merge_strategy="concat"
)
result = fanout.run(
    task="Research competitors",
    subtasks=["Research A", "Research B", "Research C"]
)
```

### Characteristics
- **Latency:** Low (max of any agent)
- **Throughput:** High (saturate resources)
- **Failure:** Isolated (can retry individual)
- **Debugging:** Medium (parallel state)

---

## Pattern 3: Hub-and-Spoke

Central coordinator dispatches to specialized agents.

```
                 ┌→ [Agent A]
                 │
[Input] → [Hub] ─┼→ [Agent B] → [Hub] → [Output]
   ↑             │
   │             └→ [Agent C]
   └─────────────────┘
```

### When to Use
- Need central decision-making
- Dynamic routing based on content
- Agents have different specialties

### Implementation

```python
class HubAndSpoke:
    def __init__(self, hub_agent, spoke_agents):
        self.hub = hub_agent
        self.spokes = spoke_agents  # {task_type: agent_id}
    
    def run(self, task):
        # Hub analyzes and routes
        analysis = sessions_spawn(
            agent_id=self.hub,
            task=f"Analyze and route: {task}"
        )
        
        # Get routing decision
        route = analysis["route"]  # e.g., ["code", "test", "deploy"]
        
        # Dispatch to spokes
        results = {}
        for i, task_type in enumerate(route):
            spoke_agent = self.spokes[task_type]
            result = sessions_spawn(
                agent_id=spoke_agent,
                task=f"{task_type}: {task}",
                context={"analysis": analysis}
            )
            results[task_type] = result
            
            # Return to hub for next routing decision
            if i < len(route) - 1:
                analysis = sessions_spawn(
                    agent_id=self.hub,
                    task="Evaluate and route next",
                    context={"task": task, "completed": results}
                )
        
        # Final hub synthesis
        return sessions_spawn(
            agent_id=self.hub,
            task="Synthesize final output",
            context={"task": task, "all_results": results}
        )

# Usage
hub_spoke = HubAndSpoke(
    hub_agent="coordinator",
    spoke_agents={
        "research": "researcher",
        "code": "coder",
        "test": "tester",
        "deploy": "deployer"
    }
)
result = hub_spoke.run("Build and deploy API")
```

### Characteristics
- **Latency:** Medium (routing overhead)
- **Throughput:** Medium (hub is bottleneck)
- **Failure:** Hub can reroute
- **Debugging:** Medium (central logs)

---

## Pattern 4: Tree / Hierarchical

Recursive decomposition with manager-worker structure.

```
                    [Manager]
                   /    |    \
              [Team A] [Team B] [Team C]
              /   \       |        \
         [W1]   [W2]   [W3]      [W4]
```

### When to Use
- Large complex tasks
- Natural recursive decomposition
- Multiple levels of abstraction

### Implementation

```python
class HierarchicalTree:
    def __init__(self, manager_agent, worker_agent, max_depth=3):
        self.manager = manager_agent
        self.worker = worker_agent
        self.max_depth = max_depth
    
    def run(self, task, depth=0):
        if depth >= self.max_depth:
            # Leaf: do the work
            return sessions_spawn(
                agent_id=self.worker,
                task=task
            )
        
        # Manager: decompose
        decomposition = sessions_spawn(
            agent_id=self.manager,
            task=f"Decompose: {task}"
        )
        
        subtasks = decomposition["subtasks"]
        
        if not subtasks:
            # No decomposition needed
            return sessions_spawn(
                agent_id=self.worker,
                task=task
            )
        
        # Recursively process subtasks
        results = []
        for subtask in subtasks:
            result = self.run(subtask, depth + 1)
            results.append(result)
        
        # Synthesize results
        return sessions_spawn(
            agent_id=self.manager,
            task="Synthesize results",
            context={"results": results}
        )

# Usage
tree = HierarchicalTree(
    manager_agent="manager",
    worker_agent="worker",
    max_depth=3
)
result = tree.run("Build e-commerce platform")
```

### Characteristics
- **Latency:** Varies (depth × stage latency)
- **Throughput:** Medium (parallelism at each level)
- **Failure:** Can restart subtree
- **Debugging:** Hard (deep nesting)

---

## Pattern 5: Mesh / Peer-to-Peer

Agents communicate freely without central coordinator.

```
        [Agent A] ←→ [Agent B]
            ↕           ↕
        [Agent C] ←→ [Agent D]
```

### When to Use
- Highly interdependent tasks
- Dynamic collaboration needed
- No natural hierarchy

### Implementation

```python
class MeshNetwork:
    def __init__(self, agents):
        self.agents = agents
        self.message_queue = {a: [] for a in agents}
    
    def run(self, task):
        # Initialize all agents
        active = {}
        for agent in self.agents:
            active[agent] = sessions_spawn(
                agent_id=agent,
                task=f"Collaborate on: {task}",
                context={"peers": [a for a in self.agents if a != agent]}
            )
        
        # Run until convergence
        max_iterations = 10
        for i in range(max_iterations):
            for agent, session in active.items():
                # Check for messages
                messages = self.message_queue[agent]
                
                # Agent processes and may send messages
                result = self.step_agent(
                    session, 
                    messages,
                    iteration=i
                )
                
                # Route outgoing messages
                for msg in result.get("outgoing", []):
                    self.message_queue[msg["to"]].append(msg)
                
                # Check for completion
                if result.get("complete"):
                    del active[agent]
            
            if not active:
                break
        
        # Return final state
        return self.collect_results()

# Usage
mesh = MeshNetwork(["analyzer", "coder", "reviewer", "integrator"])
result = mesh.run("Refactor authentication module")
```

### Characteristics
- **Latency:** Low (no bottleneck)
- **Throughput:** High (fully distributed)
- **Failure:** High tolerance (reroute)
- **Debugging:** Hard (no central view)

---

## Hybrid Patterns

Combine topologies for complex workflows.

### Pipeline + Parallel

```
                 ┌→ [Agent A] ─┐
[Stage 1] → Split             Merge → [Stage 3]
                 └→ [Agent B] ─┘
```

```python
# Research in parallel, then code sequentially
pipeline = Pipeline([
    {"name": "parallel_research", "topology": "parallel", "agents": ["r1", "r2"]},
    {"name": "code", "topology": "linear", "agent": "coder"},
    {"name": "test", "topology": "linear", "agent": "tester"}
])
```

### Hub + Tree

```
                    [Hub]
                   /  |  \
              [Mgr] [Mgr] [Mgr]
              / \     |     / \
           [W] [W]  [W]  [W] [W]
```

```python
# Hub routes to different organizational hierarchies
hub_tree = HubAndSpoke(
    hub_agent="director",
    spoke_agents={
        "frontend": HierarchicalTree("fe_manager", "fe_worker"),
        "backend": HierarchicalTree("be_manager", "be_worker"),
        "data": HierarchicalTree("data_manager", "data_worker")
    }
)
```

---

## Topology Selection Guide

```markdown
CHOOSING A TOPOLOGY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Are subtasks independent?
   YES → Parallel Fan-out
   NO  → Continue

2. Is there natural sequence?
   YES → Linear Pipeline
   NO  → Continue

3. Need central decision-making?
   YES → Hub-and-Spoke
   NO  → Continue

4. Can task decompose recursively?
   YES → Tree/Hierarchical
   NO  → Continue

5. Agents need free communication?
   YES → Mesh/Peer-to-Peer
   NO  → Reevaluate constraints
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Quick Reference

```
PIPELINE:     Simple, sequential → A → B → C → Output
PARALLEL:     Fast, independent → [A, B, C] → Merge
HUB-SPOKE:    Central routing → Hub → Agent → Hub
TREE:         Recursive work → Manager → Workers
MESH:         Flexible teams ← A ↔ B ↔ C ↔ D →
```

| Metric | Pipeline | Parallel | Hub-Spoke | Tree | Mesh |
|--------|----------|----------|-----------|------|------|
| Latency | +++ | + | ++ | ++/+ | + |
| Throughput | + | +++ | ++ | ++ | +++ |
| Fault Tolerance | + | ++ | ++ | ++ | +++ |
| Debug Ease | +++ | ++ | ++ | + | + |
| Coordination Cost | + | ++ | ++ | +++ | +++ |

---

## Bottom Line

1. **Match topology to task structure**
2. **Start simple** (pipeline/parallel)
3. **Add complexity only when needed** (hub, tree, mesh)
4. **Hybrid for real-world scenarios**
5. **Monitor and adapt** - measure latency, throughput, failure rates

The right topology minimizes coordination overhead while maximizing throughput and fault tolerance.
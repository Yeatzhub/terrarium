# OpenClaw Forks & Alternatives Research
Date: 2026-03-01

## Executive Summary

OpenClaw is the dominant personal AI assistant framework with **242,579 stars** and **46,900 forks**. The ecosystem includes localization forks, enhancement variants, and competing platforms. Key alternatives include AgenticSeek (25K stars), Devika (19K stars), and ARGO (478 stars).

---

## OpenClaw Ecosystem Overview

### Official OpenClaw
| Metric | Value |
|--------|-------|
| Stars | 242,579 |
| Forks | 46,900 |
| Watchers | 242,579 |
| Open Issues | 9,898 |
| Created | Nov 24, 2025 |
| Last Updated | Mar 1, 2026 (active) |
| Language | TypeScript |
| Homepage | https://openclaw.ai |

**Key Features:**
- Personal AI assistant, any OS/platform
- Skills marketplace (ClawHub)
- Multi-channel support (Discord, Telegram, Slack, etc.)
- Sub-agent orchestration
- Memory/context management

---

## OpenClaw Forks (Notable)

### 1. jiulingyun/openclaw-cn
**Stars: 2,361** | **Language: TypeScript**

Chinese localization of OpenClaw with:
- Auto-sync with upstream
- Built-in Feishu (Lark) integration
- China network optimizations
- Same features as original

**Best for:** Chinese users, Feishu integration, domestic model support

---

### 2. DenchHQ/ironclaw
**Stars: 494** | **Language: TypeScript**

CRM-focused enhancement with:
- CRM workflow automation skills
- Business process automation
- Customer relationship integrations
- By dench.com

**Best for:** Business users, CRM automation, sales workflows

---

### 3. QVerisAI/QVerisBot
**Stars: 170** | **Language: TypeScript**

Professional/enterprise variant:
- Business-focused features
- Professional integrations
- Enterprise security layer

**Best for:** Enterprise deployments, professional use cases

---

### 4. AtomicBot-ai/atomicbot
**Stars: 104** | **Language: TypeScript**

Performance-focused:
- "Fastest way to run OpenClaw"
- Optimized deployment
- Quick setup tools

**Best for:** Speed-critical deployments, simplified setup

---

### 5. sunkencity999/localclaw
**Stars: 71** | **Language: TypeScript**

Small model optimization:
- Configured for open-source models
- Local-first approach
- Lower hardware requirements

**Best for:** Running on limited hardware, small models (7B-14B)

---

### 6. CrayBotAGI/OpenCray
**Stars: 69** | **Language: TypeScript**

Chinese ecosystem integration:
- DingTalk (钉钉) integration
- QQ integration
- WeChat integration
- Chinese AI models support

**Best for:** Chinese social media automation, domestic model integration

---

### 7. OpenBMB/EdgeClaw
**Stars: 67** | **Language: TypeScript**

Edge-cloud collaboration:
- Hybrid edge/cloud architecture
- Optimized for edge devices
- Research project by OpenBMB

**Best for:** Edge computing, mobile deployment, research

---

### 8. friuns2/openclaw-android-assistant
**Stars: 39** | **Language: Vue**

Native Android implementation:
- OpenClaw + Codex CLI on Android
- Two AI agents in one APK
- No root required
- No Termux dependency

**Best for:** Mobile deployment, Android users

---

### 9. jomafilms/openclaw-multitenant
**Stars: 18** | **Language: TypeScript**

Multi-tenant platform:
- Container isolation
- Encrypted vault per user
- Team sharing capabilities
- Enterprise multi-user support

**Best for:** Teams, SaaS deployment, multi-user scenarios

---

### 10. kitakitsune0x/zoidbergbot
**Stars: 23** | **Language: TypeScript**

MoltBot/ClawDB variant:
- Alternative flavor
- Custom integrations
- Community modifications

---

## Competing Platforms

### 1. AgenticSeek (Fosowl/agenticSeek)
**Stars: 25,343** | **Language: Python**

"Fully Local Manus AI" - direct competitor:
- No APIs required
- No monthly bills
- Autonomous agent
- Web browsing capability
- Code generation
- Cost: electricity only
- Official updates via Twitter

**Comparison:**
| Feature | OpenClaw | AgenticSeek |
|---------|----------|-------------|
| Local-first | Optional | Required |
| Model flexibility | High | Local only |
| Cost | API costs possible | Free after setup |
| Languages | TypeScript | Python |
| Integration | Multi-channel | Desktop-focused |

---

### 2. Devika (stitionai/devika)
**Stars: 19,484** | **Language: Python**

"Agentic Software Engineer" - Devin alternative:
- Understands high-level instructions
- Breaks down tasks
- Researches information
- Writes code autonomously
- Open-source Devin competitor

**Comparison:**
| Feature | OpenClaw | Devika |
|---------|----------|--------|
| Purpose | General assistant | Software engineering |
| Autonomy | Interactive | Autonomous |
| Code generation | Yes | Primary focus |
| Task planning | Manual | Automatic |

---

### 3. ARGO (xark-argo/argo)
**Stars: 478** | **Language: Python**

"Local Manus for Desktop":
- One-click model downloads
- Closed LLM integration
- Offline-first RAG
- Knowledge bases
- DeepResearch capability
- Win/Mac/Docker support
- 100% local data

**Best for:** Research workflows, offline use, privacy-focused users

---

### 4. CUA (trycua/cua)
**Stars: 12,777** | **Language: Python**

"Computer-Use Agents Infrastructure":
- Sandboxes for agent execution
- SDKs for development
- Benchmarks for evaluation
- Desktop control (macOS, Linux, Windows)
- Infrastructure layer, not end-user app

**Best for:** Developers building agent systems, benchmarking

---

### 5. Open Interpreter
**Stars: 62,477** | **Language: Python**

"Natural language interface for computers":
- CLI-based
- Code execution
- System control
- Local or cloud models

**Comparison:**
| Feature | OpenClaw | Open Interpreter |
|---------|----------|------------------|
| Interface | Chat/Telegram/etc. | CLI |
| Scope | Full assistant | Code execution |
| Automation | Agents + Skills | Interpreter |

---

### 6. Continue (continuedev/continue)
**Stars: 31,581** | **Language: TypeScript**

"AI code assistant for IDE":
- VS Code extension
- Source-controlled AI checks
- CI integration
- Code context awareness

**Best for:** IDE integration, coding workflows

---

### 7. moeru-ai/airi
**Stars: 19,936** | **Language: TypeScript**

"Grok Companion / Waifu Container":
- Self-hosted companion
- Real-time voice chat
- Minecraft/Factorio playing
- Web/macOS/Windows
- Anime-style interaction

**Best for:** Entertainment, gaming companions, voice interaction

---

### 8. VoltAgent/awesome-openclaw-skills
**Stars: 23,945** | **Resource Collection**

Skills directory:
- 5,400+ skills categorized
- Community contributions
- Skills registry

---

## Feature Comparison Matrix

| Project | Stars | Type | Local-First | Multi-Channel | Skills | Sub-Agents | Language |
|---------|-------|------|-------------|----------------|--------|------------|----------|
| **OpenClaw** | 242K | General | Optional | ✅ | ✅ ClawHub | ✅ | TS |
| openclaw-cn | 2.4K | Chinese | ✅ | ✅ Feishu/QQ | ✅ | ✅ | TS |
| ironclaw | 494 | CRM | Optional | ✅ | CRM-focused | ✅ | TS |
| localclaw | 71 | Small models | ✅ | Limited | ✅ | ✅ | TS |
| **AgenticSeek** | 25K | Autonomous | ✅ | ❌ | ❌ | ❌ | Python |
| **Devika** | 19K | Code agent | Optional | ❌ | ❌ | ✅ | Python |
| **ARGO** | 478 | Research | ✅ | ❌ | ✅ | ❌ | Python |
| **Open Interpreter** | 62K | CLI | ✅ | ❌ | ❌ | ❌ | Python |
| **Continue** | 32K | IDE | Optional | ❌ | ✅ | ❌ | TS |

---

## OpenClaw Advantages

1. **Ecosystem Size**: 242K stars, 46.9K forks - largest personal AI assistant community
2. **Skills Marketplace**: ClawHub with 5,400+ skills
3. **Multi-Channel**: Discord, Telegram, Slack, iMessage, WhatsApp, IRC, etc.
4. **Sub-Agent Architecture**: Spawn specialized agents for tasks
5. **Memory System**: Persistent context across sessions
6. **Active Development**: Daily commits, 9,898 open issues = active community
7. **Language**: TypeScript (modern, type-safe)

---

## OpenClaw Gaps (Where Alternatives Win)

1. **Local-First**: localclaw, AgenticSeek better for offline use
2. **Small Models**: localclaw optimized for 7B-14B models
3. **Enterprise**: ironclaw, QVerisBot have business features
4. **Chinese Market**: openclaw-cn, OpenCray have native integrations
5. **Mobile**: openclaw-android-assistant has native Android
6. **Autonomous Code**: Devika better for unsupervised coding
7. **Cost**: AgenticSeek claims $0 monthly (no APIs)

---

## Recommendations

### For Current OpenClaw Users

| Need | Recommendation |
|------|----------------|
| Chinese market | openclaw-cn or OpenCray |
| CRM/business | ironclaw |
| Small models | localclaw |
| Mobile | openclaw-android-assistant |
| Multi-tenant | openclaw-multitenant |

### For New Users

| Use Case | Recommendation |
|-----------|----------------|
| General assistant | **OpenClaw** (best ecosystem) |
| Local-only, free | AgenticSeek |
| Software engineering | Devika |
| Research workflows | ARGO |
| CLI power user | Open Interpreter |
| IDE coding | Continue |

---

## Key Insights

1. **OpenClaw dominates** - 10x more stars than nearest competitor (AgenticSeek)
2. **Fork ecosystem active** - Multiple specialized variants
3. **Chinese market huge** - Multiple China-focused forks
4. **Local-first trend** - AgenticSeek, localclaw gaining traction
5. **Business focus emerging** - ironclaw, QVerisBot for enterprise
6. **Skills economy** - ClawHub creates marketplace effect
7. **Sub-agents differentiator** - OpenClaw's agent spawning unique

---

## Source

Research conducted from GitHub API searches and repository analysis on 2026-03-01.
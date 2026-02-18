import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'
import { readFile, mkdir, writeFile, appendFile } from 'fs/promises'
import { glob } from 'glob'

const execAsync = promisify(exec)

interface AgentInfo {
  id: string
  name: string
  emoji: string
  role: string
  description: string
  status: 'idle' | 'busy' | 'learning' | 'offline'
  currentTask?: string
  lastActivity: string
  model: string
  skills: string[]
  recommendedSkills: string[]
  learningProgress?: number
  sessionKey?: string
  runtime?: string
  tokensUsed?: number
}

interface PendingApproval {
  id: string
  agentId: string
  agentName: string
  task: string
  description: string
  requestedAt: string
  priority: 'high' | 'medium' | 'low'
}

export async function GET() {
  try {
    // Get active subagents from OpenClaw
    const { stdout: sessionsOutput } = await execAsync(
      'openclaw sessions list --json 2>/dev/null || echo "[]"',
      { cwd: '/home/yeatz/.openclaw/workspace' }
    ).catch(() => ({ stdout: '[]' }))

    // Get cron jobs
    const { stdout: cronOutput } = await execAsync(
      'openclaw cron list --json 2>/dev/null || echo "[]"',
      { cwd: '/home/yeatz/.openclaw/workspace' }
    ).catch(() => ({ stdout: '[]' }))

    // Parse active sessions
    let activeSessions: any[] = []
    try {
      activeSessions = JSON.parse(sessionsOutput)
    } catch {
      activeSessions = []
    }

    // Get learning files for each agent
    const learningFiles = await glob('agents/*/learning/*.md', {
      cwd: '/home/yeatz/.openclaw/workspace'
    })

    // Calculate learning progress based on file count and recency
    const getLearningProgress = async (agentId: string): Promise<number> => {
      const agentLearningFiles = learningFiles.filter(f => f.startsWith(`agents/${agentId}/`))
      if (agentLearningFiles.length === 0) return 0
      
      // Check most recent file
      const mostRecent = agentLearningFiles.sort().reverse()[0]
      try {
        const stats = await readFile(`/home/yeatz/.openclaw/workspace/${mostRecent}`, 'utf-8')
        // Rough heuristic: more content = more learning
        const contentLength = stats.length
        return Math.min(Math.floor(contentLength / 100), 100)
      } catch {
        return Math.min(agentLearningFiles.length * 10, 100)
      }
    }

    // Find active subagent sessions
    const subagentSessions = activeSessions.filter((s: any) => 
      s.kind === 'subagent' || s.label?.includes('ghost') || s.label?.includes('oracle')
    )

    // Build agent status
    const agents: AgentInfo[] = await Promise.all([
      {
        id: 'ghost',
        name: 'Ghost',
        emoji: '👻',
        role: 'Code Specialist',
        description: 'Builds trading bots, infrastructure, and async systems',
        model: 'default',
        skills: ['Python', 'Async/await', 'WebSocket', 'Trading APIs', 'Database', 'Error Handling', 'Circuit Breakers'],
        recommendedSkills: ['Rust', 'Solana smart contracts', 'MEV protection', 'Jupiter SDK'],
      },
      {
        id: 'oracle',
        name: 'Oracle',
        emoji: '🔮',
        role: 'Trading Strategist',
        description: 'Designs strategies, backtests, and risk management',
        model: 'ollama/kimi-k2.5:cloud',
        skills: ['Technical Analysis', 'Backtesting', 'Risk Management', 'Indicators', 'Position Sizing', 'Kelly Criterion'],
        recommendedSkills: ['On-chain analysis', 'Order flow', 'Machine learning for trading', 'Market regimes'],
      },
      {
        id: 'pixel',
        name: 'Pixel',
        emoji: '🎨',
        role: 'UI/UX Engineer',
        description: 'Designs interfaces and component systems',
        model: 'default',
        skills: ['React', 'Tailwind CSS', 'Next.js', 'Component Design', 'Responsive UI'],
        recommendedSkills: ['Data visualization', 'Three.js', 'Motion design', 'Real-time dashboards'],
      },
      {
        id: 'synthesis',
        name: 'Synthesis',
        emoji: '🔗',
        role: 'Team Lead',
        description: 'Coordinates tasks and integrates solutions',
        model: 'default',
        skills: ['Architecture', 'Coordination', 'Documentation', 'Project Management'],
        recommendedSkills: ['Multi-agent coordination', 'Workflow optimization', 'System design'],
      }
    ].map(async (agent) => {
      // Find matching session
      const session = subagentSessions.find((s: any) => 
        s.label?.includes(agent.id) || s.sessionKey?.includes(agent.id)
      )

      // Check recent cron activity
      const recentLearning = learningFiles.filter(f => 
        f.includes(agent.id) && f.includes(new Date().toISOString().split('T')[0])
      )

      // Determine status
      let status: AgentInfo['status'] = 'idle'
      let currentTask: string | undefined
      let runtime: string | undefined
      let tokensUsed: number | undefined

      if (session) {
        status = 'busy'
        currentTask = session.label || 'Working on task'
        runtime = session.updatedAt 
          ? `${Math.floor((Date.now() - session.updatedAt) / 60000)}m`
          : undefined
        tokensUsed = session.totalTokens
      } else if (recentLearning.length > 0) {
        status = 'learning'
        currentTask = 'Continuous learning'
        runtime = 'Auto'
      }

      const learningProgress = await getLearningProgress(agent.id)

      return {
        ...agent,
        status,
        currentTask,
        lastActivity: recentLearning.length > 0 
          ? 'Just now' 
          : session 
            ? 'Active' 
            : 'Idle',
        learningProgress,
        sessionKey: session?.sessionKey,
        runtime,
        tokensUsed
      }
    }))

    // Get pending approvals from a file-based queue
    let pendingApprovals: PendingApproval[] = []
    try {
      const approvalsFile = await readFile(
        '/home/yeatz/.openclaw/workspace/mission-control/data/pending_approvals.json',
        'utf-8'
      )
      pendingApprovals = JSON.parse(approvalsFile)
    } catch {
      pendingApprovals = []
    }

    return NextResponse.json({ 
      agents, 
      pendingApprovals,
      lastUpdate: new Date().toISOString()
    })
  } catch (error) {
    console.error('Agents API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch agent data' },
      { status: 500 }
    )
  }
}

// Handle approval actions
export async function POST(request: Request) {
  try {
    const { action, approvalId, agentId } = await request.json()

    if (action === 'approve' || action === 'reject') {
      // Read current approvals
      let approvals: any[] = []
      try {
        const file = await readFile(
          '/home/yeatz/.openclaw/workspace/mission-control/data/pending_approvals.json',
          'utf-8'
        )
        approvals = JSON.parse(file)
      } catch {
        approvals = []
      }

      // Find and update the approval
      const approval = approvals.find(a => a.id === approvalId)
      if (!approval) {
        return NextResponse.json({ error: 'Approval not found' }, { status: 404 })
      }

      // Remove from pending
      const updatedApprovals = approvals.filter(a => a.id !== approvalId)
      
      // Save back
      await mkdir('/home/yeatz/.openclaw/workspace/mission-control/data', { recursive: true })
      await writeFile(
        '/home/yeatz/.openclaw/workspace/mission-control/data/pending_approvals.json',
        JSON.stringify(updatedApprovals, null, 2)
      )

      // Log the action
      const logEntry = JSON.stringify({
        timestamp: new Date().toISOString(),
        action,
        approvalId,
        agentId,
        task: approval.task
      }) + '\n'
      
      try {
        await appendFile(
          '/home/yeatz/.openclaw/workspace/mission-control/data/approval_log.jsonl',
          logEntry
        )
      } catch {
        // Log file might not exist, create it
        await writeFile(
          '/home/yeatz/.openclaw/workspace/mission-control/data/approval_log.jsonl',
          logEntry
        )
      }

      return NextResponse.json({ 
        success: true, 
        message: `Task ${action === 'approve' ? 'approved' : 'rejected'}` 
      })
    }

    return NextResponse.json({ error: 'Invalid action' }, { status: 400 })
  } catch (error) {
    console.error('Approval action error:', error)
    return NextResponse.json(
      { error: 'Failed to process approval' },
      { status: 500 }
    )
  }
}

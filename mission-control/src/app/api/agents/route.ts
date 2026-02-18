import { NextResponse } from 'next/server'
import { readFile, readdir, stat, writeFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

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

// Agent definitions
const AGENT_DEFINITIONS = [
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
]

async function getLearningFiles(agentId: string): Promise<string[]> {
  const learningDir = `/home/yeatz/.openclaw/workspace/agents/${agentId}/learning`
  try {
    if (!existsSync(learningDir)) return []
    const files = await readdir(learningDir)
    return files.filter(f => f.endsWith('.md')).sort()
  } catch {
    return []
  }
}

async function getLearningProgress(agentId: string): Promise<number> {
  const files = await getLearningFiles(agentId)
  if (files.length === 0) return 0
  
  // Check for today's file
  const today = new Date().toISOString().split('T')[0]
  const todayFile = files.find(f => f.includes(today))
  
  // Base progress on file count and recency
  const baseProgress = Math.min(files.length * 8, 60)
  const todayBonus = todayFile ? 15 : 0
  return Math.min(baseProgress + todayBonus, 100)
}

async function getLastActivity(agentId: string): Promise<string> {
  const files = await getLearningFiles(agentId)
  if (files.length === 0) return 'Never'
  
  const mostRecent = files[files.length - 1]
  const filePath = `/home/yeatz/.openclaw/workspace/agents/${agentId}/learning/${mostRecent}`
  
  try {
    const stats = await stat(filePath)
    const age = Date.now() - stats.mtime.getTime()
    const minutes = Math.floor(age / 60000)
    const hours = Math.floor(age / 3600000)
    const days = Math.floor(age / 86400000)
    
    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    return `${days}d ago`
  } catch {
    return 'Unknown'
  }
}

async function getCurrentTask(agentId: string): Promise<string | undefined> {
  // Check for recent learning activity
  const files = await getLearningFiles(agentId)
  const today = new Date().toISOString().split('T')[0]
  const todayFiles = files.filter(f => f.includes(today))
  
  if (todayFiles.length > 0) {
    // Read most recent file for topic
    try {
      const content = await readFile(
        `/home/yeatz/.openclaw/workspace/agents/${agentId}/learning/${todayFiles[todayFiles.length - 1]}`,
        'utf-8'
      )
      // Extract first heading
      const match = content.match(/^#+\s*(.+)$/m)
      return match ? match[1].slice(0, 50) : 'Learning session'
    } catch {
      return 'Learning'
    }
  }
  
  return undefined
}

export async function GET() {
  try {
    // Build agent status from filesystem
    const agents: AgentInfo[] = await Promise.all(
      AGENT_DEFINITIONS.map(async (agent) => {
        const learningFiles = await getLearningFiles(agent.id)
        const learningProgress = await getLearningProgress(agent.id)
        const lastActivity = await getLastActivity(agent.id)
        const currentTask = await getCurrentTask(agent.id)
        
        // Determine status
        let status: AgentInfo['status'] = 'idle'
        if (currentTask) {
          status = 'learning'
        }
        
        // Check for "busy" by looking at recent activity patterns
        const today = new Date().toISOString().split('T')[0]
        const todayCount = learningFiles.filter(f => f.includes(today)).length
        if (todayCount > 1) {
          status = 'busy'
        }
        
        return {
          ...agent,
          status,
          currentTask,
          lastActivity,
          learningProgress: learningProgress > 0 ? learningProgress : undefined,
        }
      })
    )

    // Get pending approvals from file
    let pendingApprovals: PendingApproval[] = []
    try {
      const approvalPath = '/home/yeatz/.openclaw/workspace/mission-control/data/pending_approvals.json'
      if (existsSync(approvalPath)) {
        const content = await readFile(approvalPath, 'utf-8')
        pendingApprovals = JSON.parse(content)
      }
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
    const { action, approvalId } = await request.json()

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

      // Find the approval
      const approval = approvals.find(a => a.id === approvalId)
      if (!approval) {
        return NextResponse.json({ error: 'Approval not found' }, { status: 404 })
      }

      // Remove from pending
      const updatedApprovals = approvals.filter(a => a.id !== approvalId)
      
      // Save back
      const dataDir = '/home/yeatz/.openclaw/workspace/mission-control/data'
      await writeFile(
        path.join(dataDir, 'pending_approvals.json'),
        JSON.stringify(updatedApprovals, null, 2)
      )

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

import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

const DATA_FILE = path.join(process.cwd(), 'data', 'action-items.json')

interface ActionItem {
  id: string
  title: string
  description: string
  source: string
  sourceFile: string
  priority: 'high' | 'medium' | 'low'
  category: string
  createdAt: string
  dueDate: string | null
  status: 'pending' | 'in-progress' | 'completed' | 'archived'
  tags: string[]
}

interface ActionItemsData {
  actionItems: ActionItem[]
  completed: ActionItem[]
  archived: ActionItem[]
}

async function loadData(): Promise<ActionItemsData> {
  try {
    const data = await fs.readFile(DATA_FILE, 'utf-8')
    return JSON.parse(data)
  } catch {
    return { actionItems: [], completed: [], archived: [] }
  }
}

async function saveData(data: ActionItemsData) {
  await fs.writeFile(DATA_FILE, JSON.stringify(data, null, 2))
}

// Scan learning files for action items
async function scanForActionItems(): Promise<ActionItem[]> {
  const items: ActionItem[] = []
  const agentsDir = path.join(process.cwd(), 'agents')
  
  try {
    const agents = await fs.readdir(agentsDir)
    for (const agent of agents) {
      const learningDir = path.join(agentsDir, agent, 'learning')
      try {
        const files = await fs.readdir(learningDir)
        const mdFiles = files.filter(f => f.endsWith('.md')).sort().reverse() // Newest first
        
        // Check 3 most recent files per agent
        for (const file of mdFiles.slice(0, 3)) {
          const content = await fs.readFile(path.join(learningDir, file), 'utf-8')
          
          // Parse action items from content
          // Look for patterns like "Action Item:", "**Action:**", "TODO:", etc.
          const actionPatterns = [
            /Action Item[s]?:\s*([^\n]+(?:\n(?!(?:#|\*\*))[^\n]+)?)/i,
            /\*\*Action[s]?:\*\*\s*([^\n]+(?:\n[^#\n]+)?)/i,
            /^(?:-|\*)\s*\[?\s*\]?\s*Action:\s*([^\n]+)/im,
            /Before (?:every|next|your)\s+trade[s]?:?\s*([^\n]+(?:\n[^#\n]+)?)/i,
            /Next step[s]?:\s*([^\n]+(?:\n(?!(?:#|\*\*))[^\n]+)?)/i,
            /Try this:\s*([^\n]+(?:\n(?!(?:#|\*\*))[^\n]+)?)/i
          ]
          
          for (const pattern of actionPatterns) {
            const match = content.match(pattern)
            if (match) {
              const title = match[1].trim().slice(0, 100)
              const description = content.slice(match.index! + match[0].length, match.index! + match[0].length + 200).replace(/\n/g, ' ').slice(0, 200)
              
              // Deduplicate by checking if similar item exists
              const id = `${agent}-${file.replace('.md', '')}`
              if (!items.find(i => i.id.startsWith(id))) {
                items.push({
                  id,
                  title,
                  description: description || 'From agent learning session',
                  source: agent.charAt(0).toUpperCase() + agent.slice(1),
                  sourceFile: path.join('agents', agent, 'learning', file).replace(process.cwd() + '/', ''),
                  priority: content.includes('high') || content.includes('critical') ? 'high' : 'medium',
                  category: agent.toLowerCase() === 'oracle' ? 'trading' : agent.toLowerCase() === 'ghost' ? 'code' : 'general',
                  createdAt: new Date().toISOString(),
                  dueDate: null,
                  status: 'pending',
                  tags: [agent.toLowerCase(), 'learning']
                })
              }
            }
          }
        }
      } catch {
        // No learning directory or can't read
      }
    }
  } catch {
    // Can't read agents directory
  }
  
  return items
}

export async function GET() {
  const data = await loadData()
  
  // Scan for new action items from learning files
  const scannedItems = await scanForActionItems()
  
  // Merge with existing (avoid duplicates)
  const existingIds = new Set(data.actionItems.map(i => i.id))
  const newItems = scannedItems.filter(i => !existingIds.has(i.id))
  
  if (newItems.length > 0) {
    data.actionItems = [...data.actionItems, ...newItems]
    await saveData(data)
  }
  
  return NextResponse.json(data)
}

export async function POST(request: NextRequest) {
  const body = await request.json()
  const data = await loadData()
  
  switch (body.action) {
    case 'toggle': {
      const item = data.actionItems.find(i => i.id === body.id)
      if (item) {
        if (body.status === 'completed') {
          item.status = 'completed'
          data.completed = [item, ...data.completed]
          data.actionItems = data.actionItems.filter(i => i.id !== body.id)
        } else {
          item.status = body.status
        }
      } else if (body.status === 'pending') {
        // Move from completed back to active
        const completedItem = data.completed.find(i => i.id === body.id)
        if (completedItem) {
          completedItem.status = 'pending'
          data.actionItems = [completedItem, ...data.actionItems]
          data.completed = data.completed.filter(i => i.id !== body.id)
        }
      }
      await saveData(data)
      return NextResponse.json({ success: true })
    }
    
    case 'add': {
      data.actionItems = [body.item, ...data.actionItems]
      await saveData(data)
      return NextResponse.json({ success: true, item: body.item })
    }
    
    case 'delete': {
      data.actionItems = data.actionItems.filter(i => i.id !== body.id)
      await saveData(data)
      return NextResponse.json({ success: true })
    }
    
    case 'update': {
      const idx = data.actionItems.findIndex(i => i.id === body.id)
      if (idx >= 0) {
        data.actionItems[idx] = { ...data.actionItems[idx], ...body.updates }
        await saveData(data)
      }
      return NextResponse.json({ success: true })
    }
    
    default:
      return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
  }
}

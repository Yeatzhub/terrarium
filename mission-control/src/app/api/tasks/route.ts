import { NextRequest, NextResponse } from 'next/server';
import { promises as fs } from 'fs';
import path from 'path';

const TASKS_DIR = '/home/yeatz/.openclaw/workspace/tasks';

interface Task {
  id: string;
  agent: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  description: string;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
}

async function readTaskFile(filePath: string): Promise<Task | null> {
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    const filename = path.basename(filePath);
    const matches = filename.match(/^(\w+)-([^.]+)\.md$/);
    
    if (!matches) return null;
    
    const [, agent, id] = matches;
    
    // Parse frontmatter
    const frontmatterMatch = content.match(/---\n([\s\S]*?)\n---/);
    const data: Record<string, string> = {};
    
    if (frontmatterMatch) {
      const lines = frontmatterMatch[1].split('\n');
      lines.forEach((line) => {
        const [key, ...valueParts] = line.split(':');
        if (key && valueParts.length) {
          data[key.trim()] = valueParts.join(':').trim();
        }
      });
    }
    
    // Extract task description (after frontmatter)
    const description = content.replace(/---\n[\s\S]*?\n---/, '').trim();
    
    return {
      id,
      agent,
      status: (data.status as Task['status']) || 'pending',
      description: description.replace('# Task\n\n', '').slice(0, 100) + '...',
      createdAt: data.created_at || new Date().toISOString(),
      startedAt: data.started_at || undefined,
      completedAt: data.completed_at || undefined,
    };
  } catch {
    return null;
  }
}

async function getTasks(status: string): Promise<Task[]> {
  const dir = path.join(TASKS_DIR, status);
  try {
    const files = await fs.readdir(dir);
    const tasks = await Promise.all(
      files
        .filter((f) => f.endsWith('.md'))
        .map((f) => readTaskFile(path.join(dir, f)))
    );
    return tasks.filter((t): t is Task => t !== null);
  } catch {
    return [];
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const status = searchParams.get('status') || 'all';
  
  try {
    if (status === 'all') {
      const statuses = ['pending', 'in-progress', 'completed', 'failed'];
      const allTasks = await Promise.all(statuses.map((s) => getTasks(s)));
      const tasks = allTasks.flat().sort((a, b) => 
        new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      );
      return NextResponse.json({ tasks });
    }
    
    const tasks = await getTasks(status);
    return NextResponse.json({ tasks });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch tasks', details: (error as Error).message },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { agent, description } = body;
    
    if (!agent || !description) {
      return NextResponse.json(
        { error: 'Missing agent or description' },
        { status: 400 }
      );
    }
    
    // Validate agent
    const validAgents = ['pixel', 'ghost', 'oracle', 'synthesis'];
    if (!validAgents.includes(agent)) {
      return NextResponse.json(
        { error: `Invalid agent. Valid: ${validAgents.join(', ')}` },
        { status: 400 }
      );
    }
    
    const taskId = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const taskFile = path.join(TASKS_DIR, 'pending', `${agent}-${taskId}.md`);
    
    const content = `---
assigned_to: ${agent}
task_id: ${taskId}
status: pending
created_at: ${new Date().toISOString()}
started_at: null
completed_at: null
---

# Task

${description}
`;
    
    await fs.writeFile(taskFile, content);
    
    return NextResponse.json({ 
      success: true, 
      taskId,
      agent,
      message: `Task assigned to ${agent}` 
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to create task', details: (error as Error).message },
      { status: 500 }
    );
  }
}

import { NextResponse } from 'next/server'
import { exec } from 'child_process'
import { promisify } from 'util'

const execAsync = promisify(exec)

interface OllamaModel {
  name: string
  model: string
  size: number
  parameter_size?: string
  quantization_level?: string
}

interface LLMStatus {
  currentModel: string
  availableModels: string[]
  contextWindow: number
  loadedModels: OllamaModel[]
  usage: {
    totalTokens: number
    maxTokens: number
    remainingTokens: number
    percentageUsed: number
  }
  timestamp: number
}

export async function GET() {
  try {
    // Get current OpenClaw/OpenClaw runtime info from environment
    const currentModel = process.env.OPENCLAW_MODEL || 'ollama/kimi-k2.5:cloud'
    
    // Fetch loaded models from Ollama
    let loadedModels: OllamaModel[] = []
    let ollamaAvailable = false
    
    try {
      const response = await fetch('http://localhost:11434/api/ps', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        const data = await response.json()
        loadedModels = data.models || []
        ollamaAvailable = true
      }
    } catch {
      // Ollama not available
    }

    // Get list of available models
    let availableModels: string[] = []
    try {
      const response = await fetch('http://localhost:11434/api/tags', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.ok) {
        const data = await response.json()
        availableModels = data.models?.map((m: OllamaModel) => m.name) || []
      }
    } catch {
      // Ollama not available
    }

    // Estimate context window based on model
    const modelName = currentModel.toLowerCase()
    let contextWindow = 32768 // default
    
    if (modelName.includes('kimi')) {
      contextWindow = 256000
    } else if (modelName.includes('phi4')) {
      contextWindow = 16384
    } else if (modelName.includes('qwen')) {
      contextWindow = 32768
    } else if (modelName.includes('llama3')) {
      contextWindow = 8192
    } else if (modelName.includes('mixtral')) {
      contextWindow = 32768
    }

    // Generate usage stats (these would ideally come from actual tracking)
    const status: LLMStatus = {
      currentModel,
      availableModels,
      contextWindow,
      loadedModels,
      usage: {
        totalTokens: 0,
        maxTokens: contextWindow,
        remainingTokens: contextWindow,
        percentageUsed: 0
      },
      timestamp: Date.now()
    }

    return NextResponse.json(status)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch LLM status', message: String(error) },
      { status: 500 }
    )
  }
}

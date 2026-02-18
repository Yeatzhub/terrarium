'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  Calendar,
  Tag,
  User,
  ArrowLeft,
  Plus,
  Trash2,
  Archive,
  Filter,
  ChevronDown,
  ChevronUp
} from 'lucide-react'

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

export default function ActionItemsPage() {
  const [items, setItems] = useState<ActionItem[]>([])
  const [completed, setCompleted] = useState<ActionItem[]>([])
  const [filter, setFilter] = useState<'all' | 'pending' | 'in-progress' | 'completed'>('all')
  const [showCompleted, setShowCompleted] = useState(false)
  const [editingItem, setEditingItem] = useState<ActionItem | null>(null)
  const [showAddModal, setShowAddModal] = useState(false)
  const [newItem, setNewItem] = useState<Partial<ActionItem>>({
    title: '',
    description: '',
    priority: 'medium',
    category: 'general',
    tags: []
  })

  // Load action items
  useEffect(() => {
    fetchActionItems()
  }, [])

  const fetchActionItems = async () => {
    try {
      const res = await fetch('/api/action-items')
      if (res.ok) {
        const data = await res.json()
        setItems(data.actionItems || [])
        setCompleted(data.completed || [])
      }
    } catch (err) {
      console.error('Failed to load action items:', err)
    }
  }

  const toggleStatus = async (item: ActionItem) => {
    const newStatus = item.status === 'completed' ? 'pending' : 'completed'
    try {
      await fetch('/api/action-items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          action: 'toggle',
          id: item.id,
          status: newStatus 
        })
      })
      fetchActionItems()
    } catch (err) {
      console.error('Failed to toggle status:', err)
    }
  }

  const addItem = async () => {
    if (!newItem.title) return
    try {
      await fetch('/api/action-items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'add',
          item: {
            ...newItem,
            id: `user-${Date.now()}`,
            source: 'User',
            sourceFile: '',
            createdAt: new Date().toISOString(),
            status: 'pending'
          }
        })
      })
      setShowAddModal(false)
      setNewItem({ title: '', description: '', priority: 'medium', category: 'general', tags: [] })
      fetchActionItems()
    } catch (err) {
      console.error('Failed to add item:', err)
    }
  }

  const deleteItem = async (id: string) => {
    try {
      await fetch('/api/action-items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'delete', id })
      })
      fetchActionItems()
    } catch (err) {
      console.error('Failed to delete:', err)
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-400 bg-red-500/20 border-red-500/30'
      case 'medium': return 'text-amber-400 bg-amber-500/20 border-amber-500/30'
      case 'low': return 'text-cyan-400 bg-cyan-500/20 border-cyan-500/30'
      default: return 'text-slate-400 bg-slate-500/20 border-slate-500/30'
    }
  }

  const getSourceIcon = (source: string) => {
    switch (source.toLowerCase()) {
      case 'ghost': return '👻'
      case 'oracle': return '🔮'
      case 'pixel': return '🎨'
      case 'synthesis': return '🔗'
      default: return '👤'
    }
  }

  const filteredItems = items.filter(item => {
    if (filter === 'all') return item.status !== 'archived'
    if (filter === 'completed') return item.status === 'completed'
    return item.status === filter
  })

  const activeCount = items.filter(i => i.status === 'pending' || i.status === 'in-progress').length
  const completedCount = completed.length + items.filter(i => i.status === 'completed').length

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link 
              href="/"
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                Action Queue
              </h1>
              <p className="text-slate-400">{activeCount} active • {completedCount} completed</p>
            </div>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Item
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Pending', value: items.filter(i => i.status === 'pending').length, color: 'text-slate-400' },
            { label: 'In Progress', value: items.filter(i => i.status === 'in-progress').length, color: 'text-amber-400' },
            { label: 'High Priority', value: items.filter(i => i.priority === 'high' && i.status !== 'completed').length, color: 'text-red-400' },
            { label: 'Completed Today', value: completed.filter(i => new Date(i.createdAt).toDateString() === new Date().toDateString()).length, color: 'text-emerald-400' },
          ].map(stat => (
            <div key={stat.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-sm text-slate-500">{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Filter Bar */}
        <div className="flex items-center gap-4 mb-6">
          <Filter className="w-5 h-5 text-slate-400" />
          <div className="flex gap-2">
            {(['all', 'pending', 'in-progress', 'completed'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-sm capitalize transition-colors ${
                  filter === f 
                    ? 'bg-purple-600 text-white' 
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                }`}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Action Items List */}
        <div className="space-y-3">
          {filteredItems.length === 0 ? (
            <div className="text-center py-12 text-slate-500">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No {filter === 'all' ? 'action items' : filter + ' items'}</p>
              <p className="text-sm mt-1">All caught up!</p>
            </div>
          ) : (
            filteredItems.map(item => (
              <div 
                key={item.id}
                className={`bg-slate-900 rounded-xl border transition-all ${
                  item.status === 'completed' 
                    ? 'border-slate-800 opacity-60' 
                    : 'border-slate-700 hover:border-slate-600'
                }`}
              >
                <div className="p-4 flex items-start gap-4">
                  {/* Checkbox */}
                  <button
                    onClick={() => toggleStatus(item)}
                    className={`mt-0.5 transition-colors ${
                      item.status === 'completed' ? 'text-emerald-400' : 'text-slate-600 hover:text-emerald-400'
                    }`}
                  >
                    {item.status === 'completed' ? (
                      <CheckCircle2 className="w-6 h-6" />
                    ) : (
                      <Circle className="w-6 h-6" />
                    )}
                  </button>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <h3 className={`font-medium ${item.status === 'completed' ? 'line-through text-slate-500' : ''}`}>
                          {item.title}
                        </h3>
                        <p className="text-sm text-slate-400 mt-1">{item.description}</p>
                        
                        {/* Tags */}
                        <div className="flex flex-wrap gap-2 mt-3">
                          <span className={`px-2 py-0.5 rounded text-xs border ${getPriorityColor(item.priority)}`}>
                            {item.priority}
                          </span>
                          {item.tags.map(tag => (
                            <span key={tag} className="px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-xs flex items-center gap-1">
                              <Tag className="w-3 h-3" />
                              {tag}
                            </span>
                          ))}
                          <span className="px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-xs flex items-center gap-1">
                            <User className="w-3 h-3" />
                            {getSourceIcon(item.source)} {item.source}
                          </span>
                          {item.sourceFile && (
                            <Link 
                              href={`#`}
                              onClick={() => window.open(`/${item.sourceFile}`, '_blank')}
                              className="px-2 py-0.5 bg-slate-800 text-cyan-400 hover:text-blue-300 rounded text-xs flex items-center gap-1"
                            >
                              📄 Source
                            </Link>
                          )}
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2">
                        {item.status !== 'completed' && (
                          <button
                            onClick={() => deleteItem(item.id)}
                            className="p-2 text-slate-500 hover:text-red-400 transition-colors"
                            title="Delete"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Completed Toggle */}
        {completed.length > 0 && (
          <button
            onClick={() => setShowCompleted(!showCompleted)}
            className="mt-6 flex items-center gap-2 text-slate-500 hover:text-slate-300 transition-colors"
          >
            {showCompleted ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            Show {completed.length} completed items
          </button>
        )}

        {/* Add Modal */}
        {showAddModal && (
          <div 
            className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4"
            onClick={() => setShowAddModal(false)}
          >
            <div 
              className="bg-slate-900 rounded-xl border border-slate-700 p-6 max-w-md w-full"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold mb-4">Add Action Item</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-slate-400 mb-1">Title</label>
                  <input
                    type="text"
                    value={newItem.title}
                    onChange={e => setNewItem({...newItem, title: e.target.value})}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-purple-500"
                    placeholder="What needs to be done?"
                  />
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-1">Description</label>
                  <textarea
                    value={newItem.description}
                    onChange={e => setNewItem({...newItem, description: e.target.value})}
                    rows={3}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-purple-500 resize-none"
                    placeholder="Add details..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Priority</label>
                    <select
                      value={newItem.priority}
                      onChange={e => setNewItem({...newItem, priority: e.target.value as any})}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-purple-500"
                    >
                      <option value="high">High</option>
                      <option value="medium">Medium</option>
                      <option value="low">Low</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm text-slate-400 mb-1">Category</label>
                    <select
                      value={newItem.category}
                      onChange={e => setNewItem({...newItem, category: e.target.value})}
                      className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-purple-500"
                    >
                      <option value="trading">Trading</option>
                      <option value="code">Code</option>
                      <option value="research">Research</option>
                      <option value="general">General</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-1">Tags (comma separated)</label>
                  <input
                    type="text"
                    value={newItem.tags?.join(', ')}
                    onChange={e => setNewItem({...newItem, tags: e.target.value.split(',').map(t => t.trim())})}
                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:border-purple-500"
                    placeholder="risk, sizing, bitcoin"
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowAddModal(false)}
                  className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={addItem}
                  disabled={!newItem.title}
                  className="flex-1 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800/50 rounded-lg transition-colors"
                >
                  Add Item
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

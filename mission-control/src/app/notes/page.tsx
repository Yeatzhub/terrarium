'use client'

import { useState } from 'react'

export default function NotesPage() {
  const [notes, setNotes] = useState([
    { id: 1, content: 'P40 GPU arrives this week - install and test with phi4', date: '2026-02-15' },
    { id: 2, content: 'Remember to setup cron job for memory cleanup', date: '2026-02-15' },
    { id: 3, content: 'WD Red drives for NAS - setup redundancy', date: '2026-02-15' },
  ])
  const [newNote, setNewNote] = useState('')

  const addNote = () => {
    if (newNote.trim()) {
      setNotes([{ 
        id: Date.now(), 
        content: newNote, 
        date: new Date().toISOString().split('T')[0] 
      }, ...notes])
      setNewNote('')
    }
  }

  const deleteNote = (id: number) => {
    setNotes(notes.filter(n => n.id !== id))
  }

  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Quick Notes</h1>
        
        {/* Add Note */}
        <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 mb-6">
          <textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Type a quick note..."
            className="w-full bg-slate-700 rounded-lg p-3 text-white placeholder-slate-400 resize-none h-24 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex justify-end mt-3">
            <button 
              onClick={addNote}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            >
              Add Note
            </button>
          </div>
        </div>

        {/* Notes List */}
        <div className="space-y-4">
          {notes.map((note) => (
            <div key={note.id} className="bg-slate-800 rounded-xl p-4 border border-slate-700 group">
              <div className="flex justify-between items-start">
                <p className="text-slate-300 flex-1">{note.content}</p>
                <button 
                  onClick={() => deleteNote(note.id)}
                  className="text-slate-500 hover:text-red-400 transition-colors ml-4 opacity-0 group-hover:opacity-100"
                >
                  ✕
                </button>
              </div>
              <p className="text-slate-500 text-sm mt-2">{note.date}</p>
            </div>
          ))}
        </div>

        <div className="mt-6">
          <a 
            href="/"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors inline-block"
          >
            ← Back to Dashboard
          </a>
        </div>
      </div>
    </main>
  )
}
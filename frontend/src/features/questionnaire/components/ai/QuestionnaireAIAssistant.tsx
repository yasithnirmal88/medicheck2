import React, { useState, useRef, useEffect } from 'react'
import { Bot, Send, User, X } from 'lucide-react'
import { cn } from '@/lib/utils'

type Message = {
  role: 'assistant' | 'user'
  content: string
}

const QuestionnaireAIAssistant: React.FC = () => {
  const [open, setOpen] = useState(true)
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Hi! I can help explain questions, review your answers, or suggest next steps. What would you like help with?',
    },
  ])
  const bottomRef = useRef<HTMLDivElement | null>(null)

  const handleSend = () => {
    if (!input.trim()) return
    setMessages((prev) => [...prev, { role: 'user', content: input.trim() }])
    setInput('')
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        aria-label="Open AI assistant"
        className="fixed bottom-6 right-6 z-40 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-indigo-600 text-white shadow-lg shadow-indigo-500/30 transition hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60 md:static md:h-auto md:w-auto md:rounded-xl md:px-3 md:py-2 md:text-sm"
      >
        <Bot className="h-5 w-5" aria-hidden="true" />
      </button>
    )
  }

  return (
    <aside
      className={cn(
        'flex w-full max-w-sm flex-col rounded-2xl border bg-white shadow-sm dark:bg-slate-800 dark:border-gray-700',
        'transition-all duration-300',
      )}
    >
      <div className="flex items-center justify-between rounded-t-xl bg-gray-50 px-4 py-2.5 dark:bg-slate-900">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400">
            <Bot className="h-4 w-4" aria-hidden="true" />
          </div>
          <span className="font-medium text-gray-800 dark:text-gray-200">Assessment AI</span>
        </div>
        <button
          type="button"
          onClick={() => setOpen(false)}
          aria-label="Minimize AI assistant"
          className="rounded p-1 text-gray-500 hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      <ul className="flex-1 space-y-3 overflow-y-auto px-4 py-4 text-sm">
        {messages.map((m, i) => (
          <li
            key={`${m.role}-${i}`}
            className={cn(
              'max-w-[85%] rounded-xl px-3 py-2',
              m.role === 'assistant'
                ? 'self-start rounded-tl-none bg-gray-100 text-gray-800 dark:bg-slate-700 dark:text-gray-200'
                : 'item-start rounded-tr-none bg-indigo-600 text-white',
            )}
          >
            <div className="flex items-start gap-2">
              {m.role === 'assistant' && <Bot className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />}
              {m.role === 'user' && <User className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />}
              <span className="block break-words">{m.content}</span>
            </div>
          </li>
        ))}
        <div ref={bottomRef} />
      </ul>

      <div className="border-t border-gray-200 p-3 dark:border-gray-700">
        <div className="flex items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask the assistant..."
            rows={2}
            className={cn(
              'flex-1 resize-none rounded-xl border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900',
              'placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/60',
              'dark:border-gray-600 dark:bg-slate-900 dark:text-gray-100 dark:placeholder:text-gray-500',
            )}
          />
          <button
            type="button"
            disabled={!input.trim()}
            onClick={handleSend}
            aria-label="Send message"
            className={cn(
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-indigo-600 text-white',
              'disabled:cursor-not-allowed disabled:opacity-50 hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/60',
            )}
          >
            <Send className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>
        <p className="mt-1.5 text-xs text-gray-400 dark:text-gray-500">
          Press Enter to send, Shift+Enter for a new line.
        </p>
      </div>
    </aside>
  )
}

export default React.memo(QuestionnaireAIAssistant)

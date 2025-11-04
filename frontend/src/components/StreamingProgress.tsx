import { useState, useEffect, useRef } from 'react'
import { StreamEvent, SessionMessage, ThinkingStep, StatusUpdate, streamSessionUpdates } from '../services/api'

interface StreamingProgressProps {
  sessionId: string
  onComplete?: (sessionId: string, hasUpdatedAnalysis?: boolean) => void
  title?: string
}

export default function StreamingProgress({ sessionId, onComplete, title = "Devin is working..." }: StreamingProgressProps) {
  const [messages, setMessages] = useState<SessionMessage[]>([])
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([])
  const [status, setStatus] = useState<StatusUpdate | null>(null)
  const [isCompleted, setIsCompleted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isConnecting, setIsConnecting] = useState(true)
  
  const cleanupRef = useRef<(() => void) | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, thinkingSteps])

  useEffect(() => {
    if (!sessionId) return

    setIsConnecting(true)
    setError(null)

    const cleanup = streamSessionUpdates(
      sessionId,
      (event: StreamEvent) => {
        setIsConnecting(false)
        
        switch (event.type) {
          case 'message':
            setMessages(prev => [...prev, event.data as SessionMessage])
            break
            
          case 'thinking':
            setThinkingSteps(prev => [...prev, event.data as ThinkingStep])
            break
            
          case 'status':
            setStatus(event.data as StatusUpdate)
            break
            
          case 'completed':
            setIsCompleted(true)
            setStatus(prev => prev ? { ...prev, completed: true } : null)
            const hasUpdatedAnalysis = event.data?.updated_analysis !== undefined
            onComplete?.(sessionId, hasUpdatedAnalysis)
            break
            
          case 'error':
            setError(`Stream error: ${event.data.error}`)
            break
            
          case 'fatal_error':
            setError(`Connection failed: ${event.data.error}`)
            setIsCompleted(true)
            break
        }
      },
      (error: Error) => {
        setError(error.message)
        setIsConnecting(false)
      },
      () => {
        setIsCompleted(true)
        setIsConnecting(false)
      }
    )

    cleanupRef.current = cleanup

    return () => {
      cleanup()
    }
  }, [sessionId, onComplete])

  const formatTimestamp = (timestamp?: string | number) => {
    if (!timestamp) return ''
    const date = new Date(typeof timestamp === 'string' ? timestamp : timestamp * 1000)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  }

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'completed':
      case 'success':
      case 'done':
        return 'text-green-600'
      case 'failed':
      case 'error':
        return 'text-red-600'
      case 'running':
      case 'working':
        return 'text-blue-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="font-semibold text-gray-900">{title}</h3>
            {isConnecting && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                Connecting...
              </div>
            )}
          </div>
          
          {status && (
            <div className="flex items-center gap-2 text-sm">
              <span className={`font-medium ${getStatusColor(status.status)}`}>
                {status.status_enum || status.status}
              </span>
              {status.completed && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  ✓ Completed
                </span>
              )}
            </div>
          )}
        </div>
        
        {status && (
          <div className="mt-2 text-sm text-gray-500">
            {status.message_count > 0 && <span>{status.message_count} messages</span>}
            {status.thinking_count > 0 && (
              <>
                {status.message_count > 0 && <span> • </span>}
                <span>{status.thinking_count} thinking steps</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-4 py-3">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}

      {/* Content */}
      <div className="max-h-96 overflow-y-auto">
        {/* Thinking Steps with enhanced styling */}
        {thinkingSteps.map((step, index) => (
          <div key={index} className="border-b border-gray-100 px-4 py-3 animate-fadeIn">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-purple-100 rounded-full flex items-center justify-center">
                <span className="text-xs font-medium text-purple-600">💭</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-purple-600">
                    {step.content.includes('Phase') || step.content.includes('Step') ? 'Planning' : 'Thinking'}
                  </span>
                  {step.timestamp && (
                    <span className="text-xs text-gray-400">
                      {formatTimestamp(step.timestamp)}
                    </span>
                  )}
                  {index === thinkingSteps.length - 1 && !isCompleted && (
                    <div className="animate-pulse w-2 h-2 bg-purple-400 rounded-full ml-2"></div>
                  )}
                </div>
                <p className="text-sm text-gray-700 whitespace-pre-wrap">{step.content}</p>
              </div>
            </div>
          </div>
        ))}

        {/* Messages with enhanced styling and typing indicators */}
        {messages.map((message, index) => (
          <div key={index} className="border-b border-gray-100 px-4 py-3 animate-fadeIn">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center">
                <span className="text-xs font-medium text-blue-600">
                  {message.role === 'assistant' ? '🤖' : '👤'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium text-blue-600 capitalize">
                    {message.role === 'assistant' ? 'Devin' : 'User'}
                  </span>
                  {message.timestamp && (
                    <span className="text-xs text-gray-400">
                      {formatTimestamp(message.timestamp)}
                    </span>
                  )}
                  {index === messages.length - 1 && message.role === 'assistant' && !isCompleted && (
                    <div className="flex items-center gap-1 ml-2">
                      <div className="animate-bounce w-1 h-1 bg-blue-400 rounded-full" style={{animationDelay: '0ms'}}></div>
                      <div className="animate-bounce w-1 h-1 bg-blue-400 rounded-full" style={{animationDelay: '150ms'}}></div>
                      <div className="animate-bounce w-1 h-1 bg-blue-400 rounded-full" style={{animationDelay: '300ms'}}></div>
                    </div>
                  )}
                </div>
                <div className="text-sm text-gray-700 whitespace-pre-wrap">
                  {message.content}
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Loading state with enhanced progress indicators */}
        {!isCompleted && !error && thinkingSteps.length === 0 && messages.length === 0 && !isConnecting && (
          <div className="px-4 py-8 text-center">
            <div className="animate-pulse">
              <div className="inline-flex items-center gap-2 text-sm text-gray-500 mb-4">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400"></div>
                Waiting for Devin to start...
              </div>
              <div className="text-xs text-gray-400">
                {title.includes('Analyzing') 
                  ? 'Devin is reading the issue and planning the analysis...'
                  : 'Devin is preparing to implement the solution...'
                }
              </div>
            </div>
          </div>
        )}

        {/* Connection state indicator */}
        {isConnecting && (
          <div className="px-4 py-3 bg-blue-50 border-b border-blue-100">
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <div className="animate-pulse w-2 h-2 bg-blue-500 rounded-full"></div>
              <span>Connecting to Devin session...</span>
            </div>
          </div>
        )}

        {/* Empty state when completed but no content */}
        {isCompleted && thinkingSteps.length === 0 && messages.length === 0 && !error && (
          <div className="px-4 py-8 text-center text-sm text-gray-500">
            Session completed but no detailed progress was captured.
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Footer */}
      {isCompleted && (
        <div className="bg-white border-t border-gray-200 px-4 py-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">
              Session completed at {formatTimestamp(Date.now())}
            </span>
            <a
              href={`https://app.devin.ai/sessions/${sessionId.replace('devin-', '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 font-medium"
            >
              View in Devin →
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

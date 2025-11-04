import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface GitHubIssue {
  number: number
  title: string
  body: string
  state: string
  html_url: string
  user: {
    login: string
    avatar_url: string
  }
  labels: Array<{
    name: string
    color: string
  }>
  created_at: string
  updated_at: string
  analysis?: Analysis
  execution?: Execution
}

export interface Analysis {
  session_id: string
  summary: string
  detailed_analysis?: string
  confidence: number
  confidence_reasoning?: string
  steps: string[]
  complexity?: string
  potential_challenges?: string[]
  success_criteria?: string[]
  status: string
  note?: string
  session_url?: string
}

export interface Execution {
  session_id: string
  status: string
  message: string
  session_url?: string
}

export interface HealthStatus {
  status: string
  configuration: {
    github_token: boolean
    github_repo: boolean
    devin_api_key: boolean
  }
  repo?: string
}

export const getHealthStatus = async (): Promise<HealthStatus> => {
  const response = await api.get('/health')
  return response.data
}

export const getIssues = async (state: string = 'open'): Promise<GitHubIssue[]> => {
  const response = await api.get(`/issues`, { params: { state } })
  return response.data.issues
}

export const getIssue = async (issueNumber: number): Promise<GitHubIssue> => {
  const response = await api.get(`/issues/${issueNumber}`)
  return response.data.issue
}

export const analyzeIssue = async (issueNumber: number, postComment: boolean = true): Promise<Analysis> => {
  const response = await api.post(`/analyze/${issueNumber}`, null, {
    params: { post_comment: postComment }
  })
  return response.data.analysis
}

export const executeIssue = async (issueNumber: number): Promise<Execution> => {
  const response = await api.post(`/execute/${issueNumber}`)
  return response.data.execution
}

export const getSessionStatus = async (sessionId: string) => {
  const response = await api.get(`/sessions/${sessionId}`)
  return response.data.session
}

export const getHistory = async () => {
  const response = await api.get(`/history`)
  return response.data.history
}

// Streaming interfaces
export interface StreamEvent {
  type: 'message' | 'thinking' | 'status' | 'completed' | 'error' | 'fatal_error'
  data: any
  timestamp: number
}

export interface SessionMessage {
  content: string
  role: string
  timestamp?: string
  type?: string
}

export interface ThinkingStep {
  content: string
  step_number?: number
  timestamp?: string
}

export interface StatusUpdate {
  status: string
  status_enum: string
  message_count: number
  thinking_count: number
  completed: boolean
}

// Stream session updates using Server-Sent Events
export const streamSessionUpdates = (
  sessionId: string,
  onEvent: (event: StreamEvent) => void,
  onError?: (error: Error) => void,
  onComplete?: () => void
): (() => void) => {
  const API_BASE = API_BASE_URL.startsWith('/') ? 
    `${window.location.protocol}//${window.location.host}${API_BASE_URL}` : 
    API_BASE_URL
  
  const eventSource = new EventSource(`${API_BASE}/sessions/${sessionId}/stream`)
  
  eventSource.onmessage = (event) => {
    try {
      const streamEvent: StreamEvent = JSON.parse(event.data)
      onEvent(streamEvent)
      
      if (streamEvent.type === 'completed') {
        eventSource.close()
        onComplete?.()
      }
    } catch (error) {
      console.error('Error parsing stream event:', error)
      onError?.(new Error('Failed to parse stream event'))
    }
  }
  
  eventSource.onerror = (error) => {
    console.error('EventSource error:', error)
    onError?.(new Error('Stream connection error'))
  }
  
  // Return cleanup function
  return () => {
    eventSource.close()
  }
}


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
  confidence: number
  steps: string[]
  complexity?: string
  potential_challenges?: string[]
  success_criteria?: string[]
  status: string
  note?: string
  session_url?: string
  type?: string
  implementation_status?: string
  pr_url?: string
  pr_number?: string
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

export const analyzeIssue = async (issueNumber: number, postComment: boolean = true, unified: boolean = false): Promise<Analysis> => {
  const response = await api.post(`/analyze/${issueNumber}`, null, {
    params: { post_comment: postComment, unified: unified }
  })
  return response.data.analysis
}

export const analyzeAndImplementIssue = async (issueNumber: number, postComment: boolean = true): Promise<Analysis> => {
  return analyzeIssue(issueNumber, postComment, true)
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


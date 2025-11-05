import { useState } from 'react'
import { GitHubIssue, analyzeIssue, executeIssue, getIssue } from '../services/api'
import AnalysisPanel from './AnalysisPanel'
import SimpleLoadingScreen from './SimpleLoadingScreen'

interface IssueCardProps {
  issue: GitHubIssue
  onUpdate: (issue: GitHubIssue) => void
}

export default function IssueCard({ issue, onUpdate }: IssueCardProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadingSessionId, setLoadingSessionId] = useState<string | null>(null)
  const [loadingType, setLoadingType] = useState<'analysis' | 'execution' | null>(null)

  const handleAnalyze = async () => {
    // Prevent multiple simultaneous calls
    if (isAnalyzing) {
      console.log('Analysis already in progress, skipping duplicate call')
      return
    }
    
    console.log(`Starting analysis for issue #${issue.number}`)
    setIsAnalyzing(true)
    setError(null)
    setLoadingType('analysis')
    setLoadingSessionId('loading') // Show loading screen immediately
    
    try {
      const analysis = await analyzeIssue(issue.number, true)
      console.log(`Analysis API response for issue #${issue.number}:`, analysis)
      
      // Check if we need to poll or complete immediately
      if (analysis.status === 'running' && analysis.session_id) {
        setLoadingSessionId(analysis.session_id) // Switch to real session ID for polling
      } else {
        // Analysis completed immediately - show loading briefly then complete
        setTimeout(() => {
          const updatedIssue = { ...issue, analysis }
          onUpdate(updatedIssue)
          setIsAnalyzing(false)
          setLoadingType(null)
          setLoadingSessionId(null)
        }, 1000) // Show loading for 1 second even if immediate
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze issue')
      setIsAnalyzing(false)
      setLoadingType(null)
      setLoadingSessionId(null)
    }
  }

  const handleExecute = async () => {
    setIsExecuting(true)
    setError(null)
    setLoadingType('execution')
    setLoadingSessionId('loading') // Show loading screen immediately
    
    try {
      const execution = await executeIssue(issue.number)
      
      // Check if we need to poll or complete immediately
      if (execution.session_id && execution.session_id !== 'fallback-execution') {
        setLoadingSessionId(execution.session_id) // Switch to real session ID for polling
      } else {
        // Execution completed immediately (fallback) - show loading briefly then complete
        setTimeout(() => {
          const updatedIssue = { ...issue, execution }
          onUpdate(updatedIssue)
          setIsExecuting(false)
          setLoadingType(null)
          setLoadingSessionId(null)
        }, 1000) // Show loading for 1 second even if immediate
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute plan')
      setIsExecuting(false)
      setLoadingType(null)
      setLoadingSessionId(null)
    }
  }

  const handleLoadingComplete = (sessionId: string, completionData?: any) => {
    console.log(`Loading completed for issue #${issue.number}, sessionId: ${sessionId}`, completionData)
    
    // For execution completion, don't immediately clear the loading state
    // Let the completion screen show first, then update after a delay
    if (loadingType === 'execution') {
      // Keep the loading screen showing completion for execution
      setTimeout(async () => {
        try {
          console.log(`Re-fetching issue #${issue.number} after execution completion`)
          const updatedIssue = await getIssue(issue.number)
          console.log(`Updated issue #${issue.number} after execution completion:`, {
            hasAnalysis: !!updatedIssue.analysis,
            hasExecution: !!updatedIssue.execution,
            executionStatus: updatedIssue.execution?.status
          })
          onUpdate(updatedIssue)
          
          // Reset loading states after successful update
          setIsExecuting(false)
          setLoadingSessionId(null)
          setLoadingType(null)
        } catch (error) {
          console.error('Failed to refresh issue after execution completion:', error)
          // Even on error, reset the loading states
          setIsExecuting(false)
          setLoadingSessionId(null)
          setLoadingType(null)
        }
      }, 3000) // Longer delay for execution to show completion screen
    } else {
      // For analysis, update immediately
      setTimeout(async () => {
        try {
          console.log(`Re-fetching issue #${issue.number} after analysis completion`)
          const updatedIssue = await getIssue(issue.number)
          console.log(`Updated issue #${issue.number} after analysis completion:`, {
            hasAnalysis: !!updatedIssue.analysis,
            analysisStatus: updatedIssue.analysis?.status
          })
          onUpdate(updatedIssue)
        } catch (error) {
          console.error('Failed to refresh issue after analysis completion:', error)
        }
      }, 500)
      
      // Reset loading states for analysis
      setIsAnalyzing(false)
      setLoadingSessionId(null)
      setLoadingType(null)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition">
      <div className="p-6">
        {/* Issue Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <a
                href={issue.html_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xl font-semibold text-gray-900 hover:text-primary-600 transition"
              >
                #{issue.number} {issue.title}
              </a>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                issue.state === 'open' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-purple-100 text-purple-800'
              }`}>
                {issue.state}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <div className="flex items-center gap-2">
                <img
                  src={issue.user.avatar_url}
                  alt={issue.user.login}
                  className="w-5 h-5 rounded-full"
                />
                <span>{issue.user.login}</span>
              </div>
              <span>•</span>
              <span>Created {formatDate(issue.created_at)}</span>
            </div>
          </div>
        </div>

        {/* Labels */}
        {issue.labels.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-4">
            {issue.labels.map((label) => (
              <span
                key={label.name}
                className="px-3 py-1 rounded-full text-xs font-medium"
                style={{
                  backgroundColor: `#${label.color}20`,
                  color: `#${label.color}`,
                  borderColor: `#${label.color}40`,
                  borderWidth: '1px',
                }}
              >
                {label.name}
              </span>
            ))}
          </div>
        )}

        {/* Issue Body */}
        {issue.body && (
          <div className="mb-4 text-gray-700 text-sm line-clamp-3">
            {issue.body}
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3">
          {!issue.analysis && (
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || loadingSessionId !== null}
              className="flex items-center gap-2 bg-primary-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-primary-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isAnalyzing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Analyzing with Devin...
                </>
              ) : (
                <>
                  Analyze with Devin
                </>
              )}
            </button>
          )}

          {issue.analysis && !issue.execution && (
            <button
              onClick={handleExecute}
              disabled={isExecuting}
              className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-green-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExecuting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Executing...
                </>
              ) : (
                <>
                  Implement Plan
                </>
              )}
            </button>
          )}

          <a
            href={issue.html_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition"
          >
            View on GitHub
            <span>↗</span>
          </a>
        </div>

        {/* Streaming Progress */}
        {loadingSessionId && loadingType && (
          <div className="mt-6">
            <SimpleLoadingScreen 
              sessionId={loadingSessionId}
              type={loadingType}
              onComplete={handleLoadingComplete}
            />
          </div>
        )}

        {/* Analysis Panel */}
        {issue.analysis && !(loadingSessionId && loadingType === 'execution') && (
          <div className="mt-6">
            <AnalysisPanel analysis={issue.analysis} execution={issue.execution} />
          </div>
        )}
      </div>
    </div>
  )
}


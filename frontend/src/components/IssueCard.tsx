import { useState } from 'react'
import { GitHubIssue, analyzeIssue, executeIssue, getIssue } from '../services/api'
import AnalysisPanel from './AnalysisPanel'
import StreamingProgress from './StreamingProgress'

interface IssueCardProps {
  issue: GitHubIssue
  onUpdate: (issue: GitHubIssue) => void
}

export default function IssueCard({ issue, onUpdate }: IssueCardProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isExecuting, setIsExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [streamingSessionId, setStreamingSessionId] = useState<string | null>(null)
  const [streamingType, setStreamingType] = useState<'analysis' | 'execution' | null>(null)

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    setError(null)
    setStreamingType('analysis')
    try {
      const analysis = await analyzeIssue(issue.number, true)
      
      // Analysis is now synchronous - no streaming needed
      // Just update immediately with the completed analysis
      const updatedIssue = { ...issue, analysis }
      onUpdate(updatedIssue)
      setIsAnalyzing(false)
      setStreamingType(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze issue')
      setIsAnalyzing(false)
      setStreamingType(null)
    }
  }

  const handleExecute = async () => {
    setIsExecuting(true)
    setError(null)
    setStreamingType('execution')
    try {
      const execution = await executeIssue(issue.number)
      
      // Start streaming if we got a session ID
      if (execution.session_id && execution.session_id !== 'fallback-execution') {
        setStreamingSessionId(execution.session_id)
      } else {
        // No streaming available, just update immediately
        const updatedIssue = { ...issue, execution }
        onUpdate(updatedIssue)
        setIsExecuting(false)
        setStreamingType(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute plan')
      setIsExecuting(false)
      setStreamingType(null)
    }
  }

  const handleStreamComplete = (sessionId: string, hasUpdatedAnalysis?: boolean) => {
    // Re-fetch the issue to get updated analysis/execution results
    if (streamingType === 'analysis') {
      setIsAnalyzing(false)
      
      // If the backend updated the analysis, refresh the issue data
      if (hasUpdatedAnalysis) {
        setTimeout(async () => {
          try {
            const updatedIssue = await getIssue(issue.number)
            onUpdate(updatedIssue)
          } catch (error) {
            console.error('Failed to refresh issue after analysis completion:', error)
          }
        }, 500) // Small delay to ensure backend has processed the update
      }
    } else if (streamingType === 'execution') {
      setIsExecuting(false)
      
      if (hasUpdatedAnalysis) {
        setTimeout(async () => {
          try {
            const updatedIssue = await getIssue(issue.number)
            onUpdate(updatedIssue)
          } catch (error) {
            console.error('Failed to refresh issue after execution completion:', error)
          }
        }, 500)
      }
    }
    
    setStreamingSessionId(null)
    setStreamingType(null)
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
              disabled={isAnalyzing}
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
        {streamingSessionId && streamingType && (
          <div className="mt-6">
            <StreamingProgress 
              sessionId={streamingSessionId}
              onComplete={handleStreamComplete}
              title={streamingType === 'analysis' ? 'Analyzing with Devin...' : 'Implementing with Devin...'}
            />
          </div>
        )}

        {/* Analysis Panel */}
        {issue.analysis && !(streamingSessionId && streamingType === 'execution') && (
          <div className="mt-6">
            <AnalysisPanel analysis={issue.analysis} execution={issue.execution} />
          </div>
        )}
      </div>
    </div>
  )
}


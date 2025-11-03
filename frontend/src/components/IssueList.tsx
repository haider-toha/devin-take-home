import { useState, useEffect } from 'react'
import { getIssues, GitHubIssue } from '../services/api'
import IssueCard from './IssueCard'

export default function IssueList() {
  const [issues, setIssues] = useState<GitHubIssue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'open' | 'closed' | 'all'>('open')

  useEffect(() => {
    fetchIssues()
  }, [filter])

  const fetchIssues = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getIssues(filter)
      setIssues(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch issues')
    } finally {
      setLoading(false)
    }
  }

  const updateIssue = (updatedIssue: GitHubIssue) => {
    setIssues(issues.map(issue => 
      issue.number === updatedIssue.number ? updatedIssue : issue
    ))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading issues...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h3 className="text-red-800 font-semibold mb-2">Error loading issues</h3>
        <p className="text-red-600">{error}</p>
        <button
          onClick={fetchIssues}
          className="mt-4 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">
          GitHub Issues ({issues.length})
        </h2>
        <div className="flex gap-2">
          {(['open', 'closed', 'all'] as const).map((state) => (
            <button
              key={state}
              onClick={() => setFilter(state)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                filter === state
                  ? 'bg-primary-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border border-gray-300'
              }`}
            >
              {state.charAt(0).toUpperCase() + state.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {issues.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm p-12 text-center">
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No issues found</h3>
          <p className="text-gray-600">
            {filter === 'open' ? 'No open issues in this repository.' : 
             filter === 'closed' ? 'No closed issues in this repository.' :
             'No issues in this repository.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {issues.map((issue) => (
            <IssueCard
              key={issue.number}
              issue={issue}
              onUpdate={updateIssue}
            />
          ))}
        </div>
      )}
    </div>
  )
}


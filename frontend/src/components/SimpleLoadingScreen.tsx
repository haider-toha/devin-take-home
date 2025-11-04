import { useState, useEffect, useRef } from 'react'
import { StreamEvent, streamSessionUpdates } from '../services/api'

interface SimpleLoadingScreenProps {
  sessionId: string
  type: 'analysis' | 'execution'
  onComplete?: (sessionId: string, completionData?: any) => void
}

export default function SimpleLoadingScreen({ sessionId, type, onComplete }: SimpleLoadingScreenProps) {
  const [isCompleted, setIsCompleted] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [completionData, setCompletionData] = useState<any>(null)
  const cleanupRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    if (!sessionId) return

    const cleanup = streamSessionUpdates(
      sessionId,
      (event: StreamEvent) => {
        switch (event.type) {
          case 'completed':
            setIsCompleted(true)
            setCompletionData(event.data)
            onComplete?.(sessionId, event.data)
            break

          case 'error':
            setError(`Error: ${event.data.error}`)
            break

          case 'fatal_error':
            setError(`Connection failed: ${event.data.error}`)
            setIsCompleted(true)
            break
        }
      },
      (error: Error) => {
        setError(error.message)
      },
      () => {
        setIsCompleted(true)
      }
    )

    cleanupRef.current = cleanup

    return () => {
      cleanup()
    }
  }, [sessionId, onComplete])

  const title = type === 'analysis' ? 'Analyzing with Devin' : 'Implementing with Devin'
  const description = type === 'analysis'
    ? 'Devin is analyzing the issue and creating an implementation plan. This may take a few minutes...'
    : 'Devin is working on implementing the solution and creating a pull request. This may take several minutes...'

  // Show completion message for execution
  if (isCompleted && type === 'execution' && !error) {
    const prUrl = completionData?.pr_url
    const prNumber = completionData?.pr_number

    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mt-6">
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xl">✓</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Implementation Complete!</h3>
              <p className="text-sm text-gray-600">Devin has finished working on your issue</p>
            </div>
          </div>
        </div>

        <div className="px-6 py-6">
          {prUrl ? (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">✓</span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 mb-2">
                      Pull Request Created
                    </p>
                    <p className="text-sm text-gray-600 mb-3">
                      Devin has created pull request #{prNumber} with the implementation.
                      Please review the changes on GitHub.
                    </p>
                    <a
                      href={prUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
                    >
                      View Pull Request on GitHub
                      <span>↗</span>
                    </a>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t border-gray-200">
                <span>Session completed successfully</span>
                <a
                  href={`https://app.devin.ai/sessions/${sessionId.replace('devin-', '')}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 font-medium"
                >
                  View Devin Session →
                </a>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl font-bold">i</span>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 mb-2">
                      Implementation Completed
                    </p>
                    <p className="text-sm text-gray-600 mb-3">
                      Devin has finished working on the implementation.
                      Check the Devin session or your GitHub repository for the pull request.
                    </p>
                    <div className="flex gap-3">
                      <a
                        href={`https://app.devin.ai/sessions/${sessionId.replace('devin-', '')}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 transition"
                      >
                        View Devin Session
                        <span>↗</span>
                      </a>
                      <a
                        href={`https://github.com/${completionData?.repo || 'your-repo'}/pulls`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 bg-gray-100 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-200 transition"
                      >
                        Check GitHub PRs
                        <span>↗</span>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Show completion message for analysis
  if (isCompleted && type === 'analysis' && !error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mt-6">
        <div className="bg-gradient-to-r from-green-50 to-blue-50 border-b border-gray-200 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xl">✓</span>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Analysis Complete!</h3>
              <p className="text-sm text-gray-600">Review the implementation plan below</p>
            </div>
          </div>
        </div>
        <div className="px-6 py-4">
          <a
            href={`https://app.devin.ai/sessions/${sessionId.replace('devin-', '')}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            View Devin Session →
          </a>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mt-6">
        <div className="bg-red-50 border-b border-red-200 px-6 py-4">
          <h3 className="text-lg font-semibold text-red-900">Error</h3>
        </div>
        <div className="px-6 py-4">
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      </div>
    )
  }

  // Show loading state
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mt-6">
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="text-sm text-gray-600">Please wait...</p>
          </div>
        </div>
      </div>

      <div className="px-6 py-8">
        <div className="space-y-6">
          <div className="text-center">
            <p className="text-gray-700 mb-4">{description}</p>

            {/* Animated progress indicator */}
            <div className="flex items-center justify-center gap-2 mb-6">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
            </div>
          </div>

          {/* Info boxes */}
          <div className="grid grid-cols-1 gap-4">
            <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div className="flex items-start gap-3">
                <div>
                  <p className="text-sm font-medium text-gray-900 mb-1">
                    {type === 'analysis' ? 'Reading and Understanding' : 'Working on Implementation'}
                  </p>
                  <p className="text-xs text-gray-600">
                    {type === 'analysis'
                      ? 'Devin is analyzing the issue requirements, existing code, and planning the best approach.'
                      : 'Devin is writing code, running tests, and preparing a pull request with the changes.'
                    }
                  </p>
                </div>
              </div>
            </div>

            {type === 'execution' && (
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div className="flex items-start gap-3">
                  <div>
                    <p className="text-sm font-medium text-gray-900 mb-1">
                      This may take a while
                    </p>
                    <p className="text-xs text-gray-600">
                      Implementation typically takes 5-15 minutes depending on complexity.
                      You can safely navigate away and check back later.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="text-center pt-4 border-t border-gray-200">
            <a
              href={`https://app.devin.ai/sessions/${sessionId.replace('devin-', '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              Watch live progress in Devin →
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

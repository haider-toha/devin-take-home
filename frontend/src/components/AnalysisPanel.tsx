import { Analysis, Execution } from '../services/api'
import ConfidenceBar from './ConfidenceBar'

interface AnalysisPanelProps {
  analysis: Analysis
  execution?: Execution
}

export default function AnalysisPanel({ analysis, execution }: AnalysisPanelProps) {
  return (
    <div className="border-t border-gray-200 pt-6">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <span></span>
          Devin AI Analysis
        </h3>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
          analysis.status === 'completed' 
            ? 'bg-green-100 text-green-800' 
            : 'bg-yellow-100 text-yellow-800'
        }`}>
          {analysis.status}
        </span>
      </div>

      {/* Summary */}
      <div className="mb-6">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Summary</h4>
        <p className="text-gray-700 bg-gray-50 rounded-lg p-4 leading-relaxed">
          {analysis.summary}
        </p>
      </div>

      {/* Confidence Score */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-semibold text-gray-700">Confidence Score</h4>
          {analysis.complexity && (
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              analysis.complexity === 'Low' ? 'bg-green-100 text-green-800' :
              analysis.complexity === 'High' ? 'bg-red-100 text-red-800' :
              'bg-yellow-100 text-yellow-800'
            }`}>
              {analysis.complexity} Complexity
            </span>
          )}
        </div>
        <ConfidenceBar confidence={analysis.confidence} />
      </div>

      {/* Implementation Steps */}
      {analysis.steps && analysis.steps.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-semibold text-gray-700">
              Proposed Implementation Steps
            </h4>
          </div>
          <div className="space-y-2">
            {analysis.steps.map((step, index) => (
              <div
                key={index}
                className="flex items-start gap-3 bg-blue-50 rounded-lg p-3 border border-blue-100"
              >
                <div className="flex-shrink-0 w-6 h-6 bg-primary-600 text-white rounded-full flex items-center justify-center text-sm font-semibold">
                  {index + 1}
                </div>
                <p className="text-gray-700 flex-1">{step}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Potential Challenges */}
      {analysis.potential_challenges && analysis.potential_challenges.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Potential Challenges</h4>
          <div className="space-y-2">
            {analysis.potential_challenges.map((challenge, index) => (
              <div
                key={index}
                className="flex items-start gap-2 bg-yellow-50 rounded-lg p-3 border border-yellow-100"
              >
                <span className="flex-shrink-0 text-yellow-600 text-lg">⚠️</span>
                <p className="text-gray-700 text-sm">{challenge}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Success Criteria */}
      {analysis.success_criteria && analysis.success_criteria.length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Success Criteria</h4>
          <div className="space-y-2">
            {analysis.success_criteria.map((criteria, index) => (
              <div
                key={index}
                className="flex items-start gap-2 bg-green-50 rounded-lg p-3 border border-green-100"
              >
                <span className="flex-shrink-0 text-green-600 text-lg">✅</span>
                <p className="text-gray-700 text-sm">{criteria}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Session Link */}
      {analysis.session_url && analysis.session_id !== 'fallback-session' && (
        <div className="mb-4 bg-gray-50 border border-gray-200 rounded-lg p-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Devin Session</p>
              <p className="text-xs text-gray-500 mt-1">View detailed analysis progress and AI reasoning</p>
            </div>
            <a
              href={analysis.session_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:text-primary-700 bg-white px-3 py-2 border border-primary-200 rounded-md hover:bg-primary-50 transition-colors"
            >
              View Session
              <span>↗</span>
            </a>
          </div>
        </div>
      )}

      {/* Note (if fallback analysis) */}
      {analysis.note && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-3">
          <p className="text-yellow-800 text-sm">
            <strong>Note:</strong> {analysis.note}
          </p>
        </div>
      )}

      {/* Execution Status */}
      {execution && (
        <div className="mt-6 border-t border-gray-200 pt-4">
          <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            Execution Status
          </h4>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-green-900">
                {execution.message}
              </span>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                execution.status === 'running' 
                  ? 'bg-blue-100 text-blue-800' 
                  : execution.status === 'completed'
                  ? 'bg-green-100 text-green-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {execution.status}
              </span>
            </div>
            {execution.session_url && (
              <a
                href={execution.session_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary-600 hover:text-primary-700 font-medium flex items-center gap-1"
              >
                View Devin Session
                <span>↗</span>
              </a>
            )}
            <p className="text-sm text-green-700 mt-2">
              Session ID: <code className="font-mono bg-green-100 px-2 py-1 rounded">{execution.session_id}</code>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}


interface ConfidenceBarProps {
  confidence: number
}

export default function ConfidenceBar({ confidence }: ConfidenceBarProps) {
  const percentage = Math.round(confidence * 100)
  
  const getColor = () => {
    if (percentage >= 70) return 'bg-green-500'
    if (percentage >= 40) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  const getTextColor = () => {
    if (percentage >= 70) return 'text-green-700'
    if (percentage >= 40) return 'text-yellow-700'
    return 'text-red-700'
  }

  const getLabel = () => {
    if (percentage >= 80) return 'Very High'
    if (percentage >= 70) return 'High'
    if (percentage >= 50) return 'Moderate'
    if (percentage >= 30) return 'Low'
    return 'Very Low'
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className={`text-sm font-semibold ${getTextColor()}`}>
          {percentage}% - {getLabel()}
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 ${getColor()} transition-all duration-500 ease-out rounded-full`}
          style={{ width: `${percentage}%` }}
        >
          <div className="h-full w-full bg-white opacity-20 animate-pulse"></div>
        </div>
      </div>
      <div className="mt-2 text-xs text-gray-600">
        This score indicates Devin's confidence in successfully implementing this solution.
      </div>
    </div>
  )
}


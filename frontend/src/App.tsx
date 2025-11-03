import { useState, useEffect } from 'react'
import IssueList from './components/IssueList'
import Header from './components/Header'
import { getHealthStatus } from './services/api'

function App() {
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean>(false)
  const [backendRepo, setBackendRepo] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    checkBackendHealth()
  }, [])

  const checkBackendHealth = async () => {
    try {
      const health = await getHealthStatus()
      setIsBackendHealthy(health.status === 'healthy')
      setBackendRepo(health.repo)
    } catch (error) {
      console.error('Backend health check failed:', error)
      setIsBackendHealthy(false)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Connecting to backend...</p>
        </div>
      </div>
    )
  }

  if (!isBackendHealthy) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="max-w-md bg-white rounded-lg shadow-lg p-8">
          <div className="text-red-600 text-5xl mb-4">!</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Backend Not Configured</h2>
          <p className="text-gray-600 mb-4">
            Please configure your environment variables in the backend:
          </p>
          <ul className="list-disc list-inside text-sm text-gray-600 space-y-2">
            <li>GITHUB_TOKEN - Your GitHub Personal Access Token</li>
            <li>GITHUB_REPO - Repository in format owner/repo</li>
            <li>DEVIN_API_KEY - Your Devin API Key</li>
          </ul>
          <button
            onClick={checkBackendHealth}
            className="mt-6 w-full bg-primary-600 text-white py-2 px-4 rounded-lg hover:bg-primary-700 transition"
          >
            Retry Connection
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header repo={backendRepo} />
      <main className="container mx-auto px-4 py-8">
        <IssueList />
      </main>
    </div>
  )
}

export default App


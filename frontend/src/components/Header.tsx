interface HeaderProps {
  repo: string | null
}

export default function Header({ repo }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
              Devin Issue Assistant
            </h1>
            {repo && (
              <p className="text-sm text-gray-600 mt-2">
                Repository: <span className="font-mono font-semibold text-primary-600">{repo}</span>
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-green-50 px-4 py-2 rounded-lg border border-green-200">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-green-700">Connected</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}


export default function DeploymentsLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-48 bg-surface-overlay rounded mb-2" />
          <div className="h-4 w-64 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-40 bg-surface-overlay rounded" />
      </div>

      {/* Stats skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-surface-overlay rounded-lg" />
              <div>
                <div className="h-3 w-16 bg-surface-overlay rounded mb-1" />
                <div className="h-6 w-12 bg-surface-overlay rounded" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Grid skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="card p-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-surface-overlay rounded-lg" />
                <div>
                  <div className="h-5 w-32 bg-surface-overlay rounded mb-1" />
                  <div className="h-3 w-20 bg-surface-overlay rounded" />
                </div>
              </div>
              <div className="h-6 w-16 bg-surface-overlay rounded-full" />
            </div>
            <div className="space-y-2">
              <div className="h-3 w-full bg-surface-overlay rounded" />
              <div className="h-3 w-3/4 bg-surface-overlay rounded" />
            </div>
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border-subtle">
              <div className="h-8 w-20 bg-surface-overlay rounded" />
              <div className="h-8 w-20 bg-surface-overlay rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

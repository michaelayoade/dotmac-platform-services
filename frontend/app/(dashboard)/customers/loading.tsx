export default function CustomersLoading() {
  return (
    <div className="space-y-6 animate-pulse">
      {/* Header skeleton */}
      <div className="flex items-center justify-between">
        <div>
          <div className="h-8 w-48 bg-surface-overlay rounded mb-2" />
          <div className="h-4 w-64 bg-surface-overlay rounded" />
        </div>
        <div className="h-10 w-32 bg-surface-overlay rounded" />
      </div>

      {/* Stats skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="card p-4">
            <div className="h-4 w-20 bg-surface-overlay rounded mb-2" />
            <div className="h-8 w-16 bg-surface-overlay rounded" />
          </div>
        ))}
      </div>

      {/* Filters skeleton */}
      <div className="flex items-center gap-4">
        <div className="h-10 w-64 bg-surface-overlay rounded" />
        <div className="h-10 w-32 bg-surface-overlay rounded" />
        <div className="h-10 w-32 bg-surface-overlay rounded" />
      </div>

      {/* Table skeleton */}
      <div className="card">
        <div className="p-4 border-b border-border-subtle">
          <div className="flex items-center gap-4">
            <div className="h-4 w-8 bg-surface-overlay rounded" />
            <div className="h-4 w-32 bg-surface-overlay rounded" />
            <div className="h-4 w-48 bg-surface-overlay rounded" />
            <div className="h-4 w-24 bg-surface-overlay rounded" />
            <div className="h-4 w-24 bg-surface-overlay rounded" />
          </div>
        </div>
        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
          <div key={i} className="p-4 border-b border-border-subtle last:border-0">
            <div className="flex items-center gap-4">
              <div className="h-4 w-8 bg-surface-overlay rounded" />
              <div className="h-4 w-32 bg-surface-overlay rounded" />
              <div className="h-4 w-48 bg-surface-overlay rounded" />
              <div className="h-4 w-24 bg-surface-overlay rounded" />
              <div className="h-4 w-24 bg-surface-overlay rounded" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

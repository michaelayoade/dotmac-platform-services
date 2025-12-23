import { Loader2 } from "lucide-react";

export default function DashboardLoading() {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="flex flex-col items-center gap-4">
        <Loader2 className="w-8 h-8 text-accent animate-spin" />
        <p className="text-sm text-text-muted">Loading...</p>
      </div>
    </div>
  );
}

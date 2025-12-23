"use client";

import { use, useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Download,
  Search,
  Filter,
  RefreshCcw,
  Pause,
  Play,
  Terminal,
  AlertTriangle,
  Info,
  XCircle,
} from "lucide-react";
import { format } from "date-fns";
import { Button, Input } from "@dotmac/core";

import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared/page-header";
import { useDeployment, useDeploymentLogs } from "@/lib/hooks/api/use-deployments";

interface DeploymentLogsPageProps {
  params: Promise<{ id: string }>;
}

type LogLevel = "info" | "warn" | "error" | "all";

const levelColors = {
  info: "text-status-info",
  warn: "text-status-warning",
  error: "text-status-error",
};

const levelIcons = {
  info: Info,
  warn: AlertTriangle,
  error: XCircle,
};

export default function DeploymentLogsPage({ params }: DeploymentLogsPageProps) {
  const { id } = use(params);
  const router = useRouter();
  const logsContainerRef = useRef<HTMLDivElement>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState<LogLevel>("all");
  const [isStreaming, setIsStreaming] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);

  const { data: deployment } = useDeployment(id);
  const { data: logsData, refetch, isLoading } = useDeploymentLogs(id, { limit: 500 });

  // Auto-refresh when streaming
  useEffect(() => {
    if (!isStreaming) return;

    const interval = setInterval(() => {
      refetch();
    }, 2000);

    return () => clearInterval(interval);
  }, [isStreaming, refetch]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (autoScroll && logsContainerRef.current) {
      logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
    }
  }, [logsData, autoScroll]);

  const filteredLogs = (logsData?.logs || []).filter((log) => {
    const matchesSearch = searchQuery
      ? log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
        log.pod?.toLowerCase().includes(searchQuery.toLowerCase())
      : true;
    const matchesLevel = levelFilter === "all" || log.level === levelFilter;
    return matchesSearch && matchesLevel;
  });

  const handleDownload = () => {
    const content = filteredLogs
      .map((log) => `[${format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss")}] [${log.level.toUpperCase()}] ${log.pod ? `[${log.pod}]` : ""} ${log.message}`)
      .join("\n");

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${deployment?.name || "deployment"}-logs-${format(new Date(), "yyyy-MM-dd-HHmmss")}.log`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleScroll = () => {
    if (!logsContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = logsContainerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
    setAutoScroll(isAtBottom);
  };

  return (
    <div className="h-[calc(100vh-10rem)] flex flex-col space-y-4 animate-fade-up">
      {/* Page Header */}
      <PageHeader
        title="Deployment Logs"
        breadcrumbs={[
          { label: "Deployments", href: "/deployments" },
          { label: deployment?.name || "...", href: `/deployments/${id}` },
          { label: "Logs" },
        ]}
        actions={
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
        }
      />

      {/* Controls */}
      <div className="flex items-center gap-4 flex-wrap">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search logs..."
            className="pl-10"
          />
        </div>

        {/* Level Filter */}
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-text-muted" />
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value as LogLevel)}
            className="px-3 py-2 bg-surface-primary border border-border-subtle rounded-md text-sm"
          >
            <option value="all">All Levels</option>
            <option value="info">Info</option>
            <option value="warn">Warning</option>
            <option value="error">Error</option>
          </select>
        </div>

        <div className="flex-1" />

        {/* Stream Control */}
        <Button
          variant={isStreaming ? "default" : "outline"}
          size="sm"
          onClick={() => setIsStreaming(!isStreaming)}
        >
          {isStreaming ? (
            <>
              <Pause className="w-4 h-4 mr-2" />
              Pause
            </>
          ) : (
            <>
              <Play className="w-4 h-4 mr-2" />
              Resume
            </>
          )}
        </Button>

        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCcw className="w-4 h-4" />
        </Button>

        <Button variant="outline" size="sm" onClick={handleDownload}>
          <Download className="w-4 h-4 mr-2" />
          Download
        </Button>
      </div>

      {/* Log Status Bar */}
      <div className="flex items-center justify-between px-4 py-2 bg-surface-overlay rounded-lg text-sm">
        <div className="flex items-center gap-4">
          <span className="text-text-muted">
            {filteredLogs.length} log entries
            {searchQuery && ` matching "${searchQuery}"`}
          </span>
          {isStreaming && (
            <span className="flex items-center gap-1.5 text-status-success">
              <span className="w-2 h-2 bg-status-success rounded-full animate-pulse" />
              Streaming
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 text-text-muted">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-status-info" />
            {filteredLogs.filter((l) => l.level === "info").length} info
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-status-warning" />
            {filteredLogs.filter((l) => l.level === "warn").length} warn
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-status-error" />
            {filteredLogs.filter((l) => l.level === "error").length} error
          </span>
        </div>
      </div>

      {/* Logs Container */}
      <div
        ref={logsContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-auto bg-surface-primary border border-border-subtle rounded-lg font-mono text-sm"
      >
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="flex items-center gap-3 text-text-muted">
              <RefreshCcw className="w-5 h-5 animate-spin" />
              <span>Loading logs...</span>
            </div>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-text-muted">
            <Terminal className="w-12 h-12 mb-4 opacity-50" />
            <p className="text-lg font-medium">No logs found</p>
            <p className="text-sm">
              {searchQuery ? "Try adjusting your search query" : "Logs will appear here when available"}
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-1">
            {filteredLogs.map((log, index) => {
              const LevelIcon = levelIcons[log.level];
              return (
                <div
                  key={index}
                  className={cn(
                    "flex items-start gap-3 py-1.5 px-2 rounded hover:bg-surface-overlay transition-colors",
                    log.level === "error" && "bg-status-error/5"
                  )}
                >
                  {/* Timestamp */}
                  <span className="text-text-muted whitespace-nowrap shrink-0">
                    {format(new Date(log.timestamp), "HH:mm:ss.SSS")}
                  </span>

                  {/* Level */}
                  <span
                    className={cn(
                      "w-16 shrink-0 flex items-center gap-1",
                      levelColors[log.level]
                    )}
                  >
                    <LevelIcon className="w-3 h-3" />
                    {log.level.toUpperCase()}
                  </span>

                  {/* Pod */}
                  {log.pod && (
                    <span className="text-accent shrink-0 max-w-[120px] truncate">
                      [{log.pod}]
                    </span>
                  )}

                  {/* Message */}
                  <span
                    className={cn(
                      "flex-1 break-all",
                      log.level === "error" ? "text-status-error" : "text-text-primary"
                    )}
                  >
                    {log.message}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Auto-scroll indicator */}
      {!autoScroll && (
        <button
          onClick={() => {
            setAutoScroll(true);
            if (logsContainerRef.current) {
              logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
            }
          }}
          className="fixed bottom-8 right-8 px-4 py-2 bg-accent text-text-inverse rounded-full shadow-lg hover:bg-accent-hover transition-colors flex items-center gap-2"
        >
          <span>Jump to latest</span>
          <ArrowLeft className="w-4 h-4 rotate-[-90deg]" />
        </button>
      )}
    </div>
  );
}

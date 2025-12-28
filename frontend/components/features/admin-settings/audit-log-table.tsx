"use client";

import { useState } from "react";
import { ChevronDown, ChevronRight, Clock, User, Globe, MonitorSmartphone } from "lucide-react";
import { cn } from "@/lib/utils";
import { getCategoryConfig } from "@/lib/config/admin-settings";
import type { AuditLog } from "@/lib/api/admin-settings";

interface AuditLogTableProps {
  logs: AuditLog[];
}

export function AuditLogTable({ logs }: AuditLogTableProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  if (logs.length === 0) {
    return (
      <div className="card p-8 text-center">
        <Clock className="w-12 h-12 text-text-muted mx-auto mb-4" />
        <h3 className="text-lg font-medium text-text-primary mb-2">
          No audit logs yet
        </h3>
        <p className="text-text-muted">
          Settings changes will appear here once they are made.
        </p>
      </div>
    );
  }

  return (
    <div className="card overflow-hidden">
      <table className="w-full" aria-label="Settings audit log"><caption className="sr-only">Settings audit log</caption>
        <thead>
          <tr className="border-b border-border bg-surface-overlay/50">
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider w-8" />
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
              Timestamp
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
              User
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
              Category
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
              Action
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-text-muted uppercase tracking-wider">
              Changes
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {logs.map((log) => {
            const isExpanded = expandedId === log.id;
            const config = getCategoryConfig(log.category);
            const Icon = config.icon;
            const changeCount = Object.keys(log.changes).length;

            return (
              <>
                <tr
                  key={log.id}
                  className={cn(
                    "hover:bg-surface-overlay/30 cursor-pointer transition-colors",
                    isExpanded && "bg-surface-overlay/50"
                  )}
                  onClick={() => setExpandedId(isExpanded ? null : log.id)}
                >
                  <td className="px-4 py-3">
                    <button
                      className="p-1 hover:bg-surface-overlay rounded transition-colors"
                      aria-expanded={isExpanded}
                      aria-controls={`audit-details-${log.id}`}
                      aria-label={isExpanded ? "Collapse row details" : "Expand row details"}
                    >
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-text-muted" aria-hidden="true" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-text-muted" aria-hidden="true" />
                      )}
                    </button>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-text-muted" />
                      <span className="text-sm text-text-primary">
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <User className="w-4 h-4 text-text-muted" />
                      <span className="text-sm text-text-primary">
                        {log.userEmail}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Icon className={cn("w-4 h-4", config.color)} />
                      <span className="text-sm text-text-primary">
                        {config.label}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn(
                      "text-xs px-2 py-1 rounded-full font-medium",
                      log.action === "update" && "bg-accent-subtle text-accent",
                      log.action === "restore" && "bg-warning-subtle text-warning",
                      log.action === "reset" && "bg-danger-subtle text-danger",
                      log.action === "import" && "bg-success-subtle text-success"
                    )}>
                      {log.action}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-sm text-text-muted">
                      {changeCount} field{changeCount !== 1 ? "s" : ""}
                    </span>
                  </td>
                </tr>

                {/* Expanded Details */}
                {isExpanded && (
                  <tr key={`${log.id}-details`}>
                    <td colSpan={6} className="px-4 py-4 bg-surface-overlay/30">
                      <div className="pl-8 space-y-4">
                        {/* Meta Info */}
                        <div className="flex flex-wrap gap-6 text-sm text-text-muted">
                          {log.reason && (
                            <div>
                              <span className="font-medium">Reason:</span>{" "}
                              {log.reason}
                            </div>
                          )}
                          {log.ipAddress && (
                            <div className="flex items-center gap-1.5">
                              <Globe className="w-4 h-4" />
                              {log.ipAddress}
                            </div>
                          )}
                          {log.userAgent && (
                            <div className="flex items-center gap-1.5">
                              <MonitorSmartphone className="w-4 h-4" />
                              <span className="truncate max-w-xs" title={log.userAgent}>
                                {log.userAgent.split(" ")[0]}
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Changes */}
                        <div>
                          <h4 className="text-sm font-medium text-text-primary mb-2">
                            Changed Fields
                          </h4>
                          <div className="bg-surface-base rounded-lg border border-border overflow-hidden">
                            <table className="w-full text-sm" aria-label="Field changes"><caption className="sr-only">Field changes</caption>
                              <thead>
                                <tr className="border-b border-border bg-surface-overlay/50">
                                  <th className="px-3 py-2 text-left text-xs font-medium text-text-muted">
                                    Field
                                  </th>
                                  <th className="px-3 py-2 text-left text-xs font-medium text-text-muted">
                                    Previous Value
                                  </th>
                                  <th className="px-3 py-2 text-left text-xs font-medium text-text-muted">
                                    New Value
                                  </th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-border">
                                {Object.entries(log.changes).map(([field, change]) => (
                                  <tr key={field}>
                                    <td className="px-3 py-2 font-mono text-text-primary">
                                      {field}
                                    </td>
                                    <td className="px-3 py-2 font-mono text-danger">
                                      {formatValue(change.old)}
                                    </td>
                                    <td className="px-3 py-2 font-mono text-success">
                                      {formatValue(change.new)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return "(empty)";
  }
  if (typeof value === "boolean") {
    return value ? "true" : "false";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  const str = String(value);
  if (str.length > 50) {
    return str.substring(0, 47) + "...";
  }
  return str;
}

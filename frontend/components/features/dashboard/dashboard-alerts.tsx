"use client";

import { AlertCircle, AlertTriangle, Info, ExternalLink } from "lucide-react";
import Link from "next/link";
import type { DashboardAlert } from "@/lib/api/types/dashboard";

interface DashboardAlertsProps {
  alerts: DashboardAlert[];
  className?: string;
}

/**
 * Alert styles mapped to design tokens:
 * - info → primary (blue)
 * - warning → alert (orange)
 * - error → critical (red)
 */
const alertStyles = {
  info: {
    bg: "bg-blue-50 dark:bg-blue-950/20",
    border: "border-blue-200 dark:border-blue-800",
    icon: "text-blue-600 dark:text-blue-400",
    title: "text-blue-900 dark:text-blue-100",
    text: "text-blue-700 dark:text-blue-300",
  },
  warning: {
    bg: "bg-orange-50 dark:bg-orange-950/20",
    border: "border-orange-200 dark:border-orange-800",
    icon: "text-orange-600 dark:text-orange-400",
    title: "text-orange-900 dark:text-orange-100",
    text: "text-orange-700 dark:text-orange-300",
  },
  error: {
    bg: "bg-red-50 dark:bg-red-950/20",
    border: "border-red-200 dark:border-red-800",
    icon: "text-red-600 dark:text-red-400",
    title: "text-red-900 dark:text-red-100",
    text: "text-red-700 dark:text-red-300",
  },
};

const AlertIcon = ({ type }: { type: DashboardAlert["type"] }) => {
  const className = "w-5 h-5";
  switch (type) {
    case "error":
      return <AlertCircle className={className} />;
    case "warning":
      return <AlertTriangle className={className} />;
    case "info":
    default:
      return <Info className={className} />;
  }
};

export function DashboardAlerts({ alerts, className = "" }: DashboardAlertsProps) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {alerts.map((alert, index) => {
        const style = alertStyles[alert.type] || alertStyles.info;

        return (
          <div
            key={`${alert.title}-${index}`}
            className={`flex items-start gap-3 p-4 rounded-lg border ${style.bg} ${style.border}`}
          >
            <div className={`flex-shrink-0 mt-0.5 ${style.icon}`}>
              <AlertIcon type={alert.type} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h4 className={`font-medium ${style.title}`}>
                  {alert.title}
                </h4>
                {alert.count > 0 && (
                  <span className={`text-sm font-medium px-2 py-0.5 rounded-full ${style.bg} ${style.text}`}>
                    {alert.count}
                  </span>
                )}
              </div>
              <p className={`text-sm mt-1 ${style.text}`}>
                {alert.message}
              </p>
            </div>
            {alert.actionUrl && (
              <Link
                href={alert.actionUrl}
                className={`flex-shrink-0 p-1.5 rounded-md hover:bg-black/5 dark:hover:bg-white/5 transition-colors ${style.icon}`}
              >
                <ExternalLink className="w-4 h-4" />
              </Link>
            )}
          </div>
        );
      })}
    </div>
  );
}

export default DashboardAlerts;

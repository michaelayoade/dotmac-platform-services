"use client";

import { useState } from "react";
import { Eye, EyeOff, Copy, Check, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

interface SensitiveFieldProps {
  name: string;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export function SensitiveField({
  name,
  value,
  onChange,
  disabled = false,
  placeholder,
  className,
}: SensitiveFieldProps) {
  const [isRevealed, setIsRevealed] = useState(false);
  const [copied, setCopied] = useState(false);

  const isMasked = value === "••••••••" || value.startsWith("***");
  const displayValue = isRevealed ? value : isMasked ? value : "••••••••";

  const handleCopy = async () => {
    if (isMasked) return;
    await navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn("relative", className)}>
      <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
        <Lock className="w-4 h-4" />
      </div>
      <input
        type={isRevealed ? "text" : "password"}
        name={name}
        value={displayValue}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder={placeholder}
        className={cn(
          "input pl-10 pr-20 font-mono text-sm",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      />
      <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
        <button
          type="button"
          onClick={() => setIsRevealed(!isRevealed)}
          disabled={isMasked}
          className={cn(
            "p-1.5 rounded hover:bg-surface-overlay transition-colors",
            isMasked && "opacity-50 cursor-not-allowed"
          )}
          title={isRevealed ? "Hide value" : "Show value"}
        >
          {isRevealed ? (
            <EyeOff className="w-4 h-4 text-text-muted" />
          ) : (
            <Eye className="w-4 h-4 text-text-muted" />
          )}
        </button>
        <button
          type="button"
          onClick={handleCopy}
          disabled={isMasked || !value}
          className={cn(
            "p-1.5 rounded hover:bg-surface-overlay transition-colors",
            (isMasked || !value) && "opacity-50 cursor-not-allowed"
          )}
          title="Copy to clipboard"
        >
          {copied ? (
            <Check className="w-4 h-4 text-success" />
          ) : (
            <Copy className="w-4 h-4 text-text-muted" />
          )}
        </button>
      </div>
    </div>
  );
}

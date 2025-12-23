"use client";

import Image from "next/image";

import { cn } from "@/lib/utils";

interface AvatarProps {
  src?: string | null;
  name?: string;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  status?: "online" | "offline" | "away" | "busy";
}

const sizeClasses = {
  xs: "w-6 h-6 text-xs",
  sm: "w-8 h-8 text-sm",
  md: "w-10 h-10 text-base",
  lg: "w-12 h-12 text-lg",
  xl: "w-16 h-16 text-xl",
};

const statusSizeClasses = {
  xs: "w-2 h-2",
  sm: "w-2.5 h-2.5",
  md: "w-3 h-3",
  lg: "w-3.5 h-3.5",
  xl: "w-4 h-4",
};

const statusColors = {
  online: "bg-status-success",
  offline: "bg-text-muted",
  away: "bg-status-warning",
  busy: "bg-status-error",
};

const sizePx = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 48,
  xl: 64,
};

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) {
    return parts[0].charAt(0).toUpperCase();
  }
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

function getColorFromName(name: string): string {
  // Generate a consistent color based on the name
  const colors = [
    "from-accent to-highlight",
    "from-status-success to-accent",
    "from-highlight to-status-warning",
    "from-accent to-status-info",
    "from-status-info to-highlight",
    "from-status-success to-highlight",
  ];

  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
}

export function Avatar({
  src,
  name = "User",
  size = "md",
  className,
  status,
}: AvatarProps) {
  const initials = getInitials(name);
  const gradientClass = getColorFromName(name);
  const imageLoader = ({ src: imageSrc }: { src: string }) => imageSrc;

  return (
    <div className={cn("relative inline-block", className)}>
      {src ? (
        <Image
          src={src}
          alt={name}
          width={sizePx[size]}
          height={sizePx[size]}
          className={cn(
            "rounded-full object-cover bg-surface-overlay",
            sizeClasses[size]
          )}
          loader={imageLoader}
          unoptimized
        />
      ) : (
        <div
          className={cn(
            "rounded-full flex items-center justify-center font-semibold text-text-inverse bg-gradient-to-br",
            gradientClass,
            sizeClasses[size]
          )}
        >
          {initials}
        </div>
      )}
      {status && (
        <span
          className={cn(
            "absolute bottom-0 right-0 rounded-full ring-2 ring-surface-elevated",
            statusColors[status],
            statusSizeClasses[size]
          )}
        />
      )}
    </div>
  );
}

interface AvatarGroupProps {
  avatars: Array<{ src?: string; name: string }>;
  max?: number;
  size?: "xs" | "sm" | "md" | "lg";
  className?: string;
}

export function AvatarGroup({
  avatars,
  max = 4,
  size = "sm",
  className,
}: AvatarGroupProps) {
  const displayed = avatars.slice(0, max);
  const remaining = avatars.length - max;

  return (
    <div className={cn("flex -space-x-2", className)}>
      {displayed.map((avatar, index) => (
        <Avatar
          key={index}
          src={avatar.src}
          name={avatar.name}
          size={size}
          className="ring-2 ring-surface-elevated"
        />
      ))}
      {remaining > 0 && (
        <div
          className={cn(
            "rounded-full flex items-center justify-center font-medium bg-surface-overlay text-text-muted ring-2 ring-surface-elevated",
            sizeClasses[size]
          )}
        >
          +{remaining}
        </div>
      )}
    </div>
  );
}

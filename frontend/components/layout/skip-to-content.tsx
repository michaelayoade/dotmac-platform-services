"use client";

interface SkipToContentProps {
  /** ID of the target element to skip to */
  targetId?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Skip-to-content link for keyboard navigation
 * Visually hidden by default, appears on focus
 */
export function SkipToContent({
  targetId = "main-content",
  className,
}: SkipToContentProps) {
  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    const target = document.getElementById(targetId);
    if (target) {
      target.focus();
      target.scrollIntoView();
    }
  };

  return (
    <a
      href={`#${targetId}`}
      onClick={handleClick}
      className={[
        // Visually hidden by default
        "absolute -top-full left-4 z-[100]",
        "px-4 py-2 rounded-md",
        "bg-accent text-text-inverse font-medium text-sm",
        "transition-all duration-150",
        // Show on focus
        "focus:top-4",
        "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      Skip to main content
    </a>
  );
}

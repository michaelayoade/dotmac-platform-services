/**
 * Animation System
 * Comprehensive animation utilities with accessibility support
 */

import React from 'react';

import { designTokens } from './tokens';

// Animation presets with reduced motion support
export const animations = {
  // Fade animations
  fadeIn: {
    keyframes: {
      '0%': { opacity: '0' },
      '100%': { opacity: '1' },
    },
    duration: designTokens.animation.duration.normal,
    easing: designTokens.animation.easing.out,
  },

  fadeOut: {
    keyframes: {
      '0%': { opacity: '1' },
      '100%': { opacity: '0' },
    },
    duration: designTokens.animation.duration.normal,
    easing: designTokens.animation.easing.in,
  },

  // Slide animations
  slideInUp: {
    keyframes: {
      '0%': {
        transform: 'translateY(100%)',
        opacity: '0',
      },
      '100%': {
        transform: 'translateY(0)',
        opacity: '1',
      },
    },
    duration: designTokens.animation.duration.slow,
    easing: designTokens.animation.easing.out,
  },

  slideInDown: {
    keyframes: {
      '0%': {
        transform: 'translateY(-100%)',
        opacity: '0',
      },
      '100%': {
        transform: 'translateY(0)',
        opacity: '1',
      },
    },
    duration: designTokens.animation.duration.slow,
    easing: designTokens.animation.easing.out,
  },

  slideInLeft: {
    keyframes: {
      '0%': {
        transform: 'translateX(-100%)',
        opacity: '0',
      },
      '100%': {
        transform: 'translateX(0)',
        opacity: '1',
      },
    },
    duration: designTokens.animation.duration.slow,
    easing: designTokens.animation.easing.out,
  },

  slideInRight: {
    keyframes: {
      '0%': {
        transform: 'translateX(100%)',
        opacity: '0',
      },
      '100%': {
        transform: 'translateX(0)',
        opacity: '1',
      },
    },
    duration: designTokens.animation.duration.slow,
    easing: designTokens.animation.easing.out,
  },

  // Scale animations
  scaleIn: {
    keyframes: {
      '0%': {
        transform: 'scale(0.95)',
        opacity: '0',
      },
      '100%': {
        transform: 'scale(1)',
        opacity: '1',
      },
    },
    duration: designTokens.animation.duration.normal,
    easing: designTokens.animation.easing.out,
  },

  scaleOut: {
    keyframes: {
      '0%': {
        transform: 'scale(1)',
        opacity: '1',
      },
      '100%': {
        transform: 'scale(0.95)',
        opacity: '0',
      },
    },
    duration: designTokens.animation.duration.normal,
    easing: designTokens.animation.easing.in,
  },

  // Bounce animations
  bounceIn: {
    keyframes: {
      '0%': {
        transform: 'scale(0.3)',
        opacity: '0',
      },
      '50%': {
        transform: 'scale(1.05)',
        opacity: '1',
      },
      '70%': {
        transform: 'scale(0.9)',
      },
      '100%': {
        transform: 'scale(1)',
      },
    },
    duration: designTokens.animation.duration.slower,
    easing: designTokens.animation.easing.bounce,
  },

  // Pulse animations
  pulse: {
    keyframes: {
      '0%, 100%': { opacity: '1' },
      '50%': { opacity: '0.5' },
    },
    duration: '2s',
    easing: designTokens.animation.easing['in-out'],
    iterationCount: 'infinite',
  },

  // Loading animations
  spin: {
    keyframes: {
      '0%': { transform: 'rotate(0deg)' },
      '100%': { transform: 'rotate(360deg)' },
    },
    duration: '1s',
    easing: designTokens.animation.easing.linear,
    iterationCount: 'infinite',
  },

  // Notification animations
  notificationSlideIn: {
    keyframes: {
      '0%': {
        transform: 'translateX(100%)',
        opacity: '0',
      },
      '100%': {
        transform: 'translateX(0)',
        opacity: '1',
      },
    },
    duration: designTokens.animation.duration.slow,
    easing: designTokens.animation.easing.out,
  },

  notificationSlideOut: {
    keyframes: {
      '0%': {
        transform: 'translateX(0)',
        opacity: '1',
      },
      '100%': {
        transform: 'translateX(100%)',
        opacity: '0',
      },
    },
    duration: designTokens.animation.duration.slow,
    easing: designTokens.animation.easing.in,
  },

  // Progress animations
  progressIndeterminate: {
    keyframes: {
      '0%': {
        transform: 'translateX(-100%)',
      },
      '50%': {
        transform: 'translateX(0%)',
      },
      '100%': {
        transform: 'translateX(100%)',
      },
    },
    duration: '2s',
    easing: designTokens.animation.easing['in-out'],
    iterationCount: 'infinite',
  },

  // Button hover animations
  buttonHover: {
    keyframes: {
      '0%': { transform: 'translateY(0)' },
      '100%': { transform: 'translateY(-1px)' },
    },
    duration: designTokens.animation.duration.fast,
    easing: designTokens.animation.easing.out,
  },

  // Card hover animations
  cardHover: {
    keyframes: {
      '0%': {
        transform: 'translateY(0)',
        boxShadow: designTokens.shadows.card,
      },
      '100%': {
        transform: 'translateY(-2px)',
        boxShadow: designTokens.shadows.lg,
      },
    },
    duration: designTokens.animation.duration.normal,
    easing: designTokens.animation.easing.out,
  },
} as const;

// CSS-in-JS animation generator
export const createAnimation = (name: keyof typeof animations) => {
  const animation = animations[name];

  return {
    '@keyframes': {
      [name]: animation.keyframes,
    },
    animation: `${name} ${animation.duration} ${animation.easing} ${animation.iterationCount || 'once'} forwards`,
  };
};

// CSS custom properties for animations
export const animationCSS = `
  :root {
    /* Animation durations */
    --animation-duration-fast: ${designTokens.animation.duration.fast};
    --animation-duration-normal: ${designTokens.animation.duration.normal};
    --animation-duration-slow: ${designTokens.animation.duration.slow};
    --animation-duration-slower: ${designTokens.animation.duration.slower};
    
    /* Animation easings */
    --animation-easing-linear: ${designTokens.animation.easing.linear};
    --animation-easing-in: ${designTokens.animation.easing.in};
    --animation-easing-out: ${designTokens.animation.easing.out};
    --animation-easing-in-out: ${designTokens.animation.easing['in-out']};
    --animation-easing-bounce: ${designTokens.animation.easing.bounce};
    --animation-easing-elastic: ${designTokens.animation.easing.elastic};
  }

  /* Keyframe definitions */
  @keyframes fadeIn {
    0% { opacity: 0; }
    100% { opacity: 1; }
  }

  @keyframes fadeOut {
    0% { opacity: 1; }
    100% { opacity: 0; }
  }

  @keyframes slideInUp {
    0% { 
      transform: translateY(100%);
      opacity: 0;
    }
    100% { 
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes slideInDown {
    0% { 
      transform: translateY(-100%);
      opacity: 0;
    }
    100% { 
      transform: translateY(0);
      opacity: 1;
    }
  }

  @keyframes slideInLeft {
    0% { 
      transform: translateX(-100%);
      opacity: 0;
    }
    100% { 
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes slideInRight {
    0% { 
      transform: translateX(100%);
      opacity: 0;
    }
    100% { 
      transform: translateX(0);
      opacity: 1;
    }
  }

  @keyframes scaleIn {
    0% { 
      transform: scale(0.95);
      opacity: 0;
    }
    100% { 
      transform: scale(1);
      opacity: 1;
    }
  }

  @keyframes scaleOut {
    0% { 
      transform: scale(1);
      opacity: 1;
    }
    100% { 
      transform: scale(0.95);
      opacity: 0;
    }
  }

  @keyframes bounceIn {
    0% {
      transform: scale(0.3);
      opacity: 0;
    }
    50% {
      transform: scale(1.05);
      opacity: 1;
    }
    70% {
      transform: scale(0.9);
    }
    100% {
      transform: scale(1);
    }
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
  }

  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  @keyframes progressIndeterminate {
    0% { transform: translateX(-100%); }
    50% { transform: translateX(0%); }
    100% { transform: translateX(100%); }
  }

  /* Utility classes */
  .animate-fade-in {
    animation: fadeIn var(--animation-duration-normal) var(--animation-easing-out) forwards;
  }

  .animate-fade-out {
    animation: fadeOut var(--animation-duration-normal) var(--animation-easing-in) forwards;
  }

  .animate-slide-in-up {
    animation: slideInUp var(--animation-duration-slow) var(--animation-easing-out) forwards;
  }

  .animate-slide-in-down {
    animation: slideInDown var(--animation-duration-slow) var(--animation-easing-out) forwards;
  }

  .animate-slide-in-left {
    animation: slideInLeft var(--animation-duration-slow) var(--animation-easing-out) forwards;
  }

  .animate-slide-in-right {
    animation: slideInRight var(--animation-duration-slow) var(--animation-easing-out) forwards;
  }

  .animate-scale-in {
    animation: scaleIn var(--animation-duration-normal) var(--animation-easing-out) forwards;
  }

  .animate-scale-out {
    animation: scaleOut var(--animation-duration-normal) var(--animation-easing-in) forwards;
  }

  .animate-bounce-in {
    animation: bounceIn var(--animation-duration-slower) var(--animation-easing-bounce) forwards;
  }

  .animate-pulse {
    animation: pulse 2s var(--animation-easing-in-out) infinite;
  }

  .animate-spin {
    animation: spin 1s var(--animation-easing-linear) infinite;
  }

  /* Hover animations */
  .hover-lift {
    transition: transform var(--animation-duration-fast) var(--animation-easing-out);
  }

  .hover-lift:hover {
    transform: translateY(-2px);
  }

  .hover-scale {
    transition: transform var(--animation-duration-fast) var(--animation-easing-out);
  }

  .hover-scale:hover {
    transform: scale(1.02);
  }

  .hover-glow {
    transition: box-shadow var(--animation-duration-normal) var(--animation-easing-out);
  }

  .hover-glow:hover {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
  }

  /* Focus animations */
  .focus-ring {
    transition: box-shadow var(--animation-duration-fast) var(--animation-easing-out);
  }

  .focus-ring:focus {
    outline: none;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
  }

  /* Reduced motion support */
  @media (prefers-reduced-motion: reduce) {
    .animate-fade-in,
    .animate-fade-out,
    .animate-slide-in-up,
    .animate-slide-in-down,
    .animate-slide-in-left,
    .animate-slide-in-right,
    .animate-scale-in,
    .animate-scale-out,
    .animate-bounce-in {
      animation: none;
      opacity: 1;
      transform: none;
    }

    .animate-pulse,
    .animate-spin {
      animation: none;
    }

    .hover-lift,
    .hover-scale,
    .hover-glow,
    .focus-ring {
      transition: none;
    }

    .hover-lift:hover,
    .hover-scale:hover {
      transform: none;
    }

    .hover-glow:hover {
      box-shadow: none;
    }
  }

  /* High contrast mode */
  @media (prefers-contrast: high) {
    .hover-glow:hover {
      box-shadow: 0 0 0 2px currentColor;
    }

    .focus-ring:focus {
      box-shadow: 0 0 0 3px currentColor;
    }
  }
`;

// React hook for animation with reduced motion support
export const useReducedMotion = () => {
  if (typeof window === 'undefined') {
    return false;
  }

  const [prefersReducedMotion, setPrefersReducedMotion] = React.useState(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    return mediaQuery.matches;
  });

  React.useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);

    const listener = (e: MediaQueryListEvent) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', listener);

    return () => mediaQuery.removeEventListener('change', listener);
  }, []);

  return prefersReducedMotion;
};

// Animation component with reduced motion support
export const AnimatedComponent: React.FC<{
  children: React.ReactNode;
  animation: keyof typeof animations;
  className?: string;
  duration?: string;
  delay?: string;
}> = ({ children, animation, className = '', duration, delay }) => {
  const prefersReducedMotion = useReducedMotion();

  if (prefersReducedMotion) {
    return React.createElement('div', { className }, children);
  }

  const animationStyles = {
    animation: `${animation} ${duration || animations[animation].duration} ${animations[animation].easing}`,
    animationDelay: delay || '0s',
    animationFillMode: 'forwards',
  };

  return React.createElement('div', { className, style: animationStyles }, children);
};

export type AnimationType = keyof typeof animations;

/**
 * Theme Switching Stress Test
 *
 * Tests theme switching between portals and color schemes to ensure:
 * - No flash of unstyled content (FOUC)
 * - Proper theme isolation
 * - CSS custom property updates
 * - Component re-rendering stability
 */

import * as React from 'react';

import {
  AdminButton,
  AdminCard,
  AdminCardContent,
  AdminCardHeader,
  AdminCardTitle,
} from '../admin';
import {
  CustomerButton,
  CustomerCard,
  CustomerCardContent,
  CustomerCardHeader,
  CustomerCardTitle,
} from '../customer';
import {
  ResellerButton,
  ResellerCard,
  ResellerCardContent,
  ResellerCardHeader,
  ResellerCardTitle,
} from '../reseller';
import { Avatar, Badge } from '../shared';

/**
 * Test component that renders the same UI with different portal themes
 */
function PortalComparison() {
  const [renderCount, setRenderCount] = React.useState(0);
  const [switchCount, setSwitchCount] = React.useState(0);

  // Track render cycles to detect unnecessary re-renders
  React.useEffect(() => {
    setRenderCount((prev) => prev + 1);
  });

  const handleThemeSwitch = () => {
    setSwitchCount((prev) => prev + 1);
  };

  return (
    <div className='space-y-8'>
      <div className='space-y-2 text-center'>
        <h2 className='font-bold text-2xl'>Theme Switching Stress Test</h2>
        <div className='text-muted-foreground text-sm'>
          Renders: {renderCount} | Theme switches: {switchCount}
        </div>
      </div>

      {/* Side-by-side portal comparison */}
      <div className='grid grid-cols-1 gap-6 lg:grid-cols-3'>
        {/* Admin Portal Theme */}
        <div className='admin-portal'>
          <ThemeProvider defaultPortal='admin' defaultColorScheme='light'>
            <PortalTestComponents title='Admin Portal' onThemeSwitch={handleThemeSwitch} />
          </ThemeProvider>
        </div>

        {/* Customer Portal Theme */}
        <div className='customer-portal'>
          <ThemeProvider defaultPortal='customer' defaultColorScheme='light'>
            <PortalTestComponents title='Customer Portal' onThemeSwitch={handleThemeSwitch} />
          </ThemeProvider>
        </div>

        {/* Reseller Portal Theme */}
        <div className='reseller-portal'>
          <ThemeProvider defaultPortal='reseller' defaultColorScheme='light'>
            <PortalTestComponents title='Reseller Portal' onThemeSwitch={handleThemeSwitch} />
          </ThemeProvider>
        </div>
      </div>
    </div>
  );
}

/**
 * Test components for each portal
 */
function PortalTestComponents({
  title,
  onThemeSwitch,
}: {
  title: string;
  onThemeSwitch: () => void;
}) {
  const { portal, colorScheme, _toggleColorScheme } = useTheme();

  const handleToggle = () => {
    toggleColorScheme();
    onThemeSwitch();
  };

  // Portal-specific components
  const ButtonComponent = {
    admin: AdminButton,
    customer: CustomerButton,
    reseller: ResellerButton,
  }[portal];

  const CardComponent = {
    admin: AdminCard,
    customer: CustomerCard,
    reseller: ResellerCard,
  }[portal];

  const CardHeaderComponent = {
    admin: AdminCardHeader,
    customer: CustomerCardHeader,
    reseller: ResellerCardHeader,
  }[portal];

  const CardTitleComponent = {
    admin: AdminCardTitle,
    customer: CustomerCardTitle,
    reseller: ResellerCardTitle,
  }[portal];

  const CardContentComponent = {
    admin: AdminCardContent,
    customer: CustomerCardContent,
    reseller: ResellerCardContent,
  }[portal];

  return (
    <div className='space-y-4'>
      <CardComponent>
        <CardHeaderComponent>
          <CardTitleComponent>{title}</CardTitleComponent>
          <div className='text-muted-foreground text-xs'>{colorScheme} mode</div>
        </CardHeaderComponent>

        <CardContentComponent>
          <div className='space-y-4'>
            {/* Test buttons with different variants */}
            <div className='space-y-2'>
              <ButtonComponent variant='default' size='sm'>
                Primary Action
              </ButtonComponent>
              <ButtonComponent variant='outline' size='sm'>
                Secondary Action
              </ButtonComponent>
              <ButtonComponent variant='destructive' size='sm'>
                Destructive Action
              </ButtonComponent>
            </div>

            {/* Test shared components that should adapt */}
            <div className='flex items-center space-x-2'>
              <Avatar fallback='TS' size='sm' />
              <Badge variant='success' size='sm'>
                Active
              </Badge>
              <Badge variant='warning' size='sm'>
                Pending
              </Badge>
            </div>

            {/* Theme toggle button */}
            <ButtonComponent
              variant='ghost'
              size='sm'
              onClick={handleToggle}
              onKeyDown={(e) => e.key === 'Enter' && handleToggle}
              className='w-full'
            >
              Toggle {colorScheme === 'light' ? 'Dark' : 'Light'} Mode
            </ButtonComponent>
          </div>
        </CardContentComponent>
      </CardComponent>
    </div>
  );
}

/**
 * Rapid theme switching test
 */
function RapidSwitchTest() {
  const [isRunning, setIsRunning] = React.useState(false);
  const [switchCount, setSwitchCount] = React.useState(0);
  const intervalRef = React.useRef<NodeJS.Timeout>();

  const startRapidSwitch = () => {
    setIsRunning(true);
    setSwitchCount(0);

    intervalRef.current = setInterval(() => {
      setSwitchCount((prev) => {
        if (prev >= 20) {
          setIsRunning(false);
          clearInterval(intervalRef.current);
          return prev;
        }

        // Toggle theme rapidly
        document.documentElement.classList.toggle('dark');
        document.documentElement.classList.toggle('light');

        return prev + 1;
      });
    }, 100); // Switch every 100ms
  };

  const stopRapidSwitch = () => {
    setIsRunning(false);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
  };

  React.useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return (
    <div className='space-y-4 text-center'>
      <h3 className='font-semibold text-lg'>Rapid Theme Switch Test</h3>
      <p className='text-muted-foreground text-sm'>
        Tests theme switching stability under rapid changes
      </p>

      <div className='space-x-2'>
        <button
          type='button'
          onClick={startRapidSwitch}
          onKeyDown={(e) => e.key === 'Enter' && startRapidSwitch}
          disabled={isRunning}
          className='rounded-md bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50'
        >
          {isRunning ? 'Running...' : 'Start Rapid Switch'}
        </button>

        <button
          type='button'
          onClick={stopRapidSwitch}
          onKeyDown={(e) => e.key === 'Enter' && stopRapidSwitch}
          disabled={!isRunning}
          className='rounded-md bg-secondary px-4 py-2 text-secondary-foreground disabled:opacity-50'
        >
          Stop
        </button>
      </div>

      <div className='text-sm'>Switches completed: {switchCount}/20</div>
    </div>
  );
}

/**
 * CSS Custom Property Change Detection
 */
function CSSPropertyTest() {
  const [properties, setProperties] = React.useState<Record<string, string>>(_props);
  const { portal, _colorScheme } = useTheme();

  React.useEffect(() => {
    // Read current CSS custom properties
    const root = document.documentElement;
    const computedStyle = getComputedStyle(root);

    const portalProps = {
      primary: computedStyle.getPropertyValue(`--${portal}-primary`).trim(),
      background: computedStyle.getPropertyValue(`--${portal}-background`).trim(),
      foreground: computedStyle.getPropertyValue(`--${portal}-foreground`).trim(),
      border: computedStyle.getPropertyValue(`--${portal}-border`).trim(),
    };

    setProperties(portalProps);
  }, [portal]);

  return (
    <div className='space-y-4'>
      <h3 className='font-semibold text-lg'>CSS Custom Properties</h3>
      <div className='grid grid-cols-2 gap-4 font-mono text-xs'>
        {Object.entries(properties).map(([key, value]) => (
          <div key={key} className='space-y-1'>
            <div className='font-semibold'>
              --{portal}-{key}
            </div>
            <div className='text-muted-foreground'>{value || 'undefined'}</div>
            <div
              className='h-6 w-full rounded border'
              style={{ backgroundColor: `hsl(${value})` }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Performance monitoring during theme switches
 */
function PerformanceMonitor() {
  const [metrics, setMetrics] = React.useState({
    renderTime: 0,
    layoutShift: 0,
    repaints: 0,
  });

  React.useEffect(() => {
    if (typeof window !== 'undefined' && 'performance' in window) {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();

        entries.forEach((entry) => {
          if (entry.entryType === 'measure') {
            setMetrics((prev) => ({
              ...prev,
              renderTime: entry.duration,
            }));
          }
        });
      });

      observer.observe({ entryTypes: ['measure'] });

      return () => observer.disconnect();
    }
  }, []);

  return (
    <div className='space-y-4'>
      <h3 className='font-semibold text-lg'>Performance Metrics</h3>
      <div className='grid grid-cols-3 gap-4 text-sm'>
        <div>
          <div className='font-semibold'>Render Time</div>
          <div className='text-muted-foreground'>{metrics.renderTime.toFixed(2)}ms</div>
        </div>
        <div>
          <div className='font-semibold'>Layout Shift</div>
          <div className='text-muted-foreground'>{metrics.layoutShift}</div>
        </div>
        <div>
          <div className='font-semibold'>Repaints</div>
          <div className='text-muted-foreground'>{metrics.repaints}</div>
        </div>
      </div>
    </div>
  );
}

/**
 * Main stress test component
 */
export function ThemeStressTest() {
  return (
    <div className='min-h-screen bg-background p-8 text-foreground'>
      <div className='mx-auto max-w-7xl space-y-12'>
        {/* Portal comparison */}
        <PortalComparison />

        {/* Rapid switching test */}
        <div className='border-t pt-8'>
          <RapidSwitchTest />
        </div>

        {/* CSS properties inspection */}
        <div className='border-t pt-8'>
          <ThemeProvider defaultPortal='admin'>
            <CSSPropertyTest />
          </ThemeProvider>
        </div>

        {/* Performance monitoring */}
        <div className='border-t pt-8'>
          <PerformanceMonitor />
        </div>
      </div>
    </div>
  );
}

export default ThemeStressTest;

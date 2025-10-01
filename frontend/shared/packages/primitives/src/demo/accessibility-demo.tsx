/**
 * Accessibility Demo - WCAG 2.1 AA Compliance Showcase
 * Demonstrates all accessibility features in the primitives package
 */

'use client';

import React, { useState, useEffect } from 'react';
import {
  RevenueChart,
  NetworkUsageChart,
  ServiceStatusChart,
  BandwidthChart,
  StatusBadge,
  UptimeIndicator,
  NetworkPerformanceIndicator,
  ServiceTierIndicator,
  AlertSeverityIndicator,
} from '../index';
import { runDevelopmentA11yTest, AccessibilityTestResult } from '../utils/a11y-testing';

// Sample data for demos
const revenueData = [
  { month: 'Jan', revenue: 65000, target: 70000, previousYear: 55000 },
  { month: 'Feb', revenue: 78000, target: 75000, previousYear: 62000 },
  { month: 'Mar', revenue: 82000, target: 80000, previousYear: 68000 },
  { month: 'Apr', revenue: 95000, target: 85000, previousYear: 75000 },
  { month: 'May', revenue: 88000, target: 90000, previousYear: 82000 },
  { month: 'Jun', revenue: 102000, target: 95000, previousYear: 88000 },
];

const networkUsageData = [
  { hour: '00:00', download: 450, upload: 120, peak: 600 },
  { hour: '06:00', download: 680, upload: 180, peak: 850 },
  { hour: '12:00', download: 920, upload: 280, peak: 1200 },
  { hour: '18:00', download: 1150, upload: 320, peak: 1450 },
  { hour: '21:00', download: 980, upload: 250, peak: 1230 },
];

const serviceStatusData = [
  { name: 'Web Services', value: 24, status: 'online' as const },
  { name: 'Email Services', value: 3, status: 'maintenance' as const },
  { name: 'DNS Services', value: 1, status: 'offline' as const },
];

const bandwidthData = [
  { time: '00:00', utilization: 45, capacity: 80 },
  { time: '06:00', utilization: 68, capacity: 80 },
  { time: '12:00', utilization: 92, capacity: 80 },
  { time: '18:00', utilization: 87, capacity: 80 },
  { time: '21:00', utilization: 73, capacity: 80 },
];

export const AccessibilityDemo: React.FC = () => {
  const [testResults, setTestResults] = useState<AccessibilityTestResult | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('online');

  // Run accessibility test on mount
  useEffect(() => {
    const timer = setTimeout(() => {
      const container = document.getElementById('accessibility-demo');
      if (container) {
        runDevelopmentA11yTest(container);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const handleStatusClick = (status: string) => {
    setSelectedStatus(status);
    console.log(`Status changed to: ${status}`);
  };

  const handleDataPointClick = (data: any, index: number, type: string) => {
    console.log(`${type} data point clicked:`, { data, index });
  };

  return (
    <div id='accessibility-demo' className='p-8 max-w-7xl mx-auto space-y-8'>
      {/* Skip Link for keyboard users */}
      <a href='#main-content' className='sr-only-focusable skip-link'>
        Skip to main content
      </a>

      {/* Page Header */}
      <header role='banner'>
        <h1 className='text-3xl font-bold text-gray-900 mb-2'>
          ISP Management Dashboard - Accessibility Demo
        </h1>
        <p className='text-lg text-gray-600 mb-4'>
          Demonstrating WCAG 2.1 AA compliant components with full screen reader support
        </p>

        {/* Accessibility Score Display */}
        {testResults && (
          <div
            className='bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6'
            role='status'
            aria-live='polite'
          >
            <h2 className='text-lg font-semibold text-blue-900 mb-2'>Accessibility Test Results</h2>
            <p className='text-blue-800'>
              Score: <strong>{testResults.score}/100</strong> | Status:{' '}
              <strong className={testResults.passed ? 'text-green-600' : 'text-red-600'}>
                {testResults.passed ? 'PASSED' : 'NEEDS IMPROVEMENT'}
              </strong>
            </p>
            <p className='text-sm text-blue-700 mt-1'>
              Issues: {testResults.summary.critical} critical, {testResults.summary.serious} serious
            </p>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main id='main-content' role='main'>
        {/* Charts Section */}
        <section aria-labelledby='charts-heading' className='mb-12'>
          <h2 id='charts-heading' className='text-2xl font-semibold text-gray-900 mb-6'>
            Interactive Charts with Screen Reader Support
          </h2>

          <div className='grid grid-cols-1 lg:grid-cols-2 gap-8'>
            {/* Revenue Chart */}
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h3 className='text-lg font-medium text-gray-900 mb-4'>Revenue Trends</h3>
              <RevenueChart
                data={revenueData}
                height={300}
                onDataPointClick={(data, index) => handleDataPointClick(data, index, 'Revenue')}
                className='focus-trap'
              />
              <p className='text-sm text-gray-500 mt-2'>
                Use Tab to focus on chart, Enter to interact with data points.
              </p>
            </div>

            {/* Network Usage Chart */}
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h3 className='text-lg font-medium text-gray-900 mb-4'>Network Usage Patterns</h3>
              <NetworkUsageChart
                data={networkUsageData}
                height={300}
                onDataPointClick={(data, index) =>
                  handleDataPointClick(data, index, 'Network Usage')
                }
                className='focus-trap'
              />
              <p className='text-sm text-gray-500 mt-2'>
                Keyboard accessible bar chart with data table alternative for screen readers.
              </p>
            </div>

            {/* Service Status Pie Chart */}
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h3 className='text-lg font-medium text-gray-900 mb-4'>
                Service Status Distribution
              </h3>
              <ServiceStatusChart
                data={serviceStatusData}
                height={250}
                onDataPointClick={(data, index) =>
                  handleDataPointClick(data, index, 'Service Status')
                }
                className='focus-trap'
              />
              <p className='text-sm text-gray-500 mt-2'>
                Color-blind friendly with text indicators and screen reader descriptions.
              </p>
            </div>

            {/* Bandwidth Chart */}
            <div className='bg-white rounded-lg shadow-md p-6'>
              <h3 className='text-lg font-medium text-gray-900 mb-4'>Bandwidth Utilization</h3>
              <BandwidthChart
                data={bandwidthData}
                height={250}
                onDataPointClick={(data, index) => handleDataPointClick(data, index, 'Bandwidth')}
                className='focus-trap'
              />
              <p className='text-sm text-gray-500 mt-2'>
                Line chart with capacity indicators and trend analysis.
              </p>
            </div>
          </div>
        </section>

        {/* Status Indicators Section */}
        <section aria-labelledby='status-heading' className='mb-12'>
          <h2 id='status-heading' className='text-2xl font-semibold text-gray-900 mb-6'>
            Status Indicators with Text Alternatives
          </h2>

          {/* Interactive Status Badges */}
          <div className='bg-white rounded-lg shadow-md p-6 mb-8'>
            <h3 className='text-lg font-medium text-gray-900 mb-4'>Interactive Status Badges</h3>
            <div className='flex flex-wrap gap-4 mb-4'>
              {(['online', 'offline', 'maintenance', 'degraded'] as const).map((status) => (
                <StatusBadge
                  key={status}
                  variant={status}
                  onClick={() => handleStatusClick(status)}
                  className={selectedStatus === status ? 'ring-2 ring-blue-500' : ''}
                  aria-label={`Set status to ${status}`}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                </StatusBadge>
              ))}
            </div>
            <p className='text-sm text-gray-500'>
              Selected: <strong>{selectedStatus}</strong>. Use Tab and Enter/Space to change status.
              Each badge includes text indicators for accessibility.
            </p>
          </div>

          {/* Uptime Indicator */}
          <div className='bg-white rounded-lg shadow-md p-6 mb-8'>
            <h3 className='text-lg font-medium text-gray-900 mb-4'>Service Uptime Indicator</h3>
            <UptimeIndicator
              uptime={99.87}
              className='mb-4'
              aria-label='Service uptime percentage with visual progress bar'
            />
            <p className='text-sm text-gray-500'>
              Progress bar with ARIA attributes and screen reader announcements.
            </p>
          </div>

          {/* Network Performance */}
          <div className='bg-white rounded-lg shadow-md p-6 mb-8'>
            <h3 className='text-lg font-medium text-gray-900 mb-4'>Network Performance Metrics</h3>
            <NetworkPerformanceIndicator
              latency={25}
              packetLoss={0.05}
              bandwidth={87}
              onMetricClick={(metric) => console.log(`${metric} metric clicked`)}
              className='mb-4'
            />
            <p className='text-sm text-gray-500'>
              Three-metric display with individual focus management and keyboard accessibility.
            </p>
          </div>

          {/* Service Tier */}
          <div className='bg-white rounded-lg shadow-md p-6 mb-8'>
            <h3 className='text-lg font-medium text-gray-900 mb-4'>Service Tier Indicators</h3>
            <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
              {(['basic', 'standard', 'premium', 'enterprise'] as const).map((tier) => (
                <ServiceTierIndicator
                  key={tier}
                  tier={tier}
                  onClick={() => console.log(`${tier} tier selected`)}
                  aria-label={`Select ${tier} service tier`}
                />
              ))}
            </div>
            <p className='text-sm text-gray-500 mt-4'>
              Service tiers with visual icons and descriptive ARIA labels.
            </p>
          </div>

          {/* Alert Severity */}
          <div className='bg-white rounded-lg shadow-md p-6'>
            <h3 className='text-lg font-medium text-gray-900 mb-4'>Alert Severity Indicators</h3>
            <div className='space-y-4'>
              <AlertSeverityIndicator
                severity='info'
                message='System maintenance scheduled for tonight at 2 AM EST'
                timestamp={new Date()}
                onDismiss={() => console.log('Info alert dismissed')}
              />
              <AlertSeverityIndicator
                severity='warning'
                message='High bandwidth usage detected in network segment A'
                timestamp={new Date(Date.now() - 300000)}
                onDismiss={() => console.log('Warning alert dismissed')}
              />
              <AlertSeverityIndicator
                severity='error'
                message='Service interruption affecting 12 customers'
                timestamp={new Date(Date.now() - 600000)}
                onDismiss={() => console.log('Error alert dismissed')}
              />
              <AlertSeverityIndicator
                severity='critical'
                message='Primary server down - immediate attention required'
                timestamp={new Date(Date.now() - 120000)}
                onDismiss={() => console.log('Critical alert dismissed')}
              />
            </div>
            <p className='text-sm text-gray-500 mt-4'>
              Alert system with appropriate ARIA live regions and dismissible actions.
            </p>
          </div>
        </section>

        {/* Accessibility Features Summary */}
        <section aria-labelledby='features-heading'>
          <h2 id='features-heading' className='text-2xl font-semibold text-gray-900 mb-6'>
            Accessibility Features Implemented
          </h2>

          <div className='bg-green-50 border border-green-200 rounded-lg p-6'>
            <h3 className='text-lg font-semibold text-green-800 mb-4'>
              WCAG 2.1 AA Compliance Features
            </h3>
            <div className='grid md:grid-cols-2 gap-6'>
              <div>
                <h4 className='font-medium text-green-800 mb-2'>🎯 Screen Reader Support</h4>
                <ul className='text-sm text-green-700 space-y-1'>
                  <li>• Comprehensive ARIA labels and descriptions</li>
                  <li>• Alternative text for all visual content</li>
                  <li>• Data table alternatives for charts</li>
                  <li>• Live region announcements</li>
                </ul>
              </div>

              <div>
                <h4 className='font-medium text-green-800 mb-2'>⌨️ Keyboard Navigation</h4>
                <ul className='text-sm text-green-700 space-y-1'>
                  <li>• Tab order management</li>
                  <li>• Enter/Space activation</li>
                  <li>• Arrow key navigation</li>
                  <li>• Focus trapping and restoration</li>
                </ul>
              </div>

              <div>
                <h4 className='font-medium text-green-800 mb-2'>🎨 Color Independence</h4>
                <ul className='text-sm text-green-700 space-y-1'>
                  <li>• Text indicators for all status colors</li>
                  <li>• High contrast mode support</li>
                  <li>• Pattern-based alternatives</li>
                  <li>• 4.5:1 contrast ratio compliance</li>
                </ul>
              </div>

              <div>
                <h4 className='font-medium text-green-800 mb-2'>🏗️ Semantic Structure</h4>
                <ul className='text-sm text-green-700 space-y-1'>
                  <li>• Proper heading hierarchy</li>
                  <li>• Landmark roles and regions</li>
                  <li>• Meaningful element relationships</li>
                  <li>• Progressive enhancement</li>
                </ul>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer role='contentinfo' className='border-t pt-8 mt-12'>
        <p className='text-center text-gray-500 text-sm'>
          Accessibility Demo - WCAG 2.1 AA Compliant Components | Press F12 to open DevTools and
          check console for accessibility test results
        </p>
      </footer>
    </div>
  );
};

'use client';

import React, { Component, ReactNode } from 'react';
import { logger } from '@/lib/utils/logger';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log error to error reporting service
    logger.error('ErrorBoundary caught error', error, {
      componentStack: errorInfo.componentStack,
      errorBoundary: true
    });

    // Update state with error details
    this.setState({
      error,
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Send to monitoring service (e.g., Sentry)
    if (typeof window !== 'undefined' && process.env.NODE_ENV === 'production') {
      // Example: Sentry integration
      // Sentry.captureException(error, {
      //   contexts: {
      //     react: {
      //       componentStack: errorInfo.componentStack,
      //     },
      //   },
      // });
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="error-boundary-container">
          <div className="error-content">
            <h1 className="error-title">Oops! Something went wrong</h1>
            <p className="error-message">
              We&apos;re sorry for the inconvenience. The error has been logged and we&apos;ll look into it.
            </p>

            {/* Show error details in development */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="error-details">
                <summary>Error Details (Development Only)</summary>
                <pre className="error-stack">
                  <strong>{this.state.error.toString()}</strong>
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}

            <div className="error-actions">
              <button
                onClick={this.handleReset}
                className="error-reset-button"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/'}
                className="error-home-button"
              >
                Go to Home
              </button>
            </div>
          </div>

          <style jsx>{`
            .error-boundary-container {
              min-height: 100vh;
              display: flex;
              align-items: center;
              justify-content: center;
              padding: 2rem;
              background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }

            .error-content {
              max-width: 600px;
              background: white;
              border-radius: 12px;
              padding: 3rem;
              box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            }

            .error-title {
              font-size: 2rem;
              font-weight: bold;
              color: #1a202c;
              margin-bottom: 1rem;
            }

            .error-message {
              color: #4a5568;
              margin-bottom: 2rem;
              line-height: 1.6;
            }

            .error-details {
              margin: 2rem 0;
              padding: 1rem;
              background: #f7fafc;
              border-radius: 8px;
              border: 1px solid #e2e8f0;
            }

            .error-details summary {
              cursor: pointer;
              font-weight: 600;
              color: #2d3748;
              margin-bottom: 0.5rem;
            }

            .error-stack {
              margin-top: 1rem;
              padding: 1rem;
              background: #1a202c;
              color: #f7fafc;
              border-radius: 4px;
              overflow-x: auto;
              font-family: 'Monaco', 'Courier New', monospace;
              font-size: 0.875rem;
              line-height: 1.5;
            }

            .error-actions {
              display: flex;
              gap: 1rem;
              margin-top: 2rem;
            }

            .error-reset-button,
            .error-home-button {
              flex: 1;
              padding: 0.75rem 1.5rem;
              border-radius: 8px;
              font-weight: 600;
              transition: all 0.2s;
              cursor: pointer;
              border: none;
              font-size: 1rem;
            }

            .error-reset-button {
              background: #667eea;
              color: white;
            }

            .error-reset-button:hover {
              background: #5a67d8;
              transform: translateY(-1px);
            }

            .error-home-button {
              background: #edf2f7;
              color: #2d3748;
            }

            .error-home-button:hover {
              background: #e2e8f0;
              transform: translateY(-1px);
            }
          `}</style>
        </div>
      );
    }

    return this.props.children;
  }
}

// Async Error Boundary Hook
export function useAsyncError() {
  const [, setError] = React.useState();
  return React.useCallback(
    (e: Error) => {
      setError(() => {
        throw e;
      });
    },
    [setError]
  );
}

// HOC for wrapping components with error boundary
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  fallback?: ReactNode,
  onError?: (error: Error, errorInfo: React.ErrorInfo) => void
) {
  const WrappedComponent = (props: P) => (
    <ErrorBoundary fallback={fallback} onError={onError}>
      <Component {...props} />
    </ErrorBoundary>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name || 'Component'})`;

  return WrappedComponent;
}
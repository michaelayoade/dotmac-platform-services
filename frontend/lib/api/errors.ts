// Backend error response format
export interface BackendError {
  error_code: string;
  message: string;
  user_message?: string;
  correlation_id?: string;
  timestamp?: string;
  status: number;
  severity?: "low" | "medium" | "high" | "critical";
  category?:
    | "validation"
    | "authentication"
    | "authorization"
    | "business"
    | "system"
    | "network"
    | "database"
    | "external_service"
    | "unknown";
  retryable?: boolean;
  details?: Record<string, unknown>;
  recovery_hint?: string;
  field_errors?: Record<string, string[]>;
}

export class ApiClientError extends Error {
  status: number;
  code: string;
  userMessage?: string;
  details?: Record<string, unknown>;
  fieldErrors?: Record<string, string[]>;
  correlationId?: string;
  retryable: boolean;
  recoveryHint?: string;

  constructor(
    message: string,
    status: number,
    code: string,
    userMessage?: string,
    details?: Record<string, unknown>,
    fieldErrors?: Record<string, string[]>,
    correlationId?: string,
    retryable: boolean = false,
    recoveryHint?: string
  ) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.userMessage = userMessage;
    this.details = details;
    this.fieldErrors = fieldErrors;
    this.correlationId = correlationId;
    this.retryable = retryable;
    this.recoveryHint = recoveryHint;
  }

  static fromBackendError(error: BackendError): ApiClientError {
    return new ApiClientError(
      error.message,
      error.status,
      error.error_code,
      error.user_message,
      error.details,
      error.field_errors,
      error.correlation_id,
      error.retryable ?? false,
      error.recovery_hint
    );
  }

  // Check if error is an auth error
  isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }

  // Check if error is a validation error
  isValidationError(): boolean {
    return this.status === 400 || this.status === 422;
  }

  // Check if error is a rate limit error
  isRateLimitError(): boolean {
    return this.status === 429;
  }

  // Check if error is a server error
  isServerError(): boolean {
    return this.status >= 500;
  }

  // Get user-friendly message
  getUserMessage(): string {
    return this.userMessage || this.message || "An unexpected error occurred";
  }
}

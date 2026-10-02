/**
 * Error handling for the GRC Marketing TypeScript SDK.
 */

export class GRCMarketingError extends Error {
  public readonly statusCode?: number;
  public readonly responseBody?: Record<string, unknown>;

  constructor(
    message: string,
    statusCode?: number,
    responseBody?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "GRCMarketingError";
    this.statusCode = statusCode;
    this.responseBody = responseBody;
    Object.setPrototypeOf(this, GRCMarketingError.prototype);
  }

  toString(): string {
    if (this.statusCode) {
      return `[${this.statusCode}] ${this.message}`;
    }
    return this.message;
  }
}

export class AuthenticationError extends GRCMarketingError {
  constructor(message = "Authentication failed", responseBody?: Record<string, unknown>) {
    super(message, 401, responseBody);
    this.name = "AuthenticationError";
  }
}

export class AuthorizationError extends GRCMarketingError {
  constructor(message = "Access denied", responseBody?: Record<string, unknown>) {
    super(message, 403, responseBody);
    this.name = "AuthorizationError";
  }
}

export class NotFoundError extends GRCMarketingError {
  constructor(message = "Resource not found", responseBody?: Record<string, unknown>) {
    super(message, 404, responseBody);
    this.name = "NotFoundError";
  }
}

export class ValidationError extends GRCMarketingError {
  constructor(message = "Validation failed", responseBody?: Record<string, unknown>) {
    super(message, 422, responseBody);
    this.name = "ValidationError";
  }
}

export class RateLimitError extends GRCMarketingError {
  public readonly retryAfter?: number;

  constructor(
    message = "Rate limit exceeded",
    responseBody?: Record<string, unknown>,
    retryAfter?: number,
  ) {
    super(message, 429, responseBody);
    this.name = "RateLimitError";
    this.retryAfter = retryAfter;
  }
}

export class ServerError extends GRCMarketingError {
  constructor(
    message = "Internal server error",
    statusCode = 500,
    responseBody?: Record<string, unknown>,
  ) {
    super(message, statusCode, responseBody);
    this.name = "ServerError";
  }
}

export class NetworkError extends GRCMarketingError {
  public readonly originalError?: Error;

  constructor(message = "Network error", originalError?: Error) {
    super(message);
    this.name = "NetworkError";
    this.originalError = originalError;
  }
}

export class TimeoutError extends GRCMarketingError {
  public readonly timeoutSeconds?: number;

  constructor(message = "Request timed out", timeoutSeconds?: number) {
    super(message);
    this.name = "TimeoutError";
    this.timeoutSeconds = timeoutSeconds;
  }
}

export class ConfigurationError extends GRCMarketingError {
  constructor(message = "SDK configuration error") {
    super(message);
    this.name = "ConfigurationError";
  }
}

/**
 * Raise the appropriate error for an HTTP status code.
 */
export function raiseForStatus(
  statusCode: number,
  responseBody?: Record<string, unknown>,
): never {
  let message = "Unknown error";
  if (responseBody && typeof responseBody === "object") {
    message =
      (responseBody.message as string) ||
      (responseBody.error as string) ||
      message;
  }

  const errorMap: Record<number, new (msg: string, body?: Record<string, unknown>) => GRCMarketingError> = {
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    422: ValidationError,
    429: RateLimitError,
  };

  const errorCls = errorMap[statusCode];
  if (errorCls) {
    throw new errorCls(message, responseBody);
  }

  if (statusCode >= 500) {
    throw new ServerError(message, statusCode, responseBody);
  }

  if (statusCode >= 400) {
    throw new GRCMarketingError(message, statusCode, responseBody);
  }

  throw new GRCMarketingError(message, statusCode, responseBody);
}

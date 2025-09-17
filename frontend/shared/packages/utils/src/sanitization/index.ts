/**
 * Consolidated Input Sanitization for DotMac Framework
 *
 * Combines the best features from security and headless packages
 * to provide comprehensive XSS protection and input sanitization.
 */

import DOMPurify from 'dompurify';

export interface SanitizationConfig {
  allowedTags?: string[];
  allowedAttributes?: Record<string, string[]>;
  maxLength?: number;
  stripWhitespace?: boolean;
  preserveNewlines?: boolean;
  allowEmptyValues?: boolean;
  customValidators?: Array<(input: string) => string>;
  stripAll?: boolean;
}

export interface SanitizationResult {
  sanitized: string;
  wasModified: boolean;
  violations: string[];
  isValid: boolean;
}

export class InputSanitizer {
  private static instance: InputSanitizer;

  // Default safe HTML tags for rich text content
  private readonly DEFAULT_ALLOWED_TAGS = [
    'p',
    'br',
    'strong',
    'b',
    'em',
    'i',
    'u',
    'ul',
    'ol',
    'li',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'blockquote',
    'pre',
    'code',
  ];

  // Default allowed attributes
  private readonly DEFAULT_ALLOWED_ATTRIBUTES: Record<string, string[]> = {
    a: ['href', 'title'],
    img: ['src', 'alt', 'title', 'width', 'height'],
    '*': ['class'],
  };

  // Dangerous patterns that should always be removed
  private readonly DANGEROUS_PATTERNS = [
    /<script\b[^<]*(?:(?!<\/script>)[^<]*)*<\/script>/gi,
    /<iframe\b[^<]*(?:(?!<\/iframe>)[^<]*)*<\/iframe>/gi,
    /<object\b[^<]*(?:(?!<\/object>)[^<]*)*<\/object>/gi,
    /<embed\b[^<]*(?:(?!<\/embed>)[^<]*)*<\/embed>/gi,
    /<form\b[^<]*(?:(?!<\/form>)[^<]*)*<\/form>/gi,
    /javascript:/gi,
    /data:text\/html/gi,
    /vbscript:/gi,
  ];

  private config: Required<SanitizationConfig>;

  constructor(config?: SanitizationConfig) {
    this.config = {
      allowedTags: this.DEFAULT_ALLOWED_TAGS,
      allowedAttributes: this.DEFAULT_ALLOWED_ATTRIBUTES,
      maxLength: 1000,
      stripWhitespace: true,
      preserveNewlines: false,
      allowEmptyValues: false,
      customValidators: [],
      stripAll: false,
      ...config,
    };
  }

  public static getInstance(config?: SanitizationConfig): InputSanitizer {
    if (!InputSanitizer.instance) {
      InputSanitizer.instance = new InputSanitizer(config);
    }
    return InputSanitizer.instance;
  }

  /**
   * Comprehensive input sanitization
   */
  public sanitize(input: string, customConfig?: Partial<SanitizationConfig>): SanitizationResult {
    if (typeof input !== 'string') {
      return {
        sanitized: '',
        wasModified: true,
        violations: ['Invalid input type'],
        isValid: false,
      };
    }

    const config = { ...this.config, ...customConfig };
    const original = input;
    let result = input;
    const violations: string[] = [];

    // Handle empty values
    if (!result && !config.allowEmptyValues) {
      return {
        sanitized: '',
        wasModified: original !== '',
        violations: ['Empty value not allowed'],
        isValid: false,
      };
    }

    // Length validation
    if (config.maxLength && result.length > config.maxLength) {
      result = result.substring(0, config.maxLength);
      violations.push(`Input truncated to ${config.maxLength} characters`);
    }

    // Remove dangerous patterns first
    for (const pattern of this.DANGEROUS_PATTERNS) {
      const beforeClean = result;
      result = result.replace(pattern, '');
      if (beforeClean !== result) {
        violations.push('Dangerous script patterns removed');
      }
    }

    // Use DOMPurify for HTML sanitization
    if (config.stripAll) {
      // Strip all HTML tags
      result = DOMPurify.sanitize(result, {
        ALLOWED_TAGS: [],
        ALLOWED_ATTR: [],
      });
    } else {
      // Sanitize with allowed tags and attributes
      result = DOMPurify.sanitize(result, {
        ALLOWED_TAGS: config.allowedTags,
        ALLOWED_ATTR: Object.values(config.allowedAttributes).flat(),
        KEEP_CONTENT: true,
        RETURN_DOM_FRAGMENT: false,
      });
    }

    // Apply custom validators
    for (const validator of config.customValidators) {
      result = validator(result);
    }

    // Whitespace handling
    if (config.stripWhitespace) {
      result = result.trim();
      if (!config.preserveNewlines) {
        result = result.replace(/\s+/g, ' ');
      }
    }

    const wasModified = original !== result;
    const isValid = violations.length === 0;

    return {
      sanitized: result,
      wasModified,
      violations,
      isValid,
    };
  }

  /**
   * Sanitize email addresses
   */
  public sanitizeEmail(email: string): SanitizationResult {
    return this.sanitize(email, {
      stripAll: true,
      maxLength: 254,
      customValidators: [
        (input) => {
          // Basic email format validation
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          return emailRegex.test(input) ? input : '';
        },
      ],
    });
  }

  /**
   * Sanitize phone numbers
   */
  public sanitizePhone(phone: string): SanitizationResult {
    return this.sanitize(phone, {
      stripAll: true,
      maxLength: 20,
      customValidators: [
        (input) => {
          // Remove all non-numeric characters except +, -, (, ), and spaces
          return input.replace(/[^\d+\-() ]/g, '');
        },
      ],
    });
  }

  /**
   * Sanitize URLs
   */
  public sanitizeURL(url: string): SanitizationResult {
    return this.sanitize(url, {
      stripAll: true,
      maxLength: 2048,
      customValidators: [
        (input) => {
          try {
            const urlObj = new URL(input);
            // Only allow http and https protocols
            if (!['http:', 'https:'].includes(urlObj.protocol)) {
              return '';
            }
            return urlObj.toString();
          } catch {
            return '';
          }
        },
      ],
    });
  }

  /**
   * Sanitize file paths to prevent path traversal
   */
  public sanitizeFilePath(path: string): SanitizationResult {
    return this.sanitize(path, {
      stripAll: true,
      customValidators: [
        (input) => {
          // Remove path traversal attempts
          return input
            .replace(/\.\./g, '')
            .replace(/[<>:"|?*]/g, '')
            .replace(/^\/+/, '')
            .replace(/\/+/g, '/');
        },
      ],
    });
  }
}

// Convenience functions for common use cases
export const sanitizer = InputSanitizer.getInstance();

export const sanitizeInput = (input: string, config?: Partial<SanitizationConfig>) =>
  sanitizer.sanitize(input, config);

export const sanitizeEmail = (email: string) => sanitizer.sanitizeEmail(email);
export const sanitizePhone = (phone: string) => sanitizer.sanitizePhone(phone);
export const sanitizeURL = (url: string) => sanitizer.sanitizeURL(url);
export const sanitizeFilePath = (path: string) => sanitizer.sanitizeFilePath(path);

// Legacy API compatibility
export const cleanInput = sanitizeInput;
export const sanitizeHtml = (html: string) =>
  sanitizeInput(html, { allowedTags: sanitizer['DEFAULT_ALLOWED_TAGS'] });

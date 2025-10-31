/**
 * Error Handling & Loading States
 * Phase 10: Accessibility & Polish
 *
 * Provides:
 * - Global error boundary
 * - Loading state management
 * - Retry mechanisms
 * - Error logging
 */

// ==============================================
// ERROR BOUNDARY
// ==============================================

class ErrorBoundary {
  constructor() {
    this.errors = [];
    this.maxErrors = 10;
    this.init();
  }

  init() {
    // Catch unhandled errors
    window.addEventListener('error', (event) => {
      this.handleError(event.error || event.message, {
        type: 'unhandled',
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      });
      event.preventDefault();
    });

    // Catch unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.handleError(event.reason, {
        type: 'unhandled_promise',
        promise: event.promise
      });
      event.preventDefault();
    });

    // Catch HTMX errors
    document.addEventListener('htmx:responseError', (event) => {
      this.handleHTMXError(event);
    });

    document.addEventListener('htmx:sendError', (event) => {
      this.handleHTMXError(event);
    });

    document.addEventListener('htmx:timeout', (event) => {
      this.handleHTMXError(event, 'Request timeout');
    });
  }

  handleError(error, context = {}) {
    const errorInfo = {
      message: error?.message || error,
      stack: error?.stack,
      context,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href
    };

    // Store error
    this.errors.push(errorInfo);
    if (this.errors.length > this.maxErrors) {
      this.errors.shift();
    }

    // Log to console in development
    if (this.isDevelopment()) {
      console.error('ErrorBoundary caught:', errorInfo);
    }

    // Show user-friendly error message
    this.showErrorToUser(errorInfo);

    // Optionally send to error tracking service
    this.logToService(errorInfo);
  }

  handleHTMXError(event, customMessage = null) {
    const detail = event.detail;
    const errorInfo = {
      message: customMessage || detail.error || 'Network request failed',
      xhr: detail.xhr,
      target: detail.target?.id || detail.target?.tagName,
      timestamp: new Date().toISOString()
    };

    // Show error toast
    if (window.Toast) {
      Toast.error(
        errorInfo.message,
        'Request Failed'
      );
    }

    // Log error
    this.errors.push(errorInfo);
    if (this.errors.length > this.maxErrors) {
      this.errors.shift();
    }

    // Log to console in development
    if (this.isDevelopment()) {
      console.error('HTMX Error:', errorInfo);
    }
  }

  showErrorToUser(errorInfo) {
    if (!window.Toast) return;

    const userMessage = this.getUserFriendlyMessage(errorInfo);

    Toast.error(
      userMessage,
      'Something went wrong',
      {
        duration: 8000,
        actions: [
          {
            text: 'Retry',
            onClick: () => window.location.reload()
          },
          {
            text: 'Report',
            onClick: () => this.showErrorReport(errorInfo)
          }
        ]
      }
    );
  }

  getUserFriendlyMessage(errorInfo) {
    const message = errorInfo.message?.toLowerCase() || '';

    if (message.includes('network') || message.includes('fetch')) {
      return 'Unable to connect. Please check your internet connection.';
    }

    if (message.includes('timeout')) {
      return 'Request took too long. Please try again.';
    }

    if (message.includes('permission') || message.includes('denied')) {
      return 'Permission denied. Please check your permissions.';
    }

    if (message.includes('not found') || message.includes('404')) {
      return 'The requested resource was not found.';
    }

    if (message.includes('unauthorized') || message.includes('401')) {
      return 'Please log in to continue.';
    }

    if (message.includes('forbidden') || message.includes('403')) {
      return 'You don\'t have permission to access this resource.';
    }

    if (message.includes('server') || message.includes('500')) {
      return 'Server error. Please try again later.';
    }

    return 'An unexpected error occurred. Please try again.';
  }

  showErrorReport(errorInfo) {
    const report = `
Error Report
============
Time: ${errorInfo.timestamp}
URL: ${errorInfo.url}
Message: ${errorInfo.message}

Stack Trace:
${errorInfo.stack || 'Not available'}

Context:
${JSON.stringify(errorInfo.context, null, 2)}

User Agent:
${errorInfo.userAgent}
    `.trim();

    // Copy to clipboard
    navigator.clipboard.writeText(report).then(() => {
      if (window.Toast) {
        Toast.success('Error report copied to clipboard', 'Copied');
      }
    });
  }

  logToService(errorInfo) {
    // In production, send to error tracking service
    // Example: Sentry, LogRocket, etc.
    if (!this.isDevelopment()) {
      // fetch('/api/errors/log', {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(errorInfo)
      // }).catch(() => {
      //   // Silent fail - don't create error loop
      // });
    }
  }

  isDevelopment() {
    return window.location.hostname === 'localhost' ||
           window.location.hostname === '127.0.0.1';
  }

  getErrors() {
    return this.errors;
  }

  clearErrors() {
    this.errors = [];
  }
}

// Initialize global error boundary
window.errorBoundary = new ErrorBoundary();

// ==============================================
// LOADING STATE MANAGER
// ==============================================

class LoadingManager {
  constructor() {
    this.loadingStates = new Map();
    this.init();
  }

  init() {
    // Track HTMX requests
    document.addEventListener('htmx:beforeRequest', (event) => {
      this.startLoading(event.detail.target);
    });

    document.addEventListener('htmx:afterRequest', (event) => {
      this.stopLoading(event.detail.target);
    });
  }

  /**
   * Start loading state for an element
   * @param {HTMLElement|string} target - Element or selector
   * @param {Object} options - Loading options
   */
  startLoading(target, options = {}) {
    const element = this.getElement(target);
    if (!element) return;

    const id = this.getElementId(element);
    const config = {
      showSpinner: true,
      disableElement: true,
      overlayText: 'Loading...',
      ...options
    };

    this.loadingStates.set(id, {
      element,
      config,
      startTime: Date.now()
    });

    // Add loading class
    element.classList.add('loading');

    // Disable if it's a button or form
    if (config.disableElement) {
      if (element.tagName === 'BUTTON' || element.tagName === 'INPUT') {
        element.disabled = true;
        element.setAttribute('aria-busy', 'true');
      } else if (element.tagName === 'FORM') {
        const inputs = element.querySelectorAll('input, button, select, textarea');
        inputs.forEach(input => {
          input.disabled = true;
          input.setAttribute('data-was-disabled', 'true');
        });
        element.setAttribute('aria-busy', 'true');
      }
    }

    // Add spinner if requested
    if (config.showSpinner) {
      this.addSpinner(element, config.overlayText);
    }

    // Announce to screen readers
    this.announceLoading(element, config.overlayText);
  }

  /**
   * Stop loading state for an element
   * @param {HTMLElement|string} target - Element or selector
   */
  stopLoading(target) {
    const element = this.getElement(target);
    if (!element) return;

    const id = this.getElementId(element);
    const state = this.loadingStates.get(id);

    if (!state) return;

    // Calculate loading duration
    const duration = Date.now() - state.startTime;

    // Remove loading class
    element.classList.remove('loading');

    // Re-enable element
    if (state.config.disableElement) {
      if (element.tagName === 'BUTTON' || element.tagName === 'INPUT') {
        element.disabled = false;
        element.removeAttribute('aria-busy');
      } else if (element.tagName === 'FORM') {
        const inputs = element.querySelectorAll('[data-was-disabled]');
        inputs.forEach(input => {
          input.disabled = false;
          input.removeAttribute('data-was-disabled');
        });
        element.removeAttribute('aria-busy');
      }
    }

    // Remove spinner
    if (state.config.showSpinner) {
      this.removeSpinner(element);
    }

    // Clear state
    this.loadingStates.delete(id);

    // Log slow requests in development
    if (duration > 3000 && window.errorBoundary?.isDevelopment()) {
      console.warn(`Slow request: ${id} took ${duration}ms`);
    }
  }

  addSpinner(element, text) {
    // Check if spinner already exists
    if (element.querySelector('.loading-overlay')) return;

    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.setAttribute('role', 'status');
    overlay.setAttribute('aria-live', 'polite');

    overlay.innerHTML = `
      <div class="loading-content">
        <div class="loading-spinner"></div>
        ${text ? `<div class="loading-text">${text}</div>` : ''}
        <span class="sr-only">${text || 'Loading'}</span>
      </div>
    `;

    // Position relative if needed
    const position = window.getComputedStyle(element).position;
    if (position === 'static') {
      element.style.position = 'relative';
    }

    element.appendChild(overlay);
  }

  removeSpinner(element) {
    const overlay = element.querySelector('.loading-overlay');
    if (overlay) {
      overlay.remove();
    }
  }

  announceLoading(element, text) {
    // Create or update live region for screen readers
    let liveRegion = document.getElementById('loading-announcer');
    if (!liveRegion) {
      liveRegion = document.createElement('div');
      liveRegion.id = 'loading-announcer';
      liveRegion.className = 'sr-only';
      liveRegion.setAttribute('role', 'status');
      liveRegion.setAttribute('aria-live', 'polite');
      document.body.appendChild(liveRegion);
    }

    liveRegion.textContent = text || 'Loading content';
  }

  getElement(target) {
    if (typeof target === 'string') {
      return document.querySelector(target);
    }
    return target;
  }

  getElementId(element) {
    if (element.id) return element.id;
    // Generate a unique ID if none exists
    const id = `loading-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    element.setAttribute('data-loading-id', id);
    return id;
  }

  isLoading(target) {
    const element = this.getElement(target);
    if (!element) return false;
    const id = this.getElementId(element);
    return this.loadingStates.has(id);
  }
}

// Initialize global loading manager
window.loadingManager = new LoadingManager();

// ==============================================
// RETRY MECHANISM
// ==============================================

class RetryManager {
  /**
   * Retry a function with exponential backoff
   * @param {Function} fn - Function to retry
   * @param {Object} options - Retry options
   */
  static async retry(fn, options = {}) {
    const {
      maxRetries = 3,
      initialDelay = 1000,
      maxDelay = 10000,
      backoffFactor = 2,
      onRetry = null
    } = options;

    let lastError;
    let delay = initialDelay;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;

        if (attempt === maxRetries) {
          throw error;
        }

        // Call retry callback if provided
        if (onRetry) {
          onRetry(attempt, delay, error);
        }

        // Wait before retrying
        await this.sleep(delay);

        // Increase delay for next attempt (exponential backoff)
        delay = Math.min(delay * backoffFactor, maxDelay);
      }
    }

    throw lastError;
  }

  static sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Retry a fetch request
   * @param {string} url - URL to fetch
   * @param {Object} options - Fetch options
   * @param {Object} retryOptions - Retry options
   */
  static async retryFetch(url, options = {}, retryOptions = {}) {
    return this.retry(
      () => fetch(url, options).then(response => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response;
      }),
      {
        ...retryOptions,
        onRetry: (attempt, delay, error) => {
          console.warn(`Retry attempt ${attempt} for ${url} in ${delay}ms`, error);

          if (window.Toast && attempt === 1) {
            Toast.warning(
              `Retrying request (attempt ${attempt})...`,
              'Network Issue'
            );
          }

          if (retryOptions.onRetry) {
            retryOptions.onRetry(attempt, delay, error);
          }
        }
      }
    );
  }
}

window.RetryManager = RetryManager;

// ==============================================
// NETWORK STATUS MONITOR
// ==============================================

class NetworkMonitor {
  constructor() {
    this.isOnline = navigator.onLine;
    this.init();
  }

  init() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.handleOnline();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.handleOffline();
    });
  }

  handleOnline() {
    if (window.Toast) {
      Toast.success(
        'Connection restored',
        'Back Online'
      );
    }

    // Retry any pending requests
    this.retryPendingRequests();
  }

  handleOffline() {
    if (window.Toast) {
      Toast.error(
        'No internet connection. Please check your network.',
        'Offline',
        { duration: 0 } // Don't auto-dismiss
      );
    }
  }

  retryPendingRequests() {
    // Trigger HTMX to retry failed requests
    document.querySelectorAll('[hx-get], [hx-post]').forEach(element => {
      if (element.classList.contains('htmx-request-error')) {
        htmx.trigger(element, 'retry');
      }
    });
  }

  getStatus() {
    return this.isOnline ? 'online' : 'offline';
  }
}

// Initialize network monitor
window.networkMonitor = new NetworkMonitor();

// ==============================================
// UTILITY FUNCTIONS
// ==============================================

/**
 * Wrap an async function with error handling
 * @param {Function} fn - Async function to wrap
 * @param {Object} options - Error handling options
 */
function withErrorHandling(fn, options = {}) {
  return async function(...args) {
    try {
      return await fn.apply(this, args);
    } catch (error) {
      if (window.errorBoundary) {
        window.errorBoundary.handleError(error, {
          function: fn.name,
          args: args,
          ...options
        });
      } else {
        console.error('Error:', error);
      }

      if (options.rethrow) {
        throw error;
      }

      return options.fallback;
    }
  };
}

/**
 * Safe JSON parse with fallback
 * @param {string} json - JSON string to parse
 * @param {*} fallback - Fallback value if parse fails
 */
function safeJSONParse(json, fallback = null) {
  try {
    return JSON.parse(json);
  } catch (error) {
    console.warn('JSON parse error:', error);
    return fallback;
  }
}

// Export utilities
window.withErrorHandling = withErrorHandling;
window.safeJSONParse = safeJSONParse;

// ==============================================
// CONSOLE MESSAGES
// ==============================================

if (window.errorBoundary?.isDevelopment()) {
  console.log(
    '%cError Handling Active',
    'color: #28c081; font-weight: bold; font-size: 14px;'
  );
  console.log('Available utilities:', {
    errorBoundary: window.errorBoundary,
    loadingManager: window.loadingManager,
    networkMonitor: window.networkMonitor,
    RetryManager: window.RetryManager,
    withErrorHandling: window.withErrorHandling
  });
}

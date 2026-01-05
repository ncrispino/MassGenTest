/**
 * Fetch Utilities with AbortController Support
 *
 * Provides utilities for making cancellable fetch requests, particularly
 * useful for workspace browser where rapid switching between workspaces
 * requires cancelling in-flight requests.
 *
 * @see specs/001-fix-workspace-browser/spec.md FR-008
 */

/**
 * Options for fetch with abort support.
 */
export interface FetchWithAbortOptions extends Omit<RequestInit, 'signal'> {
  /** Timeout in milliseconds (default: 30000) */
  timeout?: number;
}

/**
 * Result from createAbortableFetch.
 */
export interface AbortableFetchResult<T> {
  /** Promise that resolves with the parsed response */
  promise: Promise<T>;
  /** Function to abort the request */
  abort: () => void;
  /** The AbortController instance */
  controller: AbortController;
}

/**
 * Error thrown when a fetch request is aborted.
 */
export class FetchAbortError extends Error {
  constructor(message = 'Request was aborted') {
    super(message);
    this.name = 'FetchAbortError';
  }
}

/**
 * Error thrown when a fetch request times out.
 */
export class FetchTimeoutError extends Error {
  constructor(timeout: number) {
    super(`Request timed out after ${timeout}ms`);
    this.name = 'FetchTimeoutError';
  }
}

/**
 * Creates an abortable fetch request that returns JSON.
 *
 * @param url - The URL to fetch
 * @param options - Fetch options including timeout
 * @returns Object containing the promise, abort function, and controller
 *
 * @example
 * ```typescript
 * // Create the request
 * const { promise, abort, controller } = createAbortableFetch<BrowseResponse>(
 *   `/api/workspace/browse?path=${encodeURIComponent(workspacePath)}`
 * );
 *
 * // Use the promise
 * try {
 *   const data = await promise;
 *   console.log('Files:', data.files);
 * } catch (err) {
 *   if (err instanceof FetchAbortError) {
 *     console.log('Request was cancelled');
 *   } else {
 *     console.error('Fetch failed:', err);
 *   }
 * }
 *
 * // Cancel if needed (e.g., when workspace changes)
 * abort();
 * ```
 */
export function createAbortableFetch<T>(
  url: string,
  options: FetchWithAbortOptions = {}
): AbortableFetchResult<T> {
  const controller = new AbortController();
  const { timeout = 30000, ...fetchOptions } = options;

  // Set up timeout
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  const promise = new Promise<T>((resolve, reject) => {
    // Set timeout
    if (timeout > 0) {
      timeoutId = setTimeout(() => {
        controller.abort();
        reject(new FetchTimeoutError(timeout));
      }, timeout);
    }

    fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    })
      .then(async (response) => {
        // Clear timeout on response
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }

        if (!response.ok) {
          const errorText = await response.text().catch(() => 'Unknown error');
          throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        return response.json();
      })
      .then(resolve)
      .catch((err) => {
        // Clear timeout on error
        if (timeoutId) {
          clearTimeout(timeoutId);
          timeoutId = null;
        }

        // Convert abort error to our custom error
        if (err.name === 'AbortError') {
          reject(new FetchAbortError());
        } else {
          reject(err);
        }
      });
  });

  const abort = () => {
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
    controller.abort();
  };

  return { promise, abort, controller };
}

/**
 * Simplified fetch with abort support - returns promise only.
 * Use createAbortableFetch if you need the abort function.
 *
 * @param url - The URL to fetch
 * @param signal - Optional AbortSignal for cancellation
 * @param options - Fetch options
 * @returns Promise that resolves with the parsed response
 *
 * @example
 * ```typescript
 * const controller = new AbortController();
 *
 * try {
 *   const data = await fetchWithAbort<BrowseResponse>(
 *     `/api/workspace/browse?path=${path}`,
 *     controller.signal
 *   );
 * } catch (err) {
 *   if (err instanceof FetchAbortError) {
 *     // Cancelled - ignore
 *   }
 * }
 *
 * // To cancel:
 * controller.abort();
 * ```
 */
export async function fetchWithAbort<T>(
  url: string,
  signal?: AbortSignal,
  options: Omit<RequestInit, 'signal'> = {}
): Promise<T> {
  try {
    const response = await fetch(url, {
      ...options,
      signal,
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error');
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return response.json();
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') {
      throw new FetchAbortError();
    }
    throw err;
  }
}

/**
 * Type guard for FetchAbortError.
 */
export function isAbortError(err: unknown): err is FetchAbortError {
  return err instanceof FetchAbortError;
}

/**
 * Type guard for FetchTimeoutError.
 */
export function isTimeoutError(err: unknown): err is FetchTimeoutError {
  return err instanceof FetchTimeoutError;
}

/**
 * Helper to check if error is either abort or timeout.
 */
export function isCancellationError(err: unknown): boolean {
  return isAbortError(err) || isTimeoutError(err);
}

/**
 * useFileContent Hook
 *
 * Fetches and caches file content from workspace for viewing.
 */

import { useState, useCallback } from 'react';
import type { FileContentResponse } from '../types';

interface UseFileContentReturn {
  content: FileContentResponse | null;
  isLoading: boolean;
  error: string | null;
  fetchFile: (filePath: string, workspacePath: string, skipCache?: boolean) => Promise<void>;
  clearContent: () => void;
}

// Simple in-memory cache for file contents
const fileCache = new Map<string, FileContentResponse>();
// Track files that returned 404 to avoid repeated fetches
const notFoundCache = new Set<string>();

export function useFileContent(): UseFileContentReturn {
  const [content, setContent] = useState<FileContentResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFile = useCallback(async (filePath: string, workspacePath: string, skipCache = false) => {
    const cacheKey = `${workspacePath}:${filePath}`;

    // Check cache first (unless skipping)
    if (!skipCache) {
      const cached = fileCache.get(cacheKey);
      if (cached) {
        setContent(cached);
        setError(null);
        return;
      }
      // Check if file was not found recently (avoid repeated 404s)
      if (notFoundCache.has(cacheKey)) {
        setError('File not found');
        setContent(null);
        return;
      }
    } else {
      fileCache.delete(cacheKey);
      notFoundCache.delete(cacheKey);
    }

    setIsLoading(true);
    setError(null);

    // Add timeout to prevent infinite loading
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10s timeout

    try {
      const params = new URLSearchParams({
        path: filePath,
        workspace: workspacePath,
      });

      const response = await fetch(`/api/workspace/file?${params}`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      const data: FileContentResponse = await response.json();

      if (!response.ok) {
        // Cache 404s to avoid repeated fetches
        if (response.status === 404) {
          notFoundCache.add(cacheKey);
        }
        throw new Error(data.error || 'Failed to fetch file');
      }

      // Cache the result and clear any previous 404 cache
      fileCache.set(cacheKey, data);
      notFoundCache.delete(cacheKey);

      setContent(data);
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Request timed out. Try again.');
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load file');
      }
      setContent(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearContent = useCallback(() => {
    setContent(null);
    setError(null);
  }, []);

  return {
    content,
    isLoading,
    error,
    fetchFile,
    clearContent,
  };
}

// Clear cache (useful for testing or when workspaces change)
export function clearFileCache(): void {
  fileCache.clear();
  notFoundCache.clear();
}

// Clear 404 cache for a specific file (call when WebSocket reports file created/modified)
export function clearFileNotFound(filePath: string, workspacePath: string): void {
  const cacheKey = `${workspacePath}:${filePath}`;
  notFoundCache.delete(cacheKey);
  // Also clear content cache so we fetch fresh content
  fileCache.delete(cacheKey);
}

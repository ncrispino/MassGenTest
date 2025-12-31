/**
 * WebSocket Hook for Workspace Browser Real-Time Updates
 *
 * Manages WebSocket connection lifecycle for workspace file change notifications.
 * Implements auto-reconnect with exponential backoff and full refresh on reconnect.
 *
 * @see specs/001-fix-workspace-browser/spec.md FR-002, FR-012
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type {
  WorkspaceWSEvent,
  WorkspaceFileChangeEvent,
  WorkspaceFileInfo,
} from '../types';
import type { WebSocketConnectionStatus } from '../types/workspaceState';

interface UseWorkspaceWebSocketOptions {
  /** Current session ID */
  sessionId: string;
  /** Workspace paths to watch for changes */
  workspacePaths: string[];
  /** Callback when a file change is detected */
  onFileChange?: (event: WorkspaceFileChangeEvent) => void;
  /** Callback when connection is established */
  onConnected?: (watchedPaths: string[]) => void;
  /** Callback when initial files are received on connect (avoids HTTP fetch) */
  onInitialFiles?: (workspacePath: string, files: WorkspaceFileInfo[]) => void;
  /** Callback when full refresh is needed (e.g., after reconnect) */
  onRefreshNeeded?: (workspacePath: string, files: WorkspaceFileInfo[]) => void;
  /** Callback when an error occurs */
  onError?: (error: string) => void;
  /** Whether to auto-connect on mount */
  autoConnect?: boolean;
  /** Maximum reconnect attempts before giving up */
  maxReconnectAttempts?: number;
  /** Base interval for reconnect (ms), doubled on each attempt */
  reconnectBaseInterval?: number;
}

interface UseWorkspaceWebSocketReturn {
  /** Current connection status */
  status: WebSocketConnectionStatus;
  /** Number of reconnect attempts */
  reconnectAttempts: number;
  /** Last error message */
  error: string | null;
  /** Manually connect to WebSocket */
  connect: () => void;
  /** Manually disconnect from WebSocket */
  disconnect: () => void;
  /** Request a full refresh for a workspace */
  requestRefresh: (workspacePath: string) => void;
}

export function useWorkspaceWebSocket({
  sessionId,
  workspacePaths,
  onFileChange,
  onConnected,
  onInitialFiles,
  onRefreshNeeded,
  onError,
  autoConnect = true,
  maxReconnectAttempts = 5,
  reconnectBaseInterval = 1000,
}: UseWorkspaceWebSocketOptions): UseWorkspaceWebSocketReturn {
  const [status, setStatus] = useState<WebSocketConnectionStatus>('disconnected');
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const intentionalDisconnectRef = useRef(false);
  const workspacePathsRef = useRef(workspacePaths);
  // Track last watched paths to deduplicate watch messages (FR-014)
  const lastWatchedPathsKeyRef = useRef<string>('');
  // Store sessionId in ref to prevent stale closures during reconnect (FR-016)
  const sessionIdRef = useRef(sessionId);
  // Store connectInternal ref for stable access from scheduled reconnects
  const connectInternalRef = useRef<() => void>(() => {});

  // Keep refs updated
  useEffect(() => {
    workspacePathsRef.current = workspacePaths;
  }, [workspacePaths]);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  // Build WebSocket URL for workspace endpoint
  // Uses ref to ensure stable URL even during reconnect with stale closure
  const getWsUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}/ws/workspace/${sessionIdRef.current}`;
  }, []);

  // Handle incoming WebSocket messages
  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data: WorkspaceWSEvent = JSON.parse(event.data);

        switch (data.type) {
          case 'workspace_file_change':
            onFileChange?.(data);
            break;

          case 'workspace_connected':
            onConnected?.(data.watched_paths);
            // Dispatch initial files for each workspace (avoids HTTP fetch)
            if (data.initial_files && onInitialFiles) {
              for (const [wsPath, files] of Object.entries(data.initial_files)) {
                onInitialFiles(wsPath, files);
              }
            }
            break;

          case 'workspace_refresh':
            onRefreshNeeded?.(data.workspace_path, data.files);
            break;

          case 'workspace_error':
            setError(data.error);
            onError?.(data.error);
            break;

          default:
            console.warn('Unknown workspace WebSocket event:', data);
        }
      } catch (err) {
        console.error('Failed to parse workspace WebSocket message:', err);
      }
    },
    [onFileChange, onConnected, onInitialFiles, onRefreshNeeded, onError]
  );

  // Schedule reconnect with exponential backoff
  const scheduleReconnect = useCallback(() => {
    if (intentionalDisconnectRef.current) {
      return;
    }

    setReconnectAttempts((prev) => {
      const newAttempts = prev + 1;

      if (newAttempts > maxReconnectAttempts) {
        setStatus('disconnected');
        setError(`Failed to reconnect after ${maxReconnectAttempts} attempts`);
        return prev;
      }

      setStatus('reconnecting');

      // Exponential backoff: 1s, 2s, 4s, 8s, 16s
      const delay = reconnectBaseInterval * Math.pow(2, newAttempts - 1);
      console.log(
        `Workspace WebSocket reconnecting in ${delay}ms (attempt ${newAttempts}/${maxReconnectAttempts})`
      );

      reconnectTimeoutRef.current = setTimeout(() => {
        // Re-invoke connect using ref for latest version
        wsRef.current = null;
        connectInternalRef.current();
      }, delay);

      return newAttempts;
    });
  }, [maxReconnectAttempts, reconnectBaseInterval]);

  // Internal connect function
  // Uses sessionIdRef to ensure we always have the latest session ID during reconnect
  const connectInternal = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Use ref to get latest sessionId (not stale closure value)
    const currentSessionId = sessionIdRef.current;
    if (!currentSessionId) {
      console.warn('Cannot connect workspace WebSocket: no session ID');
      return;
    }

    setStatus('connecting');
    setError(null);

    try {
      const ws = new WebSocket(getWsUrl());

      ws.onopen = () => {
        setStatus('connected');
        setReconnectAttempts(0);
        setError(null);
        console.log('Workspace WebSocket connected');

        // Send watch request for current workspace paths
        if (workspacePathsRef.current.length > 0) {
          ws.send(
            JSON.stringify({
              action: 'watch',
              workspace_paths: workspacePathsRef.current,
            })
          );
        }
      };

      ws.onmessage = handleMessage;

      ws.onclose = (event) => {
        console.log('Workspace WebSocket disconnected:', event.code, event.reason);

        // Auto-reconnect if not intentionally closed
        if (!intentionalDisconnectRef.current && event.code !== 1000) {
          scheduleReconnect();
        } else {
          setStatus('disconnected');
        }
      };

      ws.onerror = (event) => {
        console.error('Workspace WebSocket error:', event);
        setError('WebSocket connection failed');
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create workspace WebSocket:', err);
      setStatus('disconnected');
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
    // Note: sessionId removed from deps - we use sessionIdRef.current instead
  }, [getWsUrl, handleMessage, scheduleReconnect]);

  // Keep connectInternal ref updated for scheduled reconnects
  useEffect(() => {
    connectInternalRef.current = connectInternal;
  }, [connectInternal]);

  // Public connect function
  const connect = useCallback(() => {
    intentionalDisconnectRef.current = false;
    setReconnectAttempts(0);
    connectInternal();
  }, [connectInternal]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    intentionalDisconnectRef.current = true;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setStatus('disconnected');
    setReconnectAttempts(0);
  }, []);

  // Request a full refresh for a specific workspace
  const requestRefresh = useCallback((workspacePath: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          action: 'refresh',
          workspace_path: workspacePath,
        })
      );
    } else {
      console.warn('Cannot request refresh: WebSocket not connected');
    }
  }, []);

  // Update watched paths when they change
  // FIX: Deduplicate watch messages to prevent flooding (FR-014)
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN && workspacePaths.length > 0) {
      // Create a stable key from sorted paths for comparison
      const pathsKey = [...workspacePaths].sort().join('|');

      // Only send if paths actually changed
      if (pathsKey !== lastWatchedPathsKeyRef.current) {
        lastWatchedPathsKeyRef.current = pathsKey;
        wsRef.current.send(
          JSON.stringify({
            action: 'watch',
            workspace_paths: workspacePaths,
          })
        );
      }
    }
  }, [workspacePaths]);

  // Track autoConnect in ref to prevent cleanup on transient false values
  const autoConnectRef = useRef(autoConnect);
  useEffect(() => {
    autoConnectRef.current = autoConnect;
  }, [autoConnect]);

  // Auto-connect on mount and when conditions become true
  // Only disconnect on unmount or when explicitly disabled
  useEffect(() => {
    // Connect when autoConnect becomes true and we have a session
    if (autoConnect && sessionIdRef.current && wsRef.current?.readyState !== WebSocket.OPEN) {
      connect();
    }

    // Only disconnect on component unmount, not on dependency changes
    return () => {
      // Check if this is an actual unmount vs just a re-render
      // We use a microtask to allow React's double-mount (StrictMode) to complete
      queueMicrotask(() => {
        // Only disconnect if autoConnect is still false after the microtask
        // This prevents disconnect during rapid re-renders
        if (!autoConnectRef.current) {
          disconnect();
        }
      });
    };
  }, [autoConnect, connect, disconnect]); // sessionId handled via ref

  // Handle sessionId changes - reconnect if we were connected
  useEffect(() => {
    if (sessionId && autoConnectRef.current && wsRef.current?.readyState !== WebSocket.OPEN) {
      connect();
    }
  }, [sessionId, connect]);

  return {
    status,
    reconnectAttempts,
    error,
    connect,
    disconnect,
    requestRefresh,
  };
}

export default useWorkspaceWebSocket;

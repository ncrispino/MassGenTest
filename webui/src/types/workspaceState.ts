/**
 * Workspace Browser State Machine Types
 *
 * This module defines the state machine for the workspace browser component.
 * Uses a discriminated union to ensure only valid state combinations.
 *
 * @see specs/001-fix-workspace-browser/data-model.md for design documentation
 */

import type { WorkspaceFileInfo } from './index';

// ============================================================================
// Workspace and Response Types
// ============================================================================

/**
 * Individual workspace metadata.
 */
export interface WorkspaceInfo {
  /** Human-readable workspace name (e.g., "workspace1") */
  name: string;
  /** Absolute filesystem path to workspace directory */
  path: string;
  /** Whether this is a live or archived workspace */
  type: 'current' | 'historical';
  /** ISO date string when workspace was created (optional for historical) */
  date?: string;
  /** Agent ID that owns this workspace (e.g., "agent_1") */
  agentId?: string;
}

/**
 * Response from /api/workspaces endpoint.
 */
export interface WorkspacesResponse {
  /** Workspaces for currently active session */
  current: WorkspaceInfo[];
  /** Historical workspaces from previous turns/sessions */
  historical: WorkspaceInfo[];
}

/**
 * Response from /api/workspace/browse endpoint.
 */
export interface BrowseResponse {
  /** List of files in the workspace */
  files: WorkspaceFileInfo[];
  /** Absolute path of the browsed workspace */
  workspace_path: string;
  /** Directory modification time for change detection */
  workspace_mtime?: number;
}

// ============================================================================
// State Machine Types
// ============================================================================

/**
 * Error types for workspace operations.
 */
export type WorkspaceErrorType = 'workspace-fetch' | 'file-fetch' | 'network' | 'status-json-unavailable';

/**
 * Idle state - modal closed or workspace tab not active.
 */
export interface WorkspaceIdleState {
  status: 'idle';
}

/**
 * Loading workspaces state - fetching available workspaces from API.
 */
export interface WorkspaceLoadingWorkspacesState {
  status: 'loading-workspaces';
}

/**
 * Loading files state - workspaces loaded, fetching files for selected workspace.
 */
export interface WorkspaceLoadingFilesState {
  status: 'loading-files';
  workspaces: WorkspacesResponse;
  selectedAgent: string | null;
}

/**
 * Ready state - all data loaded, displaying workspace content.
 */
export interface WorkspaceReadyState {
  status: 'ready';
  workspaces: WorkspacesResponse;
  files: WorkspaceFileInfo[];
  selectedAgent: string;
  selectedFilePath: string | null;
  lastRefreshed: number; // timestamp for staleness tracking
}

/**
 * Error state - something went wrong, may preserve last known good data.
 */
export interface WorkspaceErrorState {
  status: 'error';
  error: string;
  errorType: WorkspaceErrorType;
  /** Preserve last known good state for graceful degradation */
  lastKnownWorkspaces?: WorkspacesResponse;
  lastKnownFiles?: WorkspaceFileInfo[];
}

/**
 * Workspace browser state machine type.
 * Uses discriminated union to prevent invalid state combinations.
 */
export type WorkspaceBrowserState =
  | WorkspaceIdleState
  | WorkspaceLoadingWorkspacesState
  | WorkspaceLoadingFilesState
  | WorkspaceReadyState
  | WorkspaceErrorState;

// ============================================================================
// State Transition Actions
// ============================================================================

/**
 * Actions that can trigger state transitions.
 */
export type WorkspaceAction =
  | { type: 'OPEN_MODAL' }
  | { type: 'CLOSE_MODAL' }
  | { type: 'WORKSPACES_LOADED'; workspaces: WorkspacesResponse }
  | { type: 'WORKSPACES_ERROR'; error: string; errorType: WorkspaceErrorType }
  | { type: 'SELECT_AGENT'; agentId: string }
  | { type: 'FILES_LOADED'; files: WorkspaceFileInfo[] }
  | { type: 'FILES_ERROR'; error: string; errorType: WorkspaceErrorType }
  | { type: 'SELECT_FILE'; filePath: string }
  | { type: 'REFRESH' }
  | { type: 'FILE_CHANGED'; file: WorkspaceFileInfo; operation: 'create' | 'modify' | 'delete' };

// ============================================================================
// WebSocket Connection State
// ============================================================================

/**
 * WebSocket connection status for workspace updates.
 */
export type WebSocketConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'reconnecting';

/**
 * WebSocket state for workspace browser.
 */
export interface WorkspaceWebSocketState {
  status: WebSocketConnectionStatus;
  lastConnected?: number;
  reconnectAttempts: number;
  error?: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Type guard to check if state is in a loading state.
 */
export function isLoading(state: WorkspaceBrowserState): boolean {
  return state.status === 'loading-workspaces' || state.status === 'loading-files';
}

/**
 * Type guard to check if state has workspaces available.
 */
export function hasWorkspaces(
  state: WorkspaceBrowserState
): state is WorkspaceLoadingFilesState | WorkspaceReadyState {
  return state.status === 'loading-files' || state.status === 'ready';
}

/**
 * Type guard to check if state has files available.
 */
export function hasFiles(state: WorkspaceBrowserState): state is WorkspaceReadyState {
  return state.status === 'ready';
}

/**
 * Get files from state, falling back to last known files in error state.
 */
export function getFiles(state: WorkspaceBrowserState): WorkspaceFileInfo[] {
  if (state.status === 'ready') {
    return state.files;
  }
  if (state.status === 'error' && state.lastKnownFiles) {
    return state.lastKnownFiles;
  }
  return [];
}

/**
 * Get workspaces from state, falling back to last known workspaces in error state.
 */
export function getWorkspaces(state: WorkspaceBrowserState): WorkspacesResponse | null {
  if (state.status === 'loading-files' || state.status === 'ready') {
    return state.workspaces;
  }
  if (state.status === 'error' && state.lastKnownWorkspaces) {
    return state.lastKnownWorkspaces;
  }
  return null;
}

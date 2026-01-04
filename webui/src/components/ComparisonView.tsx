/**
 * ComparisonView Component
 *
 * Side-by-side comparison of files from different agents or answer versions.
 * Supports both visual comparison (for HTML, images) and diff view (for code).
 */

import { useState, useEffect, useMemo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { X, Columns, GitCompare, ChevronDown, Loader2, Split } from 'lucide-react';
import { InlineArtifactPreview } from './InlineArtifactPreview';
import { FileDiffView } from './FileDiffView';
import { getAgentColor } from '../utils/agentColors';
import type { AnswerWorkspace } from '../types';

interface ComparisonSource {
  agentId: string;
  answerLabel: string;
  workspacePath: string;
  filePath: string;
}

interface WorkspaceInfo {
  path: string;
  answerLabel?: string;
  name?: string;
}

interface ComparisonViewProps {
  /** Whether the comparison view is open */
  isOpen: boolean;
  /** Close the comparison view */
  onClose: () => void;
  /** Available agents and their workspaces (current from filesystem) */
  agentWorkspaces: Record<string, {
    current?: WorkspaceInfo;
    historical: WorkspaceInfo[];
  }>;
  /** Historical answer workspaces (from status.json) */
  answerWorkspaces: AnswerWorkspace[];
  /** Agent order for consistent coloring */
  agentOrder: string[];
  /** Session ID for live preview */
  sessionId?: string;
  /** Initial file to compare (optional) */
  initialFile?: string;
}

export function ComparisonView({
  isOpen,
  onClose,
  agentWorkspaces,
  answerWorkspaces,
  agentOrder,
  sessionId,
  initialFile: _initialFile,
}: ComparisonViewProps) {
  // Left and right panel selections
  const [leftSource, setLeftSource] = useState<ComparisonSource | null>(null);
  const [rightSource, setRightSource] = useState<ComparisonSource | null>(null);

  // File lists for each panel
  const [leftFiles, setLeftFiles] = useState<string[]>([]);
  const [rightFiles, setRightFiles] = useState<string[]>([]);
  const [isLoadingLeft, setIsLoadingLeft] = useState(false);
  const [isLoadingRight, setIsLoadingRight] = useState(false);

  // Diff mode state
  const [showDiff, setShowDiff] = useState(false);
  const [leftContent, setLeftContent] = useState<string | null>(null);
  const [rightContent, setRightContent] = useState<string | null>(null);
  const [isLoadingDiff, setIsLoadingDiff] = useState(false);
  const [diffError, setDiffError] = useState<string | null>(null);

  // Helper to extract filename from path
  const getFileName = useCallback((path: string) => path.split('/').pop() || path, []);

  // Check if both files have the same name (enabling diff mode)
  const canShowDiff = useMemo(() => {
    if (!leftSource?.filePath || !rightSource?.filePath) return false;
    const leftName = getFileName(leftSource.filePath);
    const rightName = getFileName(rightSource.filePath);
    return leftName === rightName;
  }, [leftSource?.filePath, rightSource?.filePath, getFileName]);

  // Get labels for diff view
  const getSourceLabel = useCallback((source: ComparisonSource | null) => {
    if (!source) return '';
    const agentIdx = agentOrder.indexOf(source.agentId);
    const agentNum = agentIdx >= 0 ? agentIdx + 1 : 0;
    return agentNum > 0 ? `Agent ${agentNum} - ${source.answerLabel}` : source.answerLabel;
  }, [agentOrder]);

  // Fetch file content for diff - returns { content, error } to distinguish failure types
  const fetchFileContent = useCallback(async (workspacePath: string, filePath: string): Promise<{ content: string | null; error?: string }> => {
    try {
      console.log('[ComparisonView] Fetching file for diff:', { workspace: workspacePath, path: filePath });
      // API requires separate workspace and relative path parameters
      const response = await fetch(`/api/workspace/file?workspace=${encodeURIComponent(workspacePath)}&path=${encodeURIComponent(filePath)}`);

      if (!response.ok) {
        console.error('[ComparisonView] File fetch failed:', response.status, response.statusText);
        return { content: null, error: `Failed to load file (${response.status})` };
      }

      const data = await response.json();
      console.log('[ComparisonView] File data received:', { binary: data.binary, size: data.size, hasContent: !!data.content });

      // Check if content is binary
      if (data.binary) {
        return { content: null, error: 'Binary file cannot be diffed' };
      }

      return { content: data.content || '' };
    } catch (err) {
      console.error('[ComparisonView] Error fetching file for diff:', err);
      return { content: null, error: `Error loading file: ${err}` };
    }
  }, []);

  // Load both file contents when diff mode is enabled
  useEffect(() => {
    if (showDiff && canShowDiff && leftSource?.filePath && rightSource?.filePath) {
      setIsLoadingDiff(true);
      setDiffError(null);
      Promise.all([
        fetchFileContent(leftSource.workspacePath, leftSource.filePath),
        fetchFileContent(rightSource.workspacePath, rightSource.filePath),
      ]).then(([leftResult, rightResult]) => {
        // Check for errors
        if (leftResult.error || rightResult.error) {
          const errors = [leftResult.error, rightResult.error].filter(Boolean);
          setDiffError(errors.join(' | '));
          setLeftContent(null);
          setRightContent(null);
        } else {
          setLeftContent(leftResult.content);
          setRightContent(rightResult.content);
        }
        setIsLoadingDiff(false);
      });
    } else {
      setLeftContent(null);
      setRightContent(null);
      setDiffError(null);
    }
  }, [showDiff, canShowDiff, leftSource?.workspacePath, leftSource?.filePath, rightSource?.workspacePath, rightSource?.filePath, fetchFileContent]);

  // Reset diff mode when files change
  useEffect(() => {
    setShowDiff(false);
  }, [leftSource?.filePath, rightSource?.filePath]);

  // Build options for dropdowns - merge current workspaces + answer workspaces
  const sourceOptions = useMemo(() => {
    const options: Array<{ agentId: string; answerLabel: string; workspacePath: string; displayName: string }> = [];
    const seenPaths = new Set<string>(); // Avoid duplicates

    // First add current workspaces
    agentOrder.forEach((agentId, index) => {
      const agentData = agentWorkspaces[agentId];
      if (!agentData) return;

      const agentNum = index + 1;

      // Current workspace
      if (agentData.current && !seenPaths.has(agentData.current.path)) {
        seenPaths.add(agentData.current.path);
        options.push({
          agentId,
          answerLabel: 'current',
          workspacePath: agentData.current.path,
          displayName: `Agent ${agentNum} - Current`,
        });
      }
    });

    // Then add all historical answer workspaces
    answerWorkspaces.forEach((aw) => {
      if (seenPaths.has(aw.workspacePath)) return;
      seenPaths.add(aw.workspacePath);

      const agentIdx = agentOrder.indexOf(aw.agentId);
      const agentNum = agentIdx >= 0 ? agentIdx + 1 : 0;
      const displayLabel = aw.answerLabel || `Answer ${aw.answerNumber}`;

      options.push({
        agentId: aw.agentId,
        answerLabel: displayLabel,
        workspacePath: aw.workspacePath,
        displayName: agentNum > 0 ? `Agent ${agentNum} - ${displayLabel}` : displayLabel,
      });
    });

    // Sort by agent number, then by answer label
    options.sort((a, b) => {
      const aIdx = agentOrder.indexOf(a.agentId);
      const bIdx = agentOrder.indexOf(b.agentId);
      if (aIdx !== bIdx) return aIdx - bIdx;
      // Put 'current' first
      if (a.answerLabel === 'current') return -1;
      if (b.answerLabel === 'current') return 1;
      return a.answerLabel.localeCompare(b.answerLabel);
    });

    console.log('[ComparisonView] Built sourceOptions:', options);
    console.log('[ComparisonView] agentWorkspaces:', agentWorkspaces);
    console.log('[ComparisonView] answerWorkspaces:', answerWorkspaces);
    return options;
  }, [agentWorkspaces, answerWorkspaces, agentOrder]);

  // Auto-select first two options when opening
  useEffect(() => {
    if (isOpen && sourceOptions.length >= 2 && !leftSource && !rightSource) {
      const first = sourceOptions[0];
      const second = sourceOptions[1];

      // Don't auto-set filePath - let user select after files load
      setLeftSource({
        agentId: first.agentId,
        answerLabel: first.answerLabel,
        workspacePath: first.workspacePath,
        filePath: '',
      });
      setRightSource({
        agentId: second.agentId,
        answerLabel: second.answerLabel,
        workspacePath: second.workspacePath,
        filePath: '',
      });
    }
  }, [isOpen, sourceOptions, leftSource, rightSource]);

  // Fetch files when workspace changes
  const fetchFiles = async (workspacePath: string, setSide: 'left' | 'right') => {
    const setLoading = setSide === 'left' ? setIsLoadingLeft : setIsLoadingRight;
    const setFiles = setSide === 'left' ? setLeftFiles : setRightFiles;

    if (!workspacePath) {
      console.warn(`[ComparisonView] ${setSide}: No workspace path provided`);
      setFiles([]);
      return;
    }

    console.log(`[ComparisonView] ${setSide}: Fetching files from:`, workspacePath);
    setLoading(true);
    try {
      const response = await fetch(`/api/workspace/browse?path=${encodeURIComponent(workspacePath)}`);
      console.log(`[ComparisonView] ${setSide}: Response status:`, response.status);

      if (response.ok) {
        const data = await response.json();
        console.log(`[ComparisonView] ${setSide}: Raw response:`, data);
        // API returns files with {path, size, modified} - no type field
        // All entries are files (directories are not returned by the API)
        const files = (data.files || []).map((f: { path: string }) => f.path);
        console.log(`[ComparisonView] ${setSide}: Found ${files.length} files:`, files);
        setFiles(files);
      } else {
        const errorText = await response.text();
        console.error(`[ComparisonView] ${setSide}: Failed to fetch files:`, response.status, errorText);
        setFiles([]);
      }
    } catch (err) {
      console.error(`[ComparisonView] ${setSide}: Error fetching files:`, err);
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (leftSource?.workspacePath) {
      fetchFiles(leftSource.workspacePath, 'left');
    }
  }, [leftSource?.workspacePath]);

  useEffect(() => {
    if (rightSource?.workspacePath) {
      fetchFiles(rightSource.workspacePath, 'right');
    }
  }, [rightSource?.workspacePath]);

  // Handle source selection
  const handleSourceChange = (side: 'left' | 'right', option: typeof sourceOptions[0]) => {
    const newSource: ComparisonSource = {
      agentId: option.agentId,
      answerLabel: option.answerLabel,
      workspacePath: option.workspacePath,
      filePath: '',
    };

    if (side === 'left') {
      setLeftSource(newSource);
    } else {
      setRightSource(newSource);
    }
  };

  // Handle file selection
  const handleFileSelect = (side: 'left' | 'right', filePath: string) => {
    if (side === 'left' && leftSource) {
      setLeftSource({ ...leftSource, filePath });
    } else if (side === 'right' && rightSource) {
      setRightSource({ ...rightSource, filePath });
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[60] flex items-center justify-center"
      onClick={onClose}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="w-[95vw] h-[90vh] bg-gray-800 rounded-xl border border-gray-600 shadow-2xl flex flex-col overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 bg-gray-900/50">
          <div className="flex items-center gap-3">
            <Columns className="w-6 h-6 text-purple-400" />
            <h2 className="text-xl font-semibold text-gray-100">Side-by-Side Comparison</h2>
          </div>
          <div className="flex items-center gap-3">
            {/* Diff toggle - only shown when both files have the same name */}
            {canShowDiff && (
              <button
                onClick={() => setShowDiff(!showDiff)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors ${
                  showDiff
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                title="Toggle diff view (available for same-name files)"
              >
                <Split className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {showDiff ? 'Diff View' : 'Show Diff'}
                </span>
              </button>
            )}
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>
        </div>

        {/* Main content - two panels or diff view */}
        {showDiff && canShowDiff ? (
          // Diff view mode
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Source selectors row */}
            <div className="flex border-b border-gray-700">
              <div className="flex-1 p-3 bg-gray-800/50">
                <SourceSelector
                  source={leftSource}
                  sourceOptions={sourceOptions}
                  agentOrder={agentOrder}
                  onSourceChange={(opt) => handleSourceChange('left', opt)}
                />
                <div className="mt-2">
                  <select
                    value={leftSource?.filePath || ''}
                    onChange={(e) => handleFileSelect('left', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a file...</option>
                    {leftFiles.map((file) => (
                      <option key={file} value={file}>{file}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="w-px bg-gray-600" />
              <div className="flex-1 p-3 bg-gray-800/50">
                <SourceSelector
                  source={rightSource}
                  sourceOptions={sourceOptions}
                  agentOrder={agentOrder}
                  onSourceChange={(opt) => handleSourceChange('right', opt)}
                />
                <div className="mt-2">
                  <select
                    value={rightSource?.filePath || ''}
                    onChange={(e) => handleFileSelect('right', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">Select a file...</option>
                    {rightFiles.map((file) => (
                      <option key={file} value={file}>{file}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Diff content */}
            <div className="flex-1 min-h-0 overflow-hidden p-3">
              {isLoadingDiff ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Loader2 className="w-8 h-8 animate-spin mb-3" />
                  <span>Loading diff...</span>
                </div>
              ) : diffError ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <GitCompare className="w-12 h-12 mb-4 opacity-50" />
                  <span className="text-red-400">{diffError}</span>
                  <span className="text-sm mt-1 text-gray-600">Check console for details</span>
                </div>
              ) : leftContent === null || rightContent === null ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <GitCompare className="w-12 h-12 mb-4 opacity-50" />
                  <span>Could not load file content</span>
                  <span className="text-sm mt-1">Select files to compare</span>
                </div>
              ) : (
                <FileDiffView
                  leftContent={leftContent}
                  rightContent={rightContent}
                  leftLabel={getSourceLabel(leftSource)}
                  rightLabel={getSourceLabel(rightSource)}
                  fileName={getFileName(leftSource?.filePath || '')}
                />
              )}
            </div>
          </div>
        ) : (
          // Side-by-side preview mode
          <div className="flex-1 flex overflow-hidden">
            {/* Left Panel */}
            <ComparisonPanel
              side="left"
              source={leftSource}
              files={leftFiles}
              isLoading={isLoadingLeft}
              sourceOptions={sourceOptions}
              agentOrder={agentOrder}
              sessionId={sessionId}
              onSourceChange={(opt) => handleSourceChange('left', opt)}
              onFileSelect={(f) => handleFileSelect('left', f)}
            />

            {/* Divider */}
            <div className="w-px bg-gray-600" />

            {/* Right Panel */}
            <ComparisonPanel
              side="right"
              source={rightSource}
              files={rightFiles}
              isLoading={isLoadingRight}
              sourceOptions={sourceOptions}
              agentOrder={agentOrder}
              sessionId={sessionId}
              onSourceChange={(opt) => handleSourceChange('right', opt)}
              onFileSelect={(f) => handleFileSelect('right', f)}
            />
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}

interface SourceOption {
  agentId: string;
  answerLabel: string;
  workspacePath: string;
  displayName: string;
}

// Reusable source selector dropdown
interface SourceSelectorProps {
  source: ComparisonSource | null;
  sourceOptions: SourceOption[];
  agentOrder: string[];
  onSourceChange: (option: SourceOption) => void;
}

function SourceSelector({ source, sourceOptions, agentOrder, onSourceChange }: SourceSelectorProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const selectedOption = sourceOptions.find(
    (opt) => opt.workspacePath === source?.workspacePath
  );

  const agentColor = source ? getAgentColor(source.agentId, agentOrder) : null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className={`w-full flex items-center justify-between px-4 py-2 rounded-lg border transition-colors ${
          agentColor
            ? `${agentColor.bgLight} ${agentColor.border} ${agentColor.text}`
            : 'bg-gray-700 border-gray-600 text-gray-300'
        }`}
      >
        <span className="truncate">
          {selectedOption?.displayName || 'Select source...'}
        </span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
      </button>

      {isDropdownOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-10 max-h-60 overflow-y-auto">
          {sourceOptions.map((opt, idx) => {
            const optColor = getAgentColor(opt.agentId, agentOrder);
            return (
              <button
                key={`${opt.workspacePath}-${idx}`}
                onClick={() => {
                  onSourceChange(opt);
                  setIsDropdownOpen(false);
                }}
                className={`w-full px-4 py-2 text-left hover:bg-gray-700 transition-colors ${
                  opt.workspacePath === source?.workspacePath ? optColor.bgLight : ''
                }`}
              >
                <span className={optColor.text}>{opt.displayName}</span>
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

interface ComparisonPanelProps {
  side: 'left' | 'right';
  source: ComparisonSource | null;
  files: string[];
  isLoading: boolean;
  sourceOptions: SourceOption[];
  agentOrder: string[];
  sessionId?: string;
  onSourceChange: (option: SourceOption) => void;
  onFileSelect: (filePath: string) => void;
}

function ComparisonPanel({
  side: _side,
  source,
  files,
  isLoading,
  sourceOptions,
  agentOrder,
  sessionId,
  onSourceChange,
  onFileSelect,
}: ComparisonPanelProps) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  const selectedOption = sourceOptions.find(
    (opt) => opt.workspacePath === source?.workspacePath
  );

  const agentColor = source ? getAgentColor(source.agentId, agentOrder) : null;

  return (
    <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
      {/* Source selector */}
      <div className="p-3 border-b border-gray-700 bg-gray-800/50">
        <div className="relative">
          <button
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className={`w-full flex items-center justify-between px-4 py-2 rounded-lg border transition-colors ${
              agentColor
                ? `${agentColor.bgLight} ${agentColor.border} ${agentColor.text}`
                : 'bg-gray-700 border-gray-600 text-gray-300'
            }`}
          >
            <span className="truncate">
              {selectedOption?.displayName || 'Select source...'}
            </span>
            <ChevronDown className={`w-4 h-4 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isDropdownOpen && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-gray-800 border border-gray-600 rounded-lg shadow-xl z-10 max-h-60 overflow-y-auto">
              {sourceOptions.map((opt, idx) => {
                const optColor = getAgentColor(opt.agentId, agentOrder);
                return (
                  <button
                    key={`${opt.workspacePath}-${idx}`}
                    onClick={() => {
                      onSourceChange(opt);
                      setIsDropdownOpen(false);
                    }}
                    className={`w-full px-4 py-2 text-left hover:bg-gray-700 transition-colors ${
                      opt.workspacePath === source?.workspacePath ? optColor.bgLight : ''
                    }`}
                  >
                    <span className={optColor.text}>{opt.displayName}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* File selector */}
        {source && (
          <div className="mt-2">
            <select
              value={source.filePath}
              onChange={(e) => onFileSelect(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select a file...</option>
              {files.map((file) => (
                <option key={file} value={file}>
                  {file}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Preview area */}
      <div className="flex-1 min-h-0 overflow-auto p-3">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin mb-3" />
            <span>Loading files...</span>
          </div>
        ) : !source ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <Columns className="w-12 h-12 mb-4 opacity-50" />
            <span>Select a source to compare</span>
          </div>
        ) : !source.filePath ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <GitCompare className="w-12 h-12 mb-4 opacity-50" />
            <span>Select a file to preview</span>
            <span className="text-sm mt-1 text-gray-600">
              {files.length} files available
            </span>
          </div>
        ) : (
          <InlineArtifactPreview
            filePath={source.filePath}
            workspacePath={source.workspacePath}
            sessionId={sessionId}
            agentId={source.agentId}
          />
        )}
      </div>
    </div>
  );
}

export default ComparisonView;

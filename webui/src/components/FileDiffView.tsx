/**
 * FileDiffView Component
 *
 * Shows a git-style diff between two file contents.
 * Only used when comparing files with the same name.
 */

import { useMemo } from 'react';
import { diffLines, type Change } from 'diff';
import { GitCompare, Plus, Minus, Equal } from 'lucide-react';

interface FileDiffViewProps {
  /** Left file content */
  leftContent: string;
  /** Right file content */
  rightContent: string;
  /** Left label (e.g., "Agent 1 - agent1.1") */
  leftLabel: string;
  /** Right label (e.g., "Agent 2 - agent2.1") */
  rightLabel: string;
  /** File name being compared */
  fileName: string;
}

export function FileDiffView({
  leftContent,
  rightContent,
  leftLabel,
  rightLabel,
  fileName,
}: FileDiffViewProps) {
  // Compute the diff
  const diffResult = useMemo(() => {
    return diffLines(leftContent, rightContent);
  }, [leftContent, rightContent]);

  // Calculate statistics
  const stats = useMemo(() => {
    let additions = 0;
    let deletions = 0;
    let unchanged = 0;

    diffResult.forEach((part) => {
      const lines = part.value.split('\n').filter((l) => l !== '').length;
      if (part.added) {
        additions += lines;
      } else if (part.removed) {
        deletions += lines;
      } else {
        unchanged += lines;
      }
    });

    return { additions, deletions, unchanged };
  }, [diffResult]);

  // Check if files are identical
  const isIdentical = stats.additions === 0 && stats.deletions === 0;

  return (
    <div className="h-full flex flex-col bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <GitCompare className="w-5 h-5 text-purple-400" />
          <span className="font-medium text-gray-200">Diff: {fileName}</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          {isIdentical ? (
            <span className="text-green-400 flex items-center gap-1">
              <Equal className="w-4 h-4" />
              Files are identical
            </span>
          ) : (
            <>
              <span className="text-green-400 flex items-center gap-1">
                <Plus className="w-4 h-4" />
                {stats.additions} additions
              </span>
              <span className="text-red-400 flex items-center gap-1">
                <Minus className="w-4 h-4" />
                {stats.deletions} deletions
              </span>
            </>
          )}
        </div>
      </div>

      {/* Labels */}
      <div className="flex border-b border-gray-700 text-sm">
        <div className="flex-1 px-4 py-2 bg-red-900/20 text-red-300 border-r border-gray-700">
          <Minus className="w-3 h-3 inline mr-2" />
          {leftLabel}
        </div>
        <div className="flex-1 px-4 py-2 bg-green-900/20 text-green-300">
          <Plus className="w-3 h-3 inline mr-2" />
          {rightLabel}
        </div>
      </div>

      {/* Diff content */}
      <div className="flex-1 overflow-auto">
        <pre className="text-sm font-mono p-0 m-0">
          {diffResult.map((part, index) => (
            <DiffBlock key={index} part={part} />
          ))}
        </pre>
      </div>
    </div>
  );
}

interface DiffBlockProps {
  part: Change;
}

function DiffBlock({ part }: DiffBlockProps) {
  const lines = part.value.split('\n');
  // Remove trailing empty line from split
  if (lines[lines.length - 1] === '') {
    lines.pop();
  }

  if (part.added) {
    return (
      <>
        {lines.map((line, i) => (
          <div
            key={i}
            className="px-4 py-0.5 bg-green-900/30 text-green-300 border-l-4 border-green-500"
          >
            <span className="text-green-500 mr-2 select-none">+</span>
            {line || ' '}
          </div>
        ))}
      </>
    );
  }

  if (part.removed) {
    return (
      <>
        {lines.map((line, i) => (
          <div
            key={i}
            className="px-4 py-0.5 bg-red-900/30 text-red-300 border-l-4 border-red-500"
          >
            <span className="text-red-500 mr-2 select-none">-</span>
            {line || ' '}
          </div>
        ))}
      </>
    );
  }

  // Unchanged lines
  return (
    <>
      {lines.map((line, i) => (
        <div key={i} className="px-4 py-0.5 text-gray-400">
          <span className="text-gray-600 mr-2 select-none"> </span>
          {line || ' '}
        </div>
      ))}
    </>
  );
}

export default FileDiffView;

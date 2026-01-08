/**
 * ResizableSplitPane Component
 *
 * A horizontal split pane with a draggable divider.
 * Stores the split ratio in localStorage for persistence.
 */

import { useState, useRef, useCallback, useEffect, type ReactNode } from 'react';
import { GripVertical } from 'lucide-react';

interface ResizableSplitPaneProps {
  /** Left panel content */
  left: ReactNode;
  /** Right panel content */
  right: ReactNode;
  /** Unique key for localStorage persistence */
  storageKey?: string;
  /** Initial left panel width as percentage (0-100) */
  defaultLeftWidth?: number;
  /** Minimum left panel width as percentage */
  minLeftWidth?: number;
  /** Maximum left panel width as percentage */
  maxLeftWidth?: number;
  /** Additional className for the container */
  className?: string;
}

export function ResizableSplitPane({
  left,
  right,
  storageKey = 'split-pane-width',
  defaultLeftWidth = 30,
  minLeftWidth = 15,
  maxLeftWidth = 60,
  className = '',
}: ResizableSplitPaneProps) {
  // Load saved width or use default
  const [leftWidth, setLeftWidth] = useState(() => {
    if (typeof window === 'undefined') return defaultLeftWidth;
    const saved = localStorage.getItem(storageKey);
    if (saved) {
      const parsed = parseFloat(saved);
      if (!isNaN(parsed) && parsed >= minLeftWidth && parsed <= maxLeftWidth) {
        return parsed;
      }
    }
    return defaultLeftWidth;
  });

  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Save to localStorage when width changes
  useEffect(() => {
    localStorage.setItem(storageKey, String(leftWidth));
  }, [leftWidth, storageKey]);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const newWidth = (x / rect.width) * 100;

      // Clamp to min/max
      const clampedWidth = Math.max(minLeftWidth, Math.min(maxLeftWidth, newWidth));
      setLeftWidth(clampedWidth);
    },
    [isDragging, minLeftWidth, maxLeftWidth]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Add/remove global mouse listeners when dragging
  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      // Prevent text selection while dragging
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
    } else {
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div ref={containerRef} className={`flex h-full overflow-hidden ${className}`}>
      {/* Left Panel */}
      <div
        className="overflow-hidden flex-shrink-0"
        style={{ width: `${leftWidth}%` }}
      >
        {left}
      </div>

      {/* Resizer */}
      <div
        onMouseDown={handleMouseDown}
        className={`w-1.5 flex-shrink-0 cursor-col-resize flex items-center justify-center group transition-colors ${
          isDragging
            ? 'bg-blue-500'
            : 'bg-gray-700 hover:bg-blue-500/50'
        }`}
      >
        <GripVertical
          className={`w-3 h-6 transition-colors ${
            isDragging
              ? 'text-white'
              : 'text-gray-500 group-hover:text-blue-300'
          }`}
        />
      </div>

      {/* Right Panel */}
      <div className="flex-1 overflow-hidden min-w-0">
        {right}
      </div>
    </div>
  );
}

export default ResizableSplitPane;

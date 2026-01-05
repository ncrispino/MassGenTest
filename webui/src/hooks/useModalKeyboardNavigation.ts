/**
 * useModalKeyboardNavigation Hook
 *
 * Provides keyboard navigation within the Browser modal.
 * Supports tab switching, list navigation, and item selection.
 */

import { useEffect, useCallback, useState } from 'react';

export type TabType = 'answers' | 'votes' | 'workspace' | 'timeline';

const TAB_ORDER: TabType[] = ['answers', 'votes', 'workspace', 'timeline'];

interface UseModalKeyboardNavigationOptions {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Current active tab */
  activeTab: TabType;
  /** Number of items in the current list */
  itemCount: number;
  /** Callback when tab changes */
  onTabChange: (tab: TabType) => void;
  /** Callback when selected item changes */
  onItemSelect: (index: number) => void;
  /** Callback when item is activated (Enter/Space) */
  onItemActivate?: (index: number) => void;
  /** Callback to close the modal */
  onClose: () => void;
  /** Whether to enable navigation (disabled when focused on input) */
  enabled?: boolean;
}

interface ModalNavigationState {
  /** Currently selected item index (-1 = none) */
  selectedIndex: number;
  /** Whether keyboard navigation is actively being used */
  isNavigating: boolean;
}

export interface ModalKeyboardShortcut {
  key: string;
  description: string;
  category: 'tabs' | 'navigation' | 'actions';
}

/** Shortcuts available within the modal */
export const MODAL_SHORTCUTS: ModalKeyboardShortcut[] = [
  { key: '1', description: 'Answers tab', category: 'tabs' },
  { key: '2', description: 'Votes tab', category: 'tabs' },
  { key: '3', description: 'Workspace tab', category: 'tabs' },
  { key: '4', description: 'Timeline tab', category: 'tabs' },
  { key: 'j / ↓', description: 'Move down', category: 'navigation' },
  { key: 'k / ↑', description: 'Move up', category: 'navigation' },
  { key: 'Enter', description: 'Expand / Select', category: 'actions' },
  { key: 'Esc', description: 'Close modal', category: 'actions' },
];

export function useModalKeyboardNavigation(options: UseModalKeyboardNavigationOptions) {
  const {
    isOpen,
    activeTab,
    itemCount,
    onTabChange,
    onItemSelect,
    onItemActivate,
    onClose,
    enabled = true,
  } = options;

  const [state, setState] = useState<ModalNavigationState>({
    selectedIndex: -1,
    isNavigating: false,
  });

  // Reset selection when tab changes or modal closes
  useEffect(() => {
    setState({ selectedIndex: -1, isNavigating: false });
  }, [activeTab, isOpen]);

  // Notify parent of selection changes
  useEffect(() => {
    if (state.selectedIndex >= 0) {
      onItemSelect(state.selectedIndex);
    }
  }, [state.selectedIndex, onItemSelect]);

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!isOpen || !enabled) return;

      // Skip if focused on an input/textarea
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.isContentEditable
      ) {
        return;
      }

      // Don't interfere with modifier key combinations (except Shift for ?)
      if (event.ctrlKey || event.altKey || event.metaKey) {
        return;
      }

      let handled = false;

      switch (event.key) {
        // Tab switching with number keys
        case '1':
        case '2':
        case '3':
        case '4': {
          const tabIndex = parseInt(event.key, 10) - 1;
          if (tabIndex >= 0 && tabIndex < TAB_ORDER.length) {
            onTabChange(TAB_ORDER[tabIndex]);
            handled = true;
          }
          break;
        }

        // Navigate down
        case 'j':
        case 'ArrowDown': {
          if (itemCount > 0) {
            setState((prev) => ({
              selectedIndex: Math.min(prev.selectedIndex + 1, itemCount - 1),
              isNavigating: true,
            }));
            handled = true;
          }
          break;
        }

        // Navigate up
        case 'k':
        case 'ArrowUp': {
          if (itemCount > 0) {
            setState((prev) => ({
              selectedIndex: Math.max(prev.selectedIndex - 1, 0),
              isNavigating: true,
            }));
            handled = true;
          }
          break;
        }

        // Jump to first item
        case 'Home': {
          if (itemCount > 0) {
            setState({ selectedIndex: 0, isNavigating: true });
            handled = true;
          }
          break;
        }

        // Jump to last item
        case 'End': {
          if (itemCount > 0) {
            setState({ selectedIndex: itemCount - 1, isNavigating: true });
            handled = true;
          }
          break;
        }

        // Activate selected item
        case 'Enter':
        case ' ': {
          if (state.selectedIndex >= 0 && onItemActivate) {
            onItemActivate(state.selectedIndex);
            handled = true;
          }
          break;
        }

        // Close modal
        case 'Escape': {
          onClose();
          handled = true;
          break;
        }
      }

      if (handled) {
        event.preventDefault();
        event.stopPropagation();
      }
    },
    [isOpen, enabled, activeTab, itemCount, state.selectedIndex, onTabChange, onItemActivate, onClose]
  );

  // Register keyboard listener
  useEffect(() => {
    if (isOpen && enabled) {
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, enabled, handleKeyDown]);

  // Clear navigation state when clicking with mouse
  const clearNavigation = useCallback(() => {
    setState({ selectedIndex: -1, isNavigating: false });
  }, []);

  // Set specific selection (for mouse hover integration)
  const setSelectedIndex = useCallback((index: number) => {
    setState({ selectedIndex: index, isNavigating: false });
  }, []);

  return {
    /** Current selected index (-1 = none) */
    selectedIndex: state.selectedIndex,
    /** Whether user is actively navigating with keyboard */
    isNavigating: state.isNavigating,
    /** Clear the current selection */
    clearNavigation,
    /** Set selection to specific index */
    setSelectedIndex,
    /** Available shortcuts for display in help */
    shortcuts: MODAL_SHORTCUTS,
  };
}

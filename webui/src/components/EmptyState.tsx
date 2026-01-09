/**
 * EmptyState Component
 *
 * Reusable component for displaying empty states with helpful messages and hints.
 * Used throughout the Browser modal for consistent empty state UX.
 */

import { motion } from 'framer-motion';
import { type LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  /** Icon to display */
  icon: LucideIcon;
  /** Main title */
  title: string;
  /** Description text */
  description: string;
  /** Optional hint text (shown in slightly different style) */
  hint?: string;
  /** Optional action button */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  hint,
  action,
  size = 'md',
}: EmptyStateProps) {
  const sizeClasses = {
    sm: {
      container: 'py-6',
      icon: 'w-10 h-10',
      title: 'text-sm',
      description: 'text-xs',
      hint: 'text-xs',
    },
    md: {
      container: 'py-12',
      icon: 'w-14 h-14',
      title: 'text-base',
      description: 'text-sm',
      hint: 'text-xs',
    },
    lg: {
      container: 'py-16',
      icon: 'w-20 h-20',
      title: 'text-lg',
      description: 'text-base',
      hint: 'text-sm',
    },
  };

  const classes = sizeClasses[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex flex-col items-center justify-center ${classes.container} text-center`}
    >
      {/* Icon with subtle background */}
      <div className="relative mb-4">
        <div className="absolute inset-0 bg-gray-700/30 rounded-full blur-xl" />
        <div className="relative p-4 bg-gray-800/50 rounded-full border border-gray-700/50">
          <Icon className={`${classes.icon} text-gray-500`} />
        </div>
      </div>

      {/* Title */}
      <h3 className={`${classes.title} font-medium text-gray-300 mb-1`}>
        {title}
      </h3>

      {/* Description */}
      <p className={`${classes.description} text-gray-500 max-w-xs mb-3`}>
        {description}
      </p>

      {/* Hint */}
      {hint && (
        <p className={`${classes.hint} text-gray-600 italic max-w-xs`}>
          {hint}
        </p>
      )}

      {/* Action button */}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 px-4 py-2 text-sm font-medium text-gray-300 bg-gray-800
                     hover:bg-gray-700 border border-gray-600 rounded-lg
                     transition-colors duration-200"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  );
}

// Pre-configured empty states for common use cases
export const EMPTY_STATES = {
  noAnswers: {
    title: 'No answers yet',
    description: 'Answers will appear here as agents submit them during coordination.',
    hint: 'Press "A" to refresh the answer browser',
  },
  noVotes: {
    title: 'No votes cast yet',
    description: 'Votes are recorded after agents review each other\'s answers.',
    hint: 'Voting begins once all agents have submitted answers',
  },
  noFiles: {
    title: 'No workspace files',
    description: 'Files created by agents will appear here.',
    hint: 'Select an agent above to browse their workspace',
  },
  noWorkspaces: {
    title: 'No workspaces found',
    description: 'The session may still be initializing.',
    hint: 'Workspaces appear once agents start working',
  },
  noTimeline: {
    title: 'No timeline data yet',
    description: 'The timeline will populate as coordination progresses.',
    hint: 'Check back after agents submit answers',
  },
  loading: {
    title: 'Loading...',
    description: 'Please wait while we fetch the data.',
    hint: undefined,
  },
  error: {
    title: 'Something went wrong',
    description: 'We couldn\'t load this content. Please try again.',
    hint: 'If the problem persists, check your connection',
  },
} as const;

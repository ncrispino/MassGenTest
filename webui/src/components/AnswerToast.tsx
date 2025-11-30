/**
 * AnswerToast Component
 *
 * Toast notifications for new answers from agents.
 * Shows agent name, answer preview, with auto-dismiss after 5 seconds.
 * Click to expand or dismiss.
 */

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, X, ChevronRight } from 'lucide-react';
import { useAgentStore, selectAnswers } from '../stores/agentStore';
import type { Answer } from '../types';

interface ToastItem {
  answer: Answer;
  isExpanded: boolean;
  isExiting: boolean;
}

const TOAST_DURATION = 5000; // 5 seconds
const MAX_PREVIEW_LENGTH = 150;

function truncateContent(content: string, maxLength: number): string {
  if (content.length <= maxLength) return content;
  return content.substring(0, maxLength).trim() + '...';
}

export function AnswerToast() {
  const answers = useAgentStore(selectAnswers);
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const [seenAnswerIds, setSeenAnswerIds] = useState<Set<string>>(new Set());

  // Watch for new answers
  useEffect(() => {
    const newAnswers = answers.filter((a) => !seenAnswerIds.has(a.id));

    if (newAnswers.length > 0) {
      // Add new toasts
      setToasts((prev) => [
        ...prev,
        ...newAnswers.map((answer) => ({
          answer,
          isExpanded: false,
          isExiting: false,
        })),
      ]);

      // Mark as seen
      setSeenAnswerIds((prev) => {
        const next = new Set(prev);
        newAnswers.forEach((a) => next.add(a.id));
        return next;
      });
    }
  }, [answers, seenAnswerIds]);

  // Auto-dismiss toasts after duration
  useEffect(() => {
    if (toasts.length === 0) return;

    const timers = toasts.map((toast, index) => {
      if (toast.isExpanded || toast.isExiting) return null;

      return setTimeout(() => {
        dismissToast(toast.answer.id);
      }, TOAST_DURATION + index * 500); // Stagger dismissals
    });

    return () => {
      timers.forEach((timer) => timer && clearTimeout(timer));
    };
  }, [toasts]);

  const dismissToast = useCallback((answerId: string) => {
    setToasts((prev) =>
      prev.map((t) =>
        t.answer.id === answerId ? { ...t, isExiting: true } : t
      )
    );

    // Remove after animation
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.answer.id !== answerId));
    }, 300);
  }, []);

  const toggleExpand = useCallback((answerId: string) => {
    setToasts((prev) =>
      prev.map((t) =>
        t.answer.id === answerId ? { ...t, isExpanded: !t.isExpanded } : t
      )
    );
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-24 right-4 z-50 flex flex-col gap-2 max-w-md">
      <AnimatePresence mode="popLayout">
        {toasts.map((toast) => (
          <motion.div
            key={toast.answer.id}
            initial={{ opacity: 0, x: 100, scale: 0.9 }}
            animate={{
              opacity: toast.isExiting ? 0 : 1,
              x: toast.isExiting ? 100 : 0,
              scale: toast.isExiting ? 0.9 : 1,
            }}
            exit={{ opacity: 0, x: 100, scale: 0.9 }}
            transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            className={`
              bg-gray-800 border border-gray-600 rounded-lg shadow-xl
              overflow-hidden cursor-pointer
              ${toast.isExpanded ? 'max-h-96' : 'max-h-32'}
              transition-all duration-300
            `}
            onClick={() => toggleExpand(toast.answer.id)}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 bg-blue-900/50 border-b border-gray-700">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-blue-400" />
                <span className="font-medium text-blue-200">
                  {toast.answer.agentId}
                </span>
                <span className="text-gray-500 text-sm">
                  Answer #{toast.answer.answerNumber}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <motion.div
                  animate={{ rotate: toast.isExpanded ? 90 : 0 }}
                  className="text-gray-400"
                >
                  <ChevronRight className="w-4 h-4" />
                </motion.div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    dismissToast(toast.answer.id);
                  }}
                  className="p-1 hover:bg-gray-700 rounded transition-colors"
                >
                  <X className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-3">
              <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono leading-relaxed">
                {toast.isExpanded
                  ? toast.answer.content
                  : truncateContent(toast.answer.content, MAX_PREVIEW_LENGTH)}
              </pre>
            </div>

            {/* Footer hint */}
            {!toast.isExpanded && toast.answer.content.length > MAX_PREVIEW_LENGTH && (
              <div className="px-3 pb-2 text-xs text-gray-500">
                Click to expand...
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

export default AnswerToast;

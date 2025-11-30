/**
 * AnswerBrowserModal Component
 *
 * Modal dialog for browsing all answers from agents.
 * Filterable by agent, shows answer timeline with vote counts.
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, FileText, User, Clock, ChevronDown, Trophy } from 'lucide-react';
import { useAgentStore, selectAnswers, selectAgentOrder, selectSelectedAgent } from '../stores/agentStore';
import type { Answer } from '../types';

interface AnswerBrowserModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function formatTimestamp(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

export function AnswerBrowserModal({ isOpen, onClose }: AnswerBrowserModalProps) {
  const answers = useAgentStore(selectAnswers);
  const agentOrder = useAgentStore(selectAgentOrder);
  const selectedAgent = useAgentStore(selectSelectedAgent);

  const [filterAgent, setFilterAgent] = useState<string | 'all'>('all');
  const [expandedAnswerId, setExpandedAnswerId] = useState<string | null>(null);

  // Filter answers based on selected agent
  const filteredAnswers = useMemo(() => {
    let result = [...answers];

    if (filterAgent !== 'all') {
      result = result.filter((a) => a.agentId === filterAgent);
    }

    // Sort by timestamp (most recent first)
    return result.sort((a, b) => b.timestamp - a.timestamp);
  }, [answers, filterAgent]);

  // Group answers by agent for summary stats
  const answersByAgent = useMemo(() => {
    const grouped: Record<string, Answer[]> = {};
    answers.forEach((answer) => {
      if (!grouped[answer.agentId]) {
        grouped[answer.agentId] = [];
      }
      grouped[answer.agentId].push(answer);
    });
    return grouped;
  }, [answers]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', stiffness: 300, damping: 30 }}
            className="fixed inset-4 md:inset-10 lg:inset-20 bg-gray-800 rounded-xl border border-gray-600 shadow-2xl z-50 flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 bg-gray-900/50">
              <div className="flex items-center gap-3">
                <FileText className="w-6 h-6 text-blue-400" />
                <h2 className="text-xl font-semibold text-gray-100">Answer Browser</h2>
                <span className="px-2 py-0.5 bg-blue-900/50 text-blue-300 rounded-full text-sm">
                  {answers.length} answers
                </span>
              </div>
              <button
                onClick={onClose}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>

            {/* Filter Bar */}
            <div className="px-6 py-3 border-b border-gray-700 bg-gray-800/50 flex items-center gap-4">
              <span className="text-sm text-gray-400">Filter by agent:</span>
              <div className="relative">
                <select
                  value={filterAgent}
                  onChange={(e) => setFilterAgent(e.target.value)}
                  className="appearance-none bg-gray-700 border border-gray-600 rounded-lg px-4 py-2 pr-10 text-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Agents</option>
                  {agentOrder.map((agentId) => (
                    <option key={agentId} value={agentId}>
                      {agentId} ({answersByAgent[agentId]?.length || 0} answers)
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
              </div>
            </div>

            {/* Answer List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-4">
              {filteredAnswers.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <FileText className="w-12 h-12 mb-4 opacity-50" />
                  <p>No answers yet</p>
                  <p className="text-sm mt-1">Answers will appear here as agents submit them</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filteredAnswers.map((answer) => {
                    const isExpanded = expandedAnswerId === answer.id;
                    const isWinner = answer.agentId === selectedAgent;

                    return (
                      <motion.div
                        key={answer.id}
                        layout
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className={`
                          bg-gray-700/50 rounded-lg border overflow-hidden cursor-pointer
                          transition-colors hover:bg-gray-700/70
                          ${isWinner ? 'border-yellow-500/50' : 'border-gray-600'}
                        `}
                        onClick={() => setExpandedAnswerId(isExpanded ? null : answer.id)}
                      >
                        {/* Answer Header */}
                        <div className="flex items-center justify-between px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isWinner ? 'bg-yellow-900/50' : 'bg-blue-900/50'}`}>
                              {isWinner ? (
                                <Trophy className="w-4 h-4 text-yellow-400" />
                              ) : (
                                <User className="w-4 h-4 text-blue-400" />
                              )}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-medium text-gray-200">{answer.agentId}</span>
                                <span className="text-gray-500 text-sm">Answer #{answer.answerNumber}</span>
                                {isWinner && (
                                  <span className="px-2 py-0.5 bg-yellow-900/50 text-yellow-300 rounded-full text-xs">
                                    Winner
                                  </span>
                                )}
                              </div>
                              <div className="flex items-center gap-2 text-xs text-gray-500 mt-0.5">
                                <Clock className="w-3 h-3" />
                                <span>{formatTimestamp(answer.timestamp)}</span>
                              </div>
                            </div>
                          </div>
                          <motion.div
                            animate={{ rotate: isExpanded ? 180 : 0 }}
                            className="text-gray-400"
                          >
                            <ChevronDown className="w-5 h-5" />
                          </motion.div>
                        </div>

                        {/* Answer Content (Expandable) */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2 }}
                              className="border-t border-gray-600"
                            >
                              <div className="p-4 bg-gray-800/50">
                                <pre className="whitespace-pre-wrap text-sm text-gray-300 font-mono leading-relaxed max-h-96 overflow-y-auto custom-scrollbar">
                                  {answer.content}
                                </pre>
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Footer with stats */}
            <div className="px-6 py-3 border-t border-gray-700 bg-gray-900/50 flex items-center justify-between text-sm">
              <div className="flex items-center gap-4 text-gray-400">
                <span>Total: {answers.length} answers</span>
                <span>Agents: {Object.keys(answersByAgent).length}</span>
              </div>
              {selectedAgent && (
                <div className="flex items-center gap-2 text-yellow-400">
                  <Trophy className="w-4 h-4" />
                  <span>Winner: {selectedAgent}</span>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

export default AnswerBrowserModal;

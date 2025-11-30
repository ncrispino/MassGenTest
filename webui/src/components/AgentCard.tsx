/**
 * AgentCard Component
 *
 * Displays individual agent panel with streaming content,
 * status badge, and tool activity.
 */

import { motion } from 'framer-motion';
import { Bot, CheckCircle, Clock, AlertCircle, Vote, Loader2 } from 'lucide-react';
import { useEffect, useRef } from 'react';
import type { AgentState, AgentStatus } from '../types';

interface AgentCardProps {
  agent: AgentState;
  isWinner?: boolean;
  isVisible?: boolean;
}

const statusConfig: Record<AgentStatus, { color: string; icon: typeof Bot; label: string }> = {
  waiting: { color: 'bg-gray-500', icon: Clock, label: 'Waiting' },
  working: { color: 'bg-blue-500', icon: Loader2, label: 'Working' },
  voting: { color: 'bg-amber-500', icon: Vote, label: 'Voting' },
  completed: { color: 'bg-green-500', icon: CheckCircle, label: 'Completed' },
  failed: { color: 'bg-red-500', icon: AlertCircle, label: 'Failed' },
};

export function AgentCard({ agent, isWinner = false, isVisible = true }: AgentCardProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const { color, icon: StatusIcon, label } = statusConfig[agent.status];

  // Auto-scroll to bottom on new content
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [agent.currentContent]);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{
        opacity: isVisible ? 1 : 0.3,
        scale: isWinner ? 1.02 : 1,
      }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 30,
      }}
      className={`
        flex flex-col h-full w-full
        bg-gray-800 rounded-lg border-2 overflow-hidden
        ${isWinner ? 'border-yellow-500 shadow-lg shadow-yellow-500/20 animate-glow' : 'border-gray-700'}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-gray-900/50 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-gray-400" />
          <span className="font-medium text-gray-200">{agent.id}</span>
          {isWinner && (
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="text-yellow-500 text-lg"
            >
              👑
            </motion.span>
          )}
        </div>

        {/* Status Badge */}
        <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full ${color}`}>
          <StatusIcon
            className={`w-3.5 h-3.5 text-white ${agent.status === 'working' ? 'animate-spin' : ''}`}
          />
          <span className="text-xs font-medium text-white">{label}</span>
        </div>
      </div>

      {/* Answer Count & Vote Target */}
      <div className="flex items-center gap-4 px-3 py-2 bg-gray-800/50 text-sm">
        <span className="text-gray-400">
          Answers: <span className="text-gray-200 font-medium">{agent.answerCount}</span>
        </span>
        {agent.voteTarget && (
          <span className="text-gray-400">
            Voted for:{' '}
            <span className="text-amber-400 font-medium">{agent.voteTarget}</span>
          </span>
        )}
      </div>

      {/* Content Area */}
      <div
        ref={contentRef}
        className="flex-1 p-3 overflow-y-auto custom-scrollbar text-sm font-mono"
      >
        <pre className="whitespace-pre-wrap text-gray-300 leading-relaxed">
          {agent.currentContent || (
            <span className="text-gray-500 italic">Waiting for agent to start...</span>
          )}
        </pre>
      </div>

      {/* Tool Activity */}
      {agent.toolCalls.length > 0 && (
        <div className="border-t border-gray-700 p-2 bg-gray-900/30">
          <div className="text-xs text-gray-500 mb-1">Recent Tools:</div>
          <div className="flex flex-wrap gap-1">
            {agent.toolCalls.slice(-3).map((tool, idx) => (
              <span
                key={idx}
                className={`px-2 py-0.5 rounded text-xs ${
                  tool.success === false
                    ? 'bg-red-900/50 text-red-300'
                    : tool.result
                    ? 'bg-green-900/50 text-green-300'
                    : 'bg-blue-900/50 text-blue-300'
                }`}
              >
                {tool.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}

export default AgentCard;

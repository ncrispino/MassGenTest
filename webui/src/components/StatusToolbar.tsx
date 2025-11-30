/**
 * StatusToolbar Component
 *
 * Horizontal overview of all agents' status.
 * Shows status badges and allows quick navigation.
 */

import { motion } from 'framer-motion';
import { Bot, CheckCircle, Clock, AlertCircle, Vote, Loader2 } from 'lucide-react';
import { useAgentStore, selectAgents, selectAgentOrder, selectSelectedAgent } from '../stores/agentStore';
import type { AgentStatus } from '../types';

const statusIcons: Record<AgentStatus, typeof Bot> = {
  waiting: Clock,
  working: Loader2,
  voting: Vote,
  completed: CheckCircle,
  failed: AlertCircle,
};

const statusColors: Record<AgentStatus, string> = {
  waiting: 'bg-gray-600 text-gray-300',
  working: 'bg-blue-600 text-blue-100',
  voting: 'bg-amber-600 text-amber-100',
  completed: 'bg-green-600 text-green-100',
  failed: 'bg-red-600 text-red-100',
};

interface StatusToolbarProps {
  onAgentClick?: (agentId: string) => void;
}

export function StatusToolbar({ onAgentClick }: StatusToolbarProps) {
  const agents = useAgentStore(selectAgents);
  const agentOrder = useAgentStore(selectAgentOrder);
  const selectedAgent = useAgentStore(selectSelectedAgent);

  // Count agents by status
  const statusCounts = agentOrder.reduce(
    (acc, id) => {
      const status = agents[id]?.status || 'waiting';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    },
    {} as Record<AgentStatus, number>
  );

  return (
    <div className="bg-gray-800/50 border-b border-gray-700 px-4 py-3">
      <div className="flex items-center justify-between">
        {/* Agent Badges */}
        <div className="flex items-center gap-2 flex-wrap">
          {agentOrder.map((agentId) => {
            const agent = agents[agentId];
            if (!agent) return null;

            const Icon = statusIcons[agent.status];
            const colorClass = statusColors[agent.status];
            const isWinner = selectedAgent === agentId;

            return (
              <motion.button
                key={agentId}
                onClick={() => onAgentClick?.(agentId)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`
                  flex items-center gap-2 px-3 py-1.5 rounded-full
                  transition-all duration-200 cursor-pointer
                  ${colorClass}
                  ${isWinner ? 'ring-2 ring-yellow-500 ring-offset-2 ring-offset-gray-900' : ''}
                `}
              >
                <Icon
                  className={`w-4 h-4 ${agent.status === 'working' ? 'animate-spin' : ''}`}
                />
                <span className="text-sm font-medium">{agentId}</span>
                {agent.answerCount > 0 && (
                  <span className="text-xs bg-black/20 px-1.5 rounded-full">
                    #{agent.answerCount}
                  </span>
                )}
                {isWinner && <span className="text-sm">👑</span>}
              </motion.button>
            );
          })}
        </div>

        {/* Summary Stats */}
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <div className="flex items-center gap-1">
            <Loader2 className="w-4 h-4 text-blue-500" />
            <span>Working: {statusCounts.working || 0}</span>
          </div>
          <div className="flex items-center gap-1">
            <Vote className="w-4 h-4 text-amber-500" />
            <span>Voting: {statusCounts.voting || 0}</span>
          </div>
          <div className="flex items-center gap-1">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <span>Done: {statusCounts.completed || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default StatusToolbar;

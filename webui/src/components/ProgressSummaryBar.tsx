/**
 * ProgressSummaryBar Component
 *
 * Displays a quick summary of the coordination session at the top of the Browser modal.
 * Shows agent count, answer count, vote progress, and winner information.
 */

import { Users, FileText, Vote, Trophy, Loader2 } from 'lucide-react';
import { getAgentColor } from '../utils/agentColors';

interface ProgressSummaryBarProps {
  agentCount: number;
  answerCount: number;
  voteCount: number;
  totalVotesExpected: number;
  winnerId?: string;
  winnerVotes?: number;
  isComplete: boolean;
  isVoting: boolean;
  agentOrder: string[];
}

export function ProgressSummaryBar({
  agentCount,
  answerCount,
  voteCount,
  totalVotesExpected,
  winnerId,
  winnerVotes,
  isComplete,
  isVoting,
  agentOrder,
}: ProgressSummaryBarProps) {
  // Get winner's display name and color
  const winnerIndex = winnerId ? agentOrder.indexOf(winnerId) : -1;
  const winnerDisplayName = winnerIndex !== -1 ? `Agent ${winnerIndex + 1}` : winnerId;
  const winnerColor = winnerId ? getAgentColor(winnerId, agentOrder) : null;

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-gray-900/40 border-b border-gray-700/50 text-sm">
      {/* Agents */}
      <div className="flex items-center gap-1.5 text-gray-400">
        <Users className="w-4 h-4" />
        <span>
          <span className="text-gray-200 font-medium">{agentCount}</span> agent{agentCount !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="w-px h-4 bg-gray-700" />

      {/* Answers */}
      <div className="flex items-center gap-1.5 text-gray-400">
        <FileText className="w-4 h-4" />
        <span>
          <span className="text-gray-200 font-medium">{answerCount}</span> answer{answerCount !== 1 ? 's' : ''}
        </span>
      </div>

      <div className="w-px h-4 bg-gray-700" />

      {/* Votes / Winner */}
      {isComplete && winnerId ? (
        // Show winner
        <div className="flex items-center gap-1.5">
          <Trophy className="w-4 h-4 text-yellow-500" />
          <span className="text-gray-400">
            <span
              className={`font-medium ${winnerColor?.text || 'text-gray-200'}`}
            >
              {winnerDisplayName}
            </span>
            {' '}won
            {winnerVotes !== undefined && (
              <span className="text-gray-500">
                {' '}({winnerVotes} vote{winnerVotes !== 1 ? 's' : ''})
              </span>
            )}
          </span>
        </div>
      ) : isVoting ? (
        // Show voting progress
        <div className="flex items-center gap-1.5 text-gray-400">
          <Vote className="w-4 h-4 text-amber-400" />
          <span>
            <span className="text-amber-400 font-medium">{voteCount}</span>
            <span className="text-gray-500">/{totalVotesExpected}</span>
            {' '}votes cast
          </span>
        </div>
      ) : (
        // Show working status
        <div className="flex items-center gap-1.5 text-gray-400">
          <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          <span className="text-gray-400">Coordinating...</span>
        </div>
      )}
    </div>
  );
}

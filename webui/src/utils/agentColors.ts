/**
 * Agent Colors Utility
 *
 * Provides consistent identity colors for agents throughout the UI.
 * Each agent gets a unique color based on their order in the session.
 */

export interface AgentColor {
  /** Background color class (e.g., 'bg-blue-600') */
  bg: string;
  /** Lighter background for hover/subtle states */
  bgLight: string;
  /** Text color class (e.g., 'text-blue-400') */
  text: string;
  /** Border color class */
  border: string;
  /** Focus ring color class */
  ring: string;
  /** Raw hex value for SVG fills */
  hex: string;
  /** Lighter hex for gradients/secondary use */
  hexLight: string;
}

/**
 * Predefined color palette for up to 9 agents.
 * Colors are chosen to be visually distinct and accessible.
 */
const AGENT_COLORS: AgentColor[] = [
  {
    bg: 'bg-blue-600',
    bgLight: 'bg-blue-600/20',
    text: 'text-blue-400',
    border: 'border-blue-500',
    ring: 'ring-blue-500',
    hex: '#3B82F6',
    hexLight: '#60A5FA',
  },
  {
    bg: 'bg-emerald-600',
    bgLight: 'bg-emerald-600/20',
    text: 'text-emerald-400',
    border: 'border-emerald-500',
    ring: 'ring-emerald-500',
    hex: '#10B981',
    hexLight: '#34D399',
  },
  {
    bg: 'bg-violet-600',
    bgLight: 'bg-violet-600/20',
    text: 'text-violet-400',
    border: 'border-violet-500',
    ring: 'ring-violet-500',
    hex: '#8B5CF6',
    hexLight: '#A78BFA',
  },
  {
    bg: 'bg-orange-600',
    bgLight: 'bg-orange-600/20',
    text: 'text-orange-400',
    border: 'border-orange-500',
    ring: 'ring-orange-500',
    hex: '#F97316',
    hexLight: '#FB923C',
  },
  {
    bg: 'bg-pink-600',
    bgLight: 'bg-pink-600/20',
    text: 'text-pink-400',
    border: 'border-pink-500',
    ring: 'ring-pink-500',
    hex: '#EC4899',
    hexLight: '#F472B6',
  },
  {
    bg: 'bg-cyan-600',
    bgLight: 'bg-cyan-600/20',
    text: 'text-cyan-400',
    border: 'border-cyan-500',
    ring: 'ring-cyan-500',
    hex: '#06B6D4',
    hexLight: '#22D3EE',
  },
  {
    bg: 'bg-amber-600',
    bgLight: 'bg-amber-600/20',
    text: 'text-amber-400',
    border: 'border-amber-500',
    ring: 'ring-amber-500',
    hex: '#F59E0B',
    hexLight: '#FBBF24',
  },
  {
    bg: 'bg-rose-600',
    bgLight: 'bg-rose-600/20',
    text: 'text-rose-400',
    border: 'border-rose-500',
    ring: 'ring-rose-500',
    hex: '#F43F5E',
    hexLight: '#FB7185',
  },
  {
    bg: 'bg-indigo-600',
    bgLight: 'bg-indigo-600/20',
    text: 'text-indigo-400',
    border: 'border-indigo-500',
    ring: 'ring-indigo-500',
    hex: '#6366F1',
    hexLight: '#818CF8',
  },
];

/**
 * Get the color configuration for an agent based on their position in the agent order.
 *
 * @param agentId - The agent's ID
 * @param agentOrder - Array of agent IDs in order
 * @returns AgentColor configuration, cycling through palette if more than 9 agents
 */
export function getAgentColor(agentId: string, agentOrder: string[]): AgentColor {
  const index = agentOrder.indexOf(agentId);
  if (index === -1) {
    // Unknown agent, return first color as fallback
    return AGENT_COLORS[0];
  }
  return AGENT_COLORS[index % AGENT_COLORS.length];
}

/**
 * Get color by index directly (useful when you have the index already)
 */
export function getAgentColorByIndex(index: number): AgentColor {
  return AGENT_COLORS[index % AGENT_COLORS.length];
}

/**
 * Get the total number of unique colors available
 */
export function getColorCount(): number {
  return AGENT_COLORS.length;
}

/**
 * Get all agent colors (useful for legends/documentation)
 */
export function getAllAgentColors(): AgentColor[] {
  return [...AGENT_COLORS];
}

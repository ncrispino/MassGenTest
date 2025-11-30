/**
 * ConvergenceAnimation Component
 *
 * Dramatic multi-stage animation when consensus is reached.
 * Agents visually converge toward the winner.
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Sparkles } from 'lucide-react';
import { useAgentStore, selectSelectedAgent, selectFinalAnswer, selectIsComplete } from '../stores/agentStore';

export function ConvergenceAnimation() {
  const selectedAgent = useAgentStore(selectSelectedAgent);
  const finalAnswer = useAgentStore(selectFinalAnswer);
  const isComplete = useAgentStore(selectIsComplete);

  const showAnimation = isComplete && selectedAgent;

  return (
    <AnimatePresence>
      {showAnimation && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
        >
          {/* Background particles */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {Array.from({ length: 20 }).map((_, i) => (
              <motion.div
                key={i}
                className="absolute w-2 h-2 bg-yellow-500/60 rounded-full"
                initial={{
                  x: Math.random() * window.innerWidth,
                  y: Math.random() * window.innerHeight,
                  scale: 0,
                }}
                animate={{
                  x: window.innerWidth / 2,
                  y: window.innerHeight / 2,
                  scale: [0, 1, 0],
                }}
                transition={{
                  duration: 2,
                  delay: i * 0.1,
                  ease: 'easeInOut',
                }}
              />
            ))}
          </div>

          {/* Winner Card */}
          <motion.div
            initial={{ scale: 0, rotate: -10 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{
              type: 'spring',
              stiffness: 200,
              damping: 20,
              delay: 0.5,
            }}
            className="relative max-w-2xl mx-4"
          >
            {/* Glow effect */}
            <motion.div
              className="absolute inset-0 bg-yellow-500/20 rounded-2xl blur-3xl"
              animate={{
                scale: [1, 1.1, 1],
                opacity: [0.5, 0.8, 0.5],
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                ease: 'easeInOut',
              }}
            />

            {/* Main card */}
            <div className="relative bg-gray-900 border-2 border-yellow-500 rounded-2xl p-6 shadow-2xl">
              {/* Header */}
              <div className="flex items-center justify-center gap-3 mb-4">
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 0.5, delay: 1, repeat: 2 }}
                >
                  <Trophy className="w-10 h-10 text-yellow-500" />
                </motion.div>
                <div className="text-center">
                  <motion.h2
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                    className="text-2xl font-bold text-yellow-400"
                  >
                    Consensus Reached!
                  </motion.h2>
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 1 }}
                    className="text-gray-400"
                  >
                    Winner: <span className="text-yellow-300 font-medium">{selectedAgent}</span>
                  </motion.p>
                </div>
                <motion.div
                  animate={{ rotate: [0, -10, 10, 0] }}
                  transition={{ duration: 0.5, delay: 1.2, repeat: 2 }}
                >
                  <Sparkles className="w-10 h-10 text-yellow-500" />
                </motion.div>
              </div>

              {/* Final Answer */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1.2 }}
                className="bg-gray-800/50 rounded-lg p-4 border border-gray-700"
              >
                <h3 className="text-sm font-medium text-gray-400 mb-2">Final Coordinated Answer</h3>
                <div className="max-h-[300px] overflow-y-auto custom-scrollbar">
                  <pre className="text-gray-200 whitespace-pre-wrap text-sm leading-relaxed font-mono">
                    {finalAnswer || 'Loading...'}
                  </pre>
                </div>
              </motion.div>

              {/* Close instruction */}
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 2 }}
                className="text-center text-gray-500 text-sm mt-4"
              >
                Click anywhere to close
              </motion.p>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default ConvergenceAnimation;

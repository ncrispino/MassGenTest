/**
 * MassGen Web UI - Main Application
 *
 * Real-time visualization of multi-agent coordination.
 */

import { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Send, Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { useWebSocket, ConnectionStatus } from './hooks/useWebSocket';
import { useAgentStore, selectQuestion, selectIsComplete, selectAnswers } from './stores/agentStore';
import { AgentCarousel } from './components/AgentCarousel';
import { StatusToolbar } from './components/StatusToolbar';
import { VoteVisualization } from './components/VoteVisualization';
import { FileWorkspaceBrowser } from './components/FileWorkspaceBrowser';
import { ConvergenceAnimation } from './components/ConvergenceAnimation';
import { HeaderControls } from './components/HeaderControls';
import { EventBar } from './components/EventBar';
import { AnswerToast } from './components/AnswerToast';
import { AnswerBrowserModal } from './components/AnswerBrowserModal';

function ConnectionIndicator({ status }: { status: ConnectionStatus }) {
  const config: Record<ConnectionStatus, { icon: typeof Wifi; color: string; text: string }> = {
    connecting: { icon: Wifi, color: 'text-amber-500', text: 'Connecting...' },
    connected: { icon: Wifi, color: 'text-green-500', text: 'Connected' },
    disconnected: { icon: WifiOff, color: 'text-red-500', text: 'Disconnected' },
    error: { icon: AlertCircle, color: 'text-red-500', text: 'Error' },
  };

  const { icon: Icon, color, text } = config[status];

  return (
    <div className={`flex items-center gap-2 text-sm ${color}`}>
      <Icon className="w-4 h-4" />
      <span>{text}</span>
    </div>
  );
}

export function App() {
  // Session management
  const [sessionId, setSessionId] = useState<string>(() => crypto.randomUUID());
  const [selectedConfig, setSelectedConfig] = useState<string | null>(null);
  const [inputQuestion, setInputQuestion] = useState('');

  const question = useAgentStore(selectQuestion);
  const isComplete = useAgentStore(selectIsComplete);
  const answers = useAgentStore(selectAnswers);
  const reset = useAgentStore((s) => s.reset);

  // Answer browser modal state
  const [isAnswerBrowserOpen, setIsAnswerBrowserOpen] = useState(false);

  const { status, startCoordination, error } = useWebSocket({
    sessionId,
    autoConnect: true,
  });

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (inputQuestion.trim() && status === 'connected') {
        // Pass config path when starting coordination
        startCoordination(inputQuestion.trim(), selectedConfig || undefined);
        setInputQuestion('');
      }
    },
    [inputQuestion, status, startCoordination, selectedConfig]
  );

  const handleNewSession = useCallback(() => {
    reset();
    setSessionId(crypto.randomUUID());
  }, [reset]);

  const handleConfigChange = useCallback((configPath: string) => {
    setSelectedConfig(configPath);
  }, []);

  const handleSessionChange = useCallback((newSessionId: string) => {
    if (newSessionId !== sessionId) {
      reset();
      setSessionId(newSessionId);
    }
  }, [sessionId, reset]);

  // Get config name for display
  const configName = selectedConfig
    ? selectedConfig.split('/').pop()?.replace('.yaml', '') || 'Selected'
    : 'No config';

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex flex-col">
      {/* Header */}
      <header className="bg-gray-800/50 border-b border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              MassGen
            </h1>
            <span className="text-gray-500 text-sm">Multi-Agent Coordination</span>
            <ConnectionIndicator status={status} />
          </div>
          <HeaderControls
            currentSessionId={sessionId}
            selectedConfig={selectedConfig}
            onConfigChange={handleConfigChange}
            onSessionChange={handleSessionChange}
            onNewSession={handleNewSession}
            onOpenAnswerBrowser={() => setIsAnswerBrowserOpen(true)}
            answerCount={answers.length}
          />
        </div>
      </header>

      {/* Question Display */}
      {question && (
        <div className="bg-gray-800/30 border-b border-gray-700 px-6 py-3">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div>
              <span className="text-gray-500 text-sm">Question: </span>
              <span className="text-gray-200">{question}</span>
            </div>
            <div className="text-xs text-gray-500">
              Config: <span className="text-gray-400">{configName}</span>
            </div>
          </div>
        </div>
      )}

      {/* Status Toolbar */}
      <StatusToolbar />

      {/* Main Content */}
      <main className="flex-1 p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          {/* Error Display */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-900/30 border border-red-700 rounded-lg p-4 flex items-center gap-3"
            >
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-200">{error}</span>
            </motion.div>
          )}

          {/* No Config Warning */}
          {!selectedConfig && !question && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-amber-900/30 border border-amber-700 rounded-lg p-4 flex items-center gap-3"
            >
              <AlertCircle className="w-5 h-5 text-amber-500" />
              <span className="text-amber-200">
                Please select a configuration from the dropdown above before starting.
              </span>
            </motion.div>
          )}

          {/* Agent Carousel */}
          <section>
            <AgentCarousel />
          </section>

          {/* Bottom Panel: Votes + Files (2 columns) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <VoteVisualization />
            <FileWorkspaceBrowser />
          </div>
        </div>
      </main>

      {/* Event Bar - Full Width */}
      <EventBar />

      {/* Input Form */}
      <footer className="bg-gray-800/50 border-t border-gray-700 px-6 py-4">
        <div className="max-w-7xl mx-auto">
          {isComplete ? (
            <div className="flex items-center justify-center gap-4">
              <span className="text-green-400">Coordination Complete!</span>
              <button
                onClick={handleNewSession}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
              >
                Start New Session
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="flex gap-4">
              <input
                type="text"
                value={inputQuestion}
                onChange={(e) => setInputQuestion(e.target.value)}
                placeholder={selectedConfig
                  ? "Enter your question for multi-agent coordination..."
                  : "Select a config first..."
                }
                disabled={status !== 'connected' || !!question || !selectedConfig}
                className="flex-1 bg-gray-700 border border-gray-600 rounded-lg px-4 py-3
                         text-gray-100 placeholder-gray-500
                         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                         disabled:opacity-50 disabled:cursor-not-allowed"
              />
              <button
                type="submit"
                disabled={!inputQuestion.trim() || status !== 'connected' || !!question || !selectedConfig}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600
                         disabled:cursor-not-allowed rounded-lg transition-colors
                         flex items-center gap-2"
              >
                <Send className="w-5 h-5" />
                <span>Start</span>
              </button>
            </form>
          )}
        </div>
      </footer>

      {/* Convergence Animation Overlay */}
      <ConvergenceAnimation />

      {/* Answer Toast Notifications */}
      <AnswerToast />

      {/* Answer Browser Modal */}
      <AnswerBrowserModal
        isOpen={isAnswerBrowserOpen}
        onClose={() => setIsAnswerBrowserOpen(false)}
      />
    </div>
  );
}

export default App;

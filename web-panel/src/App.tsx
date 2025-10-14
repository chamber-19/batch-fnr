import React, { useState } from 'react';
import { Moon, Sun, Settings, FileText, Search, Layers } from 'lucide-react';
import BatchFindReplacePanel from './components/BatchFindReplacePanel';
import TextUnifierPanel from './components/TextUnifierPanel';
import UnifiedDashboard from './components/UnifiedDashboard';

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [activePanel, setActivePanel] = useState<'dashboard' | 'find-replace' | 'text-unifier'>('dashboard');

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const renderActivePanel = () => {
    switch (activePanel) {
      case 'find-replace':
        return <BatchFindReplacePanel onBack={() => setActivePanel('dashboard')} />;
      case 'text-unifier':
        return <TextUnifierPanel onBack={() => setActivePanel('dashboard')} />;
      default:
        return <UnifiedDashboard onPanelSelect={setActivePanel} />;
    }
  };

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className="min-h-screen bg-gradient-to-br from-slate-100 via-blue-50 to-slate-200 dark:from-black dark:via-gray-950 dark:to-zinc-950 transition-all duration-300">
        {/* Header */}
        <header className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border-b border-slate-200 dark:border-slate-700 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                      AutoCAD Text Tools
                    </h1>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Batch Find & Replace • Text Unifier
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  v1.5.0 (Development)
                </span>
                <button
                  onClick={toggleDarkMode}
                  className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
                >
                  {darkMode ? (
                    <Sun className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                  ) : (
                    <Moon className="w-5 h-5 text-slate-600 dark:text-slate-400" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {renderActivePanel()}
        </main>

        {/* Footer */}
        <footer className="bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-t border-slate-200 dark:border-slate-700 mt-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex justify-between items-center">
              <div className="text-sm text-slate-600 dark:text-slate-400">
                © 2024 Root3Power LLC • Hyphae Engineering
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  AutoCAD Text Processing Suite
                </span>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}

export default App;

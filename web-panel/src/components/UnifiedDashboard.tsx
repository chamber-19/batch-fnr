import React from 'react';
import { Search, Layers, Play, Settings, FileText, Zap, Target, Wrench } from 'lucide-react';

interface UnifiedDashboardProps {
  onPanelSelect: (panel: 'find-replace' | 'text-unifier') => void;
}

const UnifiedDashboard: React.FC<UnifiedDashboardProps> = ({ onPanelSelect }) => {
  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div className="text-center">
        <h2 className="text-3xl font-bold text-slate-900 dark:text-white mb-4">
          AutoCAD Text Tools Suite
        </h2>
        <p className="text-lg text-slate-600 dark:text-slate-400 max-w-3xl mx-auto">
          Powerful tools for batch text processing in AutoCAD drawings. 
          Find and replace text across multiple drawings, unify text formatting, and manage title blocks efficiently.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="panel-card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Active Tools</p>
              <p className="text-2xl font-bold text-slate-900 dark:text-white">2</p>
            </div>
          </div>
        </div>

        <div className="panel-card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
              <Zap className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Status</p>
              <p className="text-lg font-semibold text-green-600 dark:text-green-400">Ready</p>
            </div>
          </div>
        </div>

        <div className="panel-card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center">
              <Target className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Version</p>
              <p className="text-lg font-semibold text-slate-900 dark:text-white">1.5.0</p>
            </div>
          </div>
        </div>

        <div className="panel-card">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-orange-100 dark:bg-orange-900/30 rounded-lg flex items-center justify-center">
              <Wrench className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Mode</p>
              <p className="text-lg font-semibold text-orange-600 dark:text-orange-400">Dev</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Tool Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Batch Find & Replace Panel */}
        <div className="panel-card group hover:shadow-xl transition-all duration-300">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
              <Search className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                Batch Find & Replace
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                Search and replace text across multiple AutoCAD drawings. 
                Supports title blocks, annotations, and bulk text operations.
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs rounded-full">
                  Batch Processing
                </span>
                <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 text-xs rounded-full">
                  Title Blocks
                </span>
                <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded-full">
                  Regex Support
                </span>
              </div>
              <button
                onClick={() => onPanelSelect('find-replace')}
                className="panel-button w-full"
              >
                <Play className="w-4 h-4 mr-2" />
                Open Find & Replace
              </button>
            </div>
          </div>
        </div>

        {/* Text Unifier Panel */}
        <div className="panel-card group hover:shadow-xl transition-all duration-300">
          <div className="flex items-start space-x-4">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center group-hover:scale-110 transition-transform">
              <Layers className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                Text Unifier & Scaling
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                Standardize text formatting, heights, and styles across drawings. 
                Unify text appearance and apply consistent scaling.
              </p>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded-full">
                  Text Scaling
                </span>
                <span className="px-2 py-1 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-xs rounded-full">
                  Style Unification
                </span>
                <span className="px-2 py-1 bg-teal-100 dark:bg-teal-900/30 text-teal-700 dark:text-teal-300 text-xs rounded-full">
                  Geometry Tools
                </span>
              </div>
              <button
                onClick={() => onPanelSelect('text-unifier')}
                className="panel-button w-full"
              >
                <Layers className="w-4 h-4 mr-2" />
                Open Text Unifier
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="panel-card">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="panel-button">
            <Play className="w-4 h-4 mr-2" />
            Launch Desktop App
          </button>
          <button className="panel-button">
            <Settings className="w-4 h-4 mr-2" />
            Configuration
          </button>
          <button className="panel-button">
            <FileText className="w-4 h-4 mr-2" />
            View Documentation
          </button>
        </div>
      </div>
    </div>
  );
};

export default UnifiedDashboard;

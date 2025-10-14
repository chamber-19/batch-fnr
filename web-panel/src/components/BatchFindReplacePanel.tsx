import React, { useState } from 'react';
import { ArrowLeft, Search, FileText, Play, Settings, Upload, Download } from 'lucide-react';

interface BatchFindReplacePanelProps {
  onBack: () => void;
}

const BatchFindReplacePanel: React.FC<BatchFindReplacePanelProps> = ({ onBack }) => {
  const [findText, setFindText] = useState('');
  const [replaceText, setReplaceText] = useState('');
  const [useRegex, setUseRegex] = useState(false);
  const [caseSensitive, setCaseSensitive] = useState(false);
  const [includeBlocks, setIncludeBlocks] = useState(true);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onBack}
          className="p-2 rounded-lg bg-slate-100 dark:bg-slate-700 hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-slate-600 dark:text-slate-400" />
        </button>
        <div>
          <h2 className="text-2xl font-bold text-slate-900 dark:text-white">
            Batch Find & Replace
          </h2>
          <p className="text-slate-600 dark:text-slate-400">
            Search and replace text across multiple AutoCAD drawings
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Find & Replace Form */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Find & Replace Settings
            </h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Find Text
                </label>
                <input
                  type="text"
                  value={findText}
                  onChange={(e) => setFindText(e.target.value)}
                  className="panel-input"
                  placeholder="Enter text to find..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Replace With
                </label>
                <input
                  type="text"
                  value={replaceText}
                  onChange={(e) => setReplaceText(e.target.value)}
                  className="panel-input"
                  placeholder="Enter replacement text..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={useRegex}
                    onChange={(e) => setUseRegex(e.target.checked)}
                    className="rounded border-slate-300 dark:border-slate-600"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">Use Regex</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={caseSensitive}
                    onChange={(e) => setCaseSensitive(e.target.checked)}
                    className="rounded border-slate-300 dark:border-slate-600"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">Case Sensitive</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={includeBlocks}
                    onChange={(e) => setIncludeBlocks(e.target.checked)}
                    className="rounded border-slate-300 dark:border-slate-600"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">Include Blocks</span>
                </label>
              </div>
            </div>
          </div>

          {/* File Selection */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Drawing Files
            </h3>
            
            <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-8 text-center">
              <Upload className="w-12 h-12 text-slate-400 mx-auto mb-4" />
              <p className="text-slate-600 dark:text-slate-400 mb-2">
                Drop AutoCAD files here or click to browse
              </p>
              <button className="panel-button">
                <Upload className="w-4 h-4 mr-2" />
                Select Files
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-4">
            <button className="panel-button flex-1 bg-blue-600 hover:bg-blue-700 text-white">
              <Search className="w-4 h-4 mr-2" />
              Preview Changes
            </button>
            <button className="panel-button flex-1 bg-green-600 hover:bg-green-700 text-white">
              <Play className="w-4 h-4 mr-2" />
              Execute Replace
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Status */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Status
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Files Selected</span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Matches Found</span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">-</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Status</span>
                <span className="text-sm font-medium text-green-600 dark:text-green-400">Ready</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Quick Actions
            </h3>
            <div className="space-y-2">
              <button className="panel-button w-full">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </button>
              <button className="panel-button w-full">
                <FileText className="w-4 h-4 mr-2" />
                Load Template
              </button>
              <button className="panel-button w-full">
                <Download className="w-4 h-4 mr-2" />
                Export Results
              </button>
            </div>
          </div>

          {/* Recent Operations */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Recent Operations
            </h3>
            <div className="space-y-2 text-sm">
              <div className="p-2 bg-slate-50 dark:bg-slate-700 rounded">
                <p className="font-medium text-slate-900 dark:text-white">Title Block Update</p>
                <p className="text-slate-600 dark:text-slate-400">2 hours ago</p>
              </div>
              <div className="p-2 bg-slate-50 dark:bg-slate-700 rounded">
                <p className="font-medium text-slate-900 dark:text-white">Dimension Text Fix</p>
                <p className="text-slate-600 dark:text-slate-400">Yesterday</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchFindReplacePanel;

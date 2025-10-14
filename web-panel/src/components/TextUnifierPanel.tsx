import React, { useState } from 'react';
import { ArrowLeft, Layers, Play, Settings, Upload, Target, Ruler, Type } from 'lucide-react';

interface TextUnifierPanelProps {
  onBack: () => void;
}

const TextUnifierPanel: React.FC<TextUnifierPanelProps> = ({ onBack }) => {
  const [targetHeight, setTargetHeight] = useState('3.0');
  const [targetStyle, setTargetStyle] = useState('Standard');
  const [scaleMode, setScaleMode] = useState('uniform');
  const [preserveFormatting, setPreserveFormatting] = useState(true);

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
            Text Unifier & Scaling
          </h2>
          <p className="text-slate-600 dark:text-slate-400">
            Standardize text formatting and scaling across drawings
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Text Settings */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Text Unification Settings
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Target Text Height
                </label>
                <input
                  type="number"
                  value={targetHeight}
                  onChange={(e) => setTargetHeight(e.target.value)}
                  className="panel-input"
                  placeholder="3.0"
                  step="0.1"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Target Text Style
                </label>
                <select
                  value={targetStyle}
                  onChange={(e) => setTargetStyle(e.target.value)}
                  className="panel-input"
                >
                  <option value="Standard">Standard</option>
                  <option value="Arial">Arial</option>
                  <option value="Times">Times New Roman</option>
                  <option value="Calibri">Calibri</option>
                </select>
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                Scaling Mode
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="scaleMode"
                    value="uniform"
                    checked={scaleMode === 'uniform'}
                    onChange={(e) => setScaleMode(e.target.value)}
                    className="text-blue-600"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">Uniform</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="scaleMode"
                    value="proportional"
                    checked={scaleMode === 'proportional'}
                    onChange={(e) => setScaleMode(e.target.value)}
                    className="text-blue-600"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">Proportional</span>
                </label>

                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    name="scaleMode"
                    value="selective"
                    checked={scaleMode === 'selective'}
                    onChange={(e) => setScaleMode(e.target.value)}
                    className="text-blue-600"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-300">Selective</span>
                </label>
              </div>
            </div>

            <div className="mt-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={preserveFormatting}
                  onChange={(e) => setPreserveFormatting(e.target.checked)}
                  className="rounded border-slate-300 dark:border-slate-600"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">
                  Preserve Special Formatting
                </span>
              </label>
            </div>
          </div>

          {/* Geometry Tools */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Geometry Operations
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button className="panel-button">
                <Target className="w-4 h-4 mr-2" />
                Align Text Objects
              </button>
              <button className="panel-button">
                <Ruler className="w-4 h-4 mr-2" />
                Distribute Spacing
              </button>
              <button className="panel-button">
                <Type className="w-4 h-4 mr-2" />
                Normalize Rotation
              </button>
              <button className="panel-button">
                <Layers className="w-4 h-4 mr-2" />
                Layer Cleanup
              </button>
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
            <button className="panel-button flex-1 bg-purple-600 hover:bg-purple-700 text-white">
              <Layers className="w-4 h-4 mr-2" />
              Preview Changes
            </button>
            <button className="panel-button flex-1 bg-green-600 hover:bg-green-700 text-white">
              <Play className="w-4 h-4 mr-2" />
              Apply Unification
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Analysis */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Text Analysis
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Text Objects</span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">-</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Unique Heights</span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">-</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Unique Styles</span>
                <span className="text-sm font-medium text-slate-900 dark:text-white">-</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-slate-600 dark:text-slate-400">Status</span>
                <span className="text-sm font-medium text-orange-600 dark:text-orange-400">Analyzing</span>
              </div>
            </div>
          </div>

          {/* Presets */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Quick Presets
            </h3>
            <div className="space-y-2">
              <button className="panel-button w-full">
                <Type className="w-4 h-4 mr-2" />
                Standard Drawing
              </button>
              <button className="panel-button w-full">
                <Ruler className="w-4 h-4 mr-2" />
                Title Block Only
              </button>
              <button className="panel-button w-full">
                <Target className="w-4 h-4 mr-2" />
                Dimension Text
              </button>
              <button className="panel-button w-full">
                <Settings className="w-4 h-4 mr-2" />
                Custom Settings
              </button>
            </div>
          </div>

          {/* Progress */}
          <div className="panel-card">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
              Operation Progress
            </h3>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-600 dark:text-slate-400">Current File</span>
                <span className="text-slate-900 dark:text-white">Ready</span>
              </div>
              <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2">
                <div className="bg-purple-600 h-2 rounded-full" style={{ width: '0%' }}></div>
              </div>
              <div className="flex justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>0 of 0 files</span>
                <span>0%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TextUnifierPanel;

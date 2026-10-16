import React, { useState } from 'react';
import { Stethoscope, Upload, Activity, RefreshCw, Trash2, CheckCircle2, AlertCircle, Layers } from 'lucide-react';
import { IntakeForm } from './IntakeForm';
import { Ingestion } from './Ingestion';
import { ChunkInspector } from './ChunkInspector';
import type { SystemHealth } from '../types';

interface DashboardProps {
  health: SystemHealth | null;
  onRefreshHealth: () => void;
  loadingHealth: boolean;
}

export const Dashboard: React.FC<DashboardProps> = ({ health, onRefreshHealth, loadingHealth }) => {
  const [activeTab, setActiveTab] = useState<'ingestion' | 'intake' | 'inspect'>('ingestion');
  const [clearing, setClearing] = useState<boolean>(false);

  const hasDocs = Boolean(health && (health.total_chunks_indexed ?? 0) > 0);

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to delete all uploaded documents from the database?')) {
      return;
    }
    setClearing(true);
    try {
      await fetch('http://127.0.0.1:8000/api/v1/clear', { method: 'POST' });
      onRefreshHealth();
      alert('All uploaded documents have been cleared from database.');
    } catch (e) {
      console.error('Failed to clear:', e);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900 font-sans">
      {/* Top Clean Medical Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-sm px-4 lg:px-8 py-3">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center text-white shadow-md">
              <Activity className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold text-slate-900 tracking-tight">
                  Clinical Document <span className="text-emerald-700">RAG Assistant</span>
                </h1>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                  Strictly Grounded
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Answers ONLY from your uploaded documents. If not in the document: "Not mentioned in the PDF."
              </p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-xl border border-slate-200">
            <button
              onClick={() => setActiveTab('ingestion')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'ingestion'
                  ? 'bg-white text-emerald-800 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Upload className="w-4 h-4 text-emerald-600" />
              <span>Step 1: Upload</span>
            </button>

            <button
              onClick={() => setActiveTab('intake')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'intake'
                  ? 'bg-white text-emerald-800 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Stethoscope className="w-4 h-4 text-emerald-600" />
              <span>Step 2: Ask & Prescribe</span>
            </button>

            <button
              onClick={() => setActiveTab('inspect')}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-bold transition-all ${
                activeTab === 'inspect'
                  ? 'bg-white text-indigo-800 shadow-sm border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers className="w-4 h-4 text-indigo-600" />
              <span>Step 3: Inspect Chunks</span>
            </button>
          </div>

          {/* Status & Clear Button */}
          <div className="flex items-center gap-2">
            {hasDocs ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Active ({health?.total_chunks_indexed} chunks)</span>
                </div>
                <button
                  onClick={handleClearAll}
                  disabled={clearing}
                  className="p-1.5 rounded-lg bg-red-50 hover:bg-red-100 border border-red-200 text-red-700 text-xs font-semibold flex items-center gap-1 transition-colors"
                  title="Wipe uploaded documents"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span className="hidden md:inline">Clear</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-800 font-semibold">
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                <span>No Document Uploaded</span>
              </div>
            )}

            <button
              onClick={onRefreshHealth}
              disabled={loadingHealth}
              className="p-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-600 transition-colors shadow-sm"
              title="Refresh Status"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHealth ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 max-w-6xl mx-auto w-full p-4 sm:p-6 lg:p-8">
        {activeTab === 'ingestion' && (
          <Ingestion 
            health={health} 
            onRefreshHealth={onRefreshHealth} 
            onProceedToQuery={() => setActiveTab('intake')}
          />
        )}
        {activeTab === 'intake' && (
          <IntakeForm 
            indexedDiseases={health?.indexed_diseases || []} 
            hasUploadedDocs={hasDocs}
            onGoToUpload={() => setActiveTab('ingestion')}
          />
        )}
        {activeTab === 'inspect' && (
          <ChunkInspector 
            health={health}
            onRefreshHealth={onRefreshHealth}
          />
        )}
      </main>

      {/* Clean Footer */}
      <footer className="bg-white border-t border-slate-200 py-3.5 px-6 text-center text-xs text-slate-500">
        <p>
          Strict Grounding Constraint: Only answers questions based on user-uploaded documents. 
          If not mentioned in the PDF, returns <strong>"Not mentioned in the PDF."</strong>
        </p>
      </footer>
    </div>
  );
};

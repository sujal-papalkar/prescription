import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, RefreshCw, ArrowRight, Trash2, Database, Shield } from 'lucide-react';
import type { IngestResponse, SystemHealth } from '../types';

interface IngestionProps {
  health: SystemHealth | null;
  onRefreshHealth: () => void;
  onProceedToQuery?: () => void;
}

export const Ingestion: React.FC<IngestionProps> = ({ health, onRefreshHealth, onProceedToQuery }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentTitle, setDocumentTitle] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState<boolean>(false);

  const hasDocs = Boolean(health && (health.total_chunks_indexed ?? 0) > 0);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setError(null);
      setResult(null);
      // Auto-set document title from file name if empty
      if (!documentTitle.trim()) {
        const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
        setDocumentTitle(cleanName);
      }
    }
  };

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile) {
      setError('Please choose a document file to upload (PDF, DOCX, TXT, MD, CSV, XLSX, PNG, JPG, JPEG).');
      return;
    }

    const titleToUse = documentTitle.trim() || selectedFile.name.replace(/\.[^/.]+$/, '');

    setIsSubmitting(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('disease_name', titleToUse);
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/ingest', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Ingestion failed on backend server.');
      }

      const data: IngestResponse = await response.json();
      setResult(data);
      onRefreshHealth();
    } catch (err: any) {
      setError(err.message || 'Could not connect to backend server. Make sure backend is running.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to delete all uploaded guideline documents from the local database?')) {
      return;
    }
    setClearing(true);
    try {
      await fetch('http://127.0.0.1:8000/api/v1/clear', { method: 'POST' });
      setSelectedFile(null);
      setDocumentTitle('');
      setResult(null);
      onRefreshHealth();
    } catch (e) {
      console.error('Failed to clear:', e);
    } finally {
      setClearing(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Intro Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center justify-center">
              1
            </span>
            <h2 className="text-xl font-bold text-slate-900">
              Upload Clinical Guideline Document
            </h2>
          </div>
          <p className="text-xs text-slate-500 mt-1 ml-8">
            Upload your medical guideline or protocol document. It stays 100% on your local machine.
          </p>
        </div>

        {hasDocs && (
          <button
            onClick={handleClearAll}
            disabled={clearing}
            className="px-3 py-1.5 rounded-lg text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 border border-red-200 transition-colors flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>{clearing ? 'Deleting...' : 'Clear Uploaded Documents'}</span>
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Upload Box */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <form onSubmit={handleIngest} className="space-y-5">
            {/* Step A: Select File */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Select Guideline Document
                </label>
                <div className="flex flex-wrap gap-1 text-[10px] text-slate-500">
                  {['PDF', 'DOCX', 'TXT', 'MD', 'CSV', 'XLSX', 'PNG', 'JPG'].map((fmt) => (
                    <span key={fmt} className="px-1.5 py-0.5 bg-slate-100 border border-slate-200 rounded font-mono font-medium text-slate-600">
                      {fmt}
                    </span>
                  ))}
                </div>
              </div>
              
              <div className="border-2 border-dashed border-slate-300 hover:border-emerald-500 rounded-xl p-8 text-center transition-all bg-slate-50 relative group">
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx,.xls,.xlsv,.png,.jpg,.jpeg"
                  onChange={handleFileChange}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                
                <div className="flex flex-col items-center justify-center space-y-3 pointer-events-none">
                  <div className="w-12 h-12 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center group-hover:scale-105 transition-transform">
                    <Upload className="w-6 h-6" />
                  </div>
                  
                  {selectedFile ? (
                    <div>
                      <p className="text-sm font-bold text-emerald-900">{selectedFile.name}</p>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB • Ready to process
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p className="text-sm font-semibold text-slate-800">
                        Click to browse or drop your document here
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        Supports PDF, DOCX, TXT, MD, CSV, Excel, PNG, JPG, JPEG
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Step B: Document Label / Name */}
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">
                Document / Guideline Title (Optional)
              </label>
              <input
                type="text"
                placeholder="e.g. Ayurvedic Clinical Guideline / Respiratory Infections"
                value={documentTitle}
                onChange={(e) => setDocumentTitle(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3.5 py-2.5 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-colors"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Used to label the vector index partitions for this document.
              </p>
            </div>

            {error && (
              <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-lg flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Ingest Button */}
            <button
              type="submit"
              disabled={isSubmitting || !selectedFile}
              className="w-full py-3 px-4 rounded-xl font-bold text-sm bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Parsing Document & Building Local Index...</span>
                </>
              ) : (
                <>
                  <Database className="w-4 h-4" />
                  <span>Upload and Index Document</span>
                </>
              )}
            </button>
          </form>

          {/* Success Result & CTA */}
          {result && (
            <div className="p-5 bg-emerald-50 border border-emerald-200 rounded-xl space-y-3">
              <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span>Document Successfully Ingested!</span>
              </div>
              <p className="text-xs text-emerald-800">
                Created <strong>{result.chunks_indexed}</strong> structured table and text chunks from your document.
              </p>
              
              {onProceedToQuery && (
                <button
                  onClick={onProceedToQuery}
                  className="mt-2 w-full py-2.5 px-4 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-bold flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer"
                >
                  <span>Proceed to Step 2: Ask Questions & Prescribe</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right Info Box */}
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-600" />
              Active Guidelines in Database
            </h3>

            {hasDocs ? (
              <div className="space-y-2">
                {health?.indexed_diseases.map((d, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-emerald-50/60 border border-emerald-200 text-xs font-semibold text-slate-800 flex items-center justify-between"
                  >
                    <span className="flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-500" />
                      {d}
                    </span>
                    <span className="text-[10px] text-emerald-800 font-bold">
                      Indexed
                    </span>
                  </div>
                ))}
                <p className="text-[11px] text-slate-500 pt-1">
                  Total Chunks: <strong>{health?.total_chunks_indexed}</strong>
                </p>
              </div>
            ) : (
              <div className="p-4 rounded-xl border border-dashed border-slate-200 text-center space-y-2 bg-slate-50">
                <p className="text-xs font-medium text-slate-600">
                  No PDF uploaded yet
                </p>
                <p className="text-[11px] text-slate-400">
                  Upload your PDF on the left. The database will only answer questions from your uploaded document.
                </p>
              </div>
            )}
          </div>

          <div className="bg-emerald-50/70 p-4 rounded-2xl border border-emerald-200/80 text-xs text-slate-700 space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-emerald-900">
              <Shield className="w-4 h-4 text-emerald-700" />
              <span>Strict Grounding Guarantee</span>
            </div>
            <p className="text-[11px] text-slate-600 leading-relaxed">
              Whenever you ask a question in Step 2, if the condition, dosage, or query is <strong>not mentioned in the PDF</strong>, the system will explicitly say:
            </p>
            <div className="p-2 rounded bg-white border border-emerald-200 font-mono text-center text-xs font-bold text-slate-800">
              "Not mentioned in the PDF."
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

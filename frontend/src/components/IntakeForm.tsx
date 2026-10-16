import React, { useState } from 'react';
import { 
  AlertTriangle, 
  ChevronDown, 
  ChevronUp, 
  RefreshCw, 
  Search, 
  AlertCircle, 
  ArrowLeft
} from 'lucide-react';
import { StructuredAnswerTable } from './StructuredAnswerTable';
import type { QuestionResponse } from '../types';

interface IntakeFormProps {
  indexedDiseases: string[];
  hasUploadedDocs: boolean;
  onGoToUpload: () => void;
}

export const IntakeForm: React.FC<IntakeFormProps> = ({ 
  indexedDiseases, 
  hasUploadedDocs, 
  onGoToUpload 
}) => {
  // Q&A State
  const [question, setQuestion] = useState<string>('');
  const [selectedDisease, setSelectedDisease] = useState<string>('All');
  const [questionLoading, setQuestionLoading] = useState<boolean>(false);
  const [questionError, setQuestionError] = useState<string | null>(null);
  const [questionResult, setQuestionResult] = useState<QuestionResponse | null>(null);
  const [showQuestionSources, setShowQuestionSources] = useState<boolean>(false);

  // Quick Question suggestions
  const questionSuggestions = [
    'What medications are recommended?',
    'What is the dosage and timing?',
    'What are the contraindications?',
    'What diet (Pathya and Apathya) is suggested?'
  ];

  // Handle Asking Question
  const handleAskQuestion = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!question.trim()) return;

    setQuestionLoading(true);
    setQuestionError(null);
    setQuestionResult(null);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          question: question.trim(),
          disease_name: selectedDisease !== 'All' ? selectedDisease : undefined
        }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || 'Failed to query the document.');
      }

      const data: QuestionResponse = await response.json();
      setQuestionResult(data);
    } catch (err: any) {
      setQuestionError(err.message || 'Could not connect to backend server.');
    } finally {
      setQuestionLoading(false);
    }
  };

  // If no document uploaded
  if (!hasUploadedDocs) {
    return (
      <div className="max-w-xl mx-auto py-12 px-6">
        <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm text-center space-y-5">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 border border-amber-200 text-amber-700 flex items-center justify-center mx-auto shadow-sm">
            <AlertTriangle className="w-7 h-7" />
          </div>

          <div>
            <h2 className="text-xl font-bold text-slate-900">
              No PDF Document Uploaded Yet
            </h2>
            <p className="text-xs text-slate-600 mt-2 max-w-md mx-auto leading-relaxed">
              This assistant strictly grounds all answers in your uploaded PDF.
              Please upload your clinical guideline or medical protocol PDF in Step 1 first.
            </p>
          </div>

          <div className="pt-2">
            <button
              onClick={onGoToUpload}
              className="inline-flex items-center gap-2 px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs shadow-sm transition-all cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Go to Step 1: Upload Your PDF</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* ======================================================== */}
      {/* SECTION 1: DIRECT QUESTION ANSWERING (PRIMARY FEATURE)    */}
      {/* ======================================================== */}
      <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center justify-center">
                2
              </span>
              <h2 className="text-xl font-bold text-slate-900">
                Ask Questions About Your PDF
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1 ml-8">
              Ask anything. If it is not in your uploaded PDF, the system will explicitly say: <strong>"Not mentioned in the PDF."</strong>
            </p>
          </div>

          <span className="px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
            PDF Loaded & Ready
          </span>
        </div>

        {/* Question Search Form */}
        <form onSubmit={handleAskQuestion} className="space-y-4">
          {indexedDiseases && indexedDiseases.length > 1 && (
            <div className="flex items-center gap-2 pb-1">
              <label className="text-xs font-semibold text-slate-600">Guideline Filter:</label>
              <select
                value={selectedDisease}
                onChange={(e) => setSelectedDisease(e.target.value)}
                className="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1 text-xs text-slate-800"
              >
                <option value="All">All Uploaded Documents</option>
                {indexedDiseases.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
          )}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
              <Search className="w-5 h-5" />
            </div>
            <input
              type="text"
              placeholder="Type your question (e.g. What is the dosage of Sitopaladi?, What are the contraindications?)"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="w-full pl-11 pr-28 py-3.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:bg-white transition-all shadow-sm"
            />
            <div className="absolute inset-y-0 right-1.5 flex items-center">
              <button
                type="submit"
                disabled={questionLoading || !question.trim()}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg text-xs transition-colors flex items-center gap-1.5 shadow-sm disabled:opacity-50 cursor-pointer"
              >
                {questionLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Searching...</span>
                  </>
                ) : (
                  <span>Ask Question</span>
                )}
              </button>
            </div>
          </div>

          {/* Quick Suggestion Chips */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <span className="text-[11px] font-semibold text-slate-400">Example questions:</span>
            {questionSuggestions.map((sug, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuestion(sug);
                }}
                className="px-2.5 py-1 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition-colors cursor-pointer"
              >
                {sug}
              </button>
            ))}
          </div>
        </form>

        {questionError && (
          <div className="p-3 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{questionError}</span>
          </div>
        )}

        {/* Question Result Display */}
        {questionResult && (
          <div className="pt-2 space-y-3">
            {!questionResult.found_in_pdf ? (
              /* NEGATIVE GROUNDING ALERT */
              <div className="p-5 rounded-xl bg-amber-50 border-2 border-amber-300 text-amber-950 space-y-2">
                <div className="flex items-center gap-2 font-bold text-base text-amber-900">
                  <AlertCircle className="w-5 h-5 text-amber-600" />
                  <span>Not mentioned in the PDF.</span>
                </div>
                <p className="text-xs text-amber-800">
                  The query: <em>"{questionResult.question}"</em> is not found or discussed in your uploaded PDF document.
                </p>
                <div className="p-2.5 rounded bg-white/80 border border-amber-200 text-xs font-mono text-slate-700">
                  Response: {questionResult.answer}
                </div>
              </div>
            ) : (
              /* CLINICAL RESULT CARD MATCHING UI SPECIFICATION */
              <div className="space-y-4">
                <StructuredAnswerTable 
                  answer={questionResult.answer} 
                  question={questionResult.question}
                  sourceChunks={questionResult.source_chunks}
                />

                {/* Collapsible Source Excerpts */}
                {questionResult.source_chunks && questionResult.source_chunks.length > 0 && (
                  <div className="px-2">
                    <button
                      type="button"
                      onClick={() => setShowQuestionSources(!showQuestionSources)}
                      className="text-xs font-bold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 cursor-pointer"
                    >
                      {showQuestionSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                      <span>
                        {showQuestionSources ? 'Hide' : 'View'} Raw Source Excerpts from PDF ({questionResult.source_chunks.length})
                      </span>
                    </button>

                    {showQuestionSources && (
                      <div className="mt-2 space-y-2">
                        {questionResult.source_chunks.map((chunk, idx) => (
                          <div key={idx} className="p-3 bg-white rounded-xl border border-slate-200 text-xs font-mono text-slate-700 leading-relaxed shadow-xs">
                            <span className="font-bold text-emerald-700">[Excerpt {idx + 1}]: </span>
                            {chunk.text}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

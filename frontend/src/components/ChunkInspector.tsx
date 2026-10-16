import React, { useState, useEffect } from 'react';
import { 
  Layers, 
  Table, 
  Search, 
  ChevronDown, 
  ChevronUp, 
  Database, 
  RefreshCw, 
  BookOpen,
  Info
} from 'lucide-react';

interface ChunkItem {
  chunk_id: string;
  disease_name: string;
  chunk_type: string;
  page: number | string;
  section: string;
  source: string;
  metadata: Record<string, any>;
  word_count: number;
  preview: string;
  text: string;
}

interface InspectResponse {
  status: string;
  total_in_db: number;
  total_matching: number;
  offset: number;
  limit: number;
  summary: {
    by_disease: Record<string, number>;
    by_type: Record<string, number>;
    by_page: Record<string, number>;
  };
  chunks: ChunkItem[];
}

interface ChunkInspectorProps {
  health?: any;
  onRefreshHealth: () => void;
}

export const ChunkInspector: React.FC<ChunkInspectorProps> = ({ onRefreshHealth }) => {
  const [data, setData] = useState<InspectResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [selectedDisease, setSelectedDisease] = useState<string>('All');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [selectedPage, setSelectedPage] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedChunkId, setExpandedChunkId] = useState<string | null>(null);
  const [pageOffset, setPageOffset] = useState<number>(0);
  const pageSize = 25;

  const fetchChunks = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (selectedDisease !== 'All') params.append('disease_name', selectedDisease);
      if (selectedType !== 'All') params.append('chunk_type', selectedType);
      if (selectedPage !== 'All') params.append('page', selectedPage);
      if (searchQuery.trim()) params.append('search', searchQuery.trim());
      params.append('limit', pageSize.toString());
      params.append('offset', pageOffset.toString());

      const res = await fetch(`http://127.0.0.1:8000/api/v1/inspect/chunks?${params.toString()}`);
      if (!res.ok) {
        throw new Error('Failed to load chunks from backend inspector API.');
      }
      const json: InspectResponse = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Error connecting to chunk inspection API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChunks();
  }, [selectedDisease, selectedType, selectedPage, pageOffset]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPageOffset(0);
    fetchChunks();
  };

  const diseaseList = data?.summary?.by_disease ? Object.keys(data.summary.by_disease) : [];
  const pageList = data?.summary?.by_page ? Object.keys(data.summary.by_page) : [];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Top Banner & Stats */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-100 text-indigo-700 flex items-center justify-center font-bold">
                <Layers className="w-4 h-4" />
              </div>
              <h2 className="text-lg font-bold text-slate-900">
                Extraction & Chunking Audit Inspector
              </h2>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Verify how your clinical documents were extracted, split into section hierarchies, and converted into structured matrices.
            </p>
          </div>

          <button
            onClick={() => { onRefreshHealth(); fetchChunks(); }}
            disabled={loading}
            className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Chunks</span>
          </button>
        </div>

        {/* Summary Metric Cards */}
        {data && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2 border-t border-slate-100">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/80">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-600 uppercase tracking-wider">Total Chunks</span>
                <Database className="w-4 h-4 text-indigo-600" />
              </div>
              <p className="text-2xl font-extrabold text-slate-900 mt-1">{data.total_in_db}</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                {data.total_matching} matching current filters
              </p>
            </div>

            <div className="p-4 rounded-xl bg-indigo-50/50 border border-indigo-200/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-800 uppercase tracking-wider">Table Matrices</span>
                <Table className="w-4 h-4 text-indigo-700" />
              </div>
              <p className="text-2xl font-extrabold text-indigo-950 mt-1">
                {data.summary.by_type?.table_matrix || 0}
              </p>
              <p className="text-[11px] text-indigo-700 mt-0.5">
                Forward-filled rows for exact prescription matching
              </p>
            </div>

            <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800 uppercase tracking-wider">Prose & Tables</span>
                <BookOpen className="w-4 h-4 text-emerald-700" />
              </div>
              <p className="text-2xl font-extrabold text-emerald-950 mt-1">
                {data.summary.by_type?.prose_narrative || 0}
              </p>
              <p className="text-[11px] text-emerald-700 mt-0.5">
                Section breadcrumbs & full Markdown tables
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Filter & Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3 items-center">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search words inside chunks (e.g. Somtajvir, Diabetes, MILD, HRCT)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition-colors cursor-pointer w-full sm:w-auto"
          >
            Filter
          </button>
        </form>

        <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs">
          {/* Document Partition */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-500 text-[11px] uppercase">Document:</span>
            <select
              value={selectedDisease}
              onChange={(e) => { setSelectedDisease(e.target.value); setPageOffset(0); }}
              className="bg-slate-50 border border-slate-200 rounded px-2.5 py-1 text-xs text-slate-800 focus:outline-none"
            >
              <option value="All">All Documents</option>
              {diseaseList.map((d) => (
                <option key={d} value={d}>
                  {d} ({data?.summary?.by_disease[d]})
                </option>
              ))}
            </select>
          </div>

          {/* Chunk Type Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-500 text-[11px] uppercase">Type:</span>
            <select
              value={selectedType}
              onChange={(e) => { setSelectedType(e.target.value); setPageOffset(0); }}
              className="bg-slate-50 border border-slate-200 rounded px-2.5 py-1 text-xs text-slate-800 focus:outline-none"
            >
              <option value="All">All Types</option>
              <option value="table_matrix">table_matrix ({data?.summary?.by_type?.table_matrix || 0})</option>
              <option value="prose_narrative">prose_narrative ({data?.summary?.by_type?.prose_narrative || 0})</option>
            </select>
          </div>

          {/* Page Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-500 text-[11px] uppercase">Page:</span>
            <select
              value={selectedPage}
              onChange={(e) => { setSelectedPage(e.target.value); setPageOffset(0); }}
              className="bg-slate-50 border border-slate-200 rounded px-2.5 py-1 text-xs text-slate-800 focus:outline-none"
            >
              <option value="All">All Pages</option>
              {pageList.map((p) => (
                <option key={p} value={p}>
                  Page {p} ({data?.summary?.by_page[p]})
                </option>
              ))}
            </select>
          </div>

          {(selectedDisease !== 'All' || selectedType !== 'All' || selectedPage !== 'All' || searchQuery) && (
            <button
              onClick={() => {
                setSelectedDisease('All');
                setSelectedType('All');
                setSelectedPage('All');
                setSearchQuery('');
                setPageOffset(0);
              }}
              className="text-[11px] text-red-600 hover:underline font-semibold ml-auto"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Chunk List */}
      <div className="space-y-3">
        {loading && (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm text-slate-500 text-xs">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-600 mb-2" />
            <span>Loading extracted chunks...</span>
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl">
            {error}
          </div>
        )}

        {!loading && !error && data && data.chunks.length === 0 && (
          <div className="p-12 text-center bg-white rounded-2xl border border-slate-200 shadow-sm text-slate-500 text-xs">
            <Info className="w-6 h-6 mx-auto text-slate-400 mb-2" />
            <span>No chunks match the current filter criteria.</span>
          </div>
        )}

        {!loading && data && data.chunks.map((chunk, idx) => {
          const isExpanded = expandedChunkId === chunk.chunk_id;
          const isTableMatrix = chunk.chunk_type === 'table_matrix';

          return (
            <div
              key={chunk.chunk_id || idx}
              className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden transition-all hover:border-slate-300"
            >
              {/* Header row */}
              <div
                onClick={() => setExpandedChunkId(isExpanded ? null : chunk.chunk_id)}
                className="p-4 flex items-center justify-between gap-3 cursor-pointer select-none bg-slate-50/50 hover:bg-slate-50 transition-colors"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                    isTableMatrix 
                      ? 'bg-indigo-100 text-indigo-800 border border-indigo-200' 
                      : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  }`}>
                    {chunk.chunk_type}
                  </span>

                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-200/80 text-slate-700 border border-slate-300">
                    Page {chunk.page}
                  </span>

                  <span className="text-xs font-bold text-slate-800 max-w-md truncate">
                    {chunk.section || chunk.disease_name}
                  </span>

                  <span className="text-[11px] text-slate-400">
                    ({chunk.word_count} words)
                  </span>
                </div>

                <div className="flex items-center gap-2 text-slate-400">
                  <span className="text-[11px] font-mono text-slate-400 hidden md:inline">
                    {chunk.chunk_id}
                  </span>
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </div>
              </div>

              {/* Text Preview / Expanded Body */}
              <div className="p-4 border-t border-slate-100 text-xs">
                {isExpanded ? (
                  <div className="space-y-3">
                    <div className="bg-slate-900 text-slate-100 p-4 rounded-lg font-mono text-[11px] whitespace-pre-wrap leading-relaxed overflow-x-auto max-h-96">
                      {chunk.text}
                    </div>

                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1 text-[11px] text-slate-600">
                      <p><strong>Source Document:</strong> {chunk.source}</p>
                      <p><strong>Partition:</strong> {chunk.disease_name}</p>
                      {chunk.metadata?.category && (
                        <p><strong>Category / Sub-condition:</strong> {chunk.metadata.category}</p>
                      )}
                      {chunk.metadata?.level !== undefined && (
                        <p><strong>Heading Level:</strong> {chunk.metadata.level}</p>
                      )}
                    </div>
                  </div>
                ) : (
                  <p className="text-slate-600 line-clamp-2 font-mono text-[11px]">
                    {chunk.preview}
                  </p>
                )}
              </div>
            </div>
          );
        })}

        {/* Pagination Bar */}
        {!loading && data && data.total_matching > pageSize && (
          <div className="flex items-center justify-between p-4 bg-white rounded-xl border border-slate-200 shadow-sm text-xs">
            <span className="text-slate-500">
              Showing {pageOffset + 1} - {Math.min(pageOffset + pageSize, data.total_matching)} of {data.total_matching} chunks
            </span>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setPageOffset(Math.max(0, pageOffset - pageSize))}
                disabled={pageOffset === 0}
                className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>

              <button
                onClick={() => setPageOffset(pageOffset + pageSize)}
                disabled={pageOffset + pageSize >= data.total_matching}
                className="px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

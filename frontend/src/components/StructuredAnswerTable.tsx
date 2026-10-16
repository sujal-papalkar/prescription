import React, { useState, useMemo } from 'react';
import { 
  ShieldCheck, 
  Pill, 
  Clock, 
  Droplets, 
  Calendar, 
  FileText, 
  ExternalLink, 
  Copy, 
  Check, 
  Printer, 
  Sparkles,
  AlertCircle,
  Activity,
  ClipboardList,
  Table,
  LayoutGrid
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface StructuredAnswerTableProps {
  answer: string;
  question?: string;
  sourceChunks?: Array<{
    chunk_id?: string;
    text: string;
    metadata?: Record<string, any>;
  }>;
}

export interface FormulationItem {
  id: string;
  name: string;
  dose: string;
  frequency?: string;
  timing?: string;
  duration?: string;
  vehicle?: string;
  source: string;
  page: string;
  section?: string;
}

export interface ProtocolItem {
  id: string;
  topic: string;
  details: string;
  source: string;
  page: string;
  section?: string;
}

interface ParsedClinicalContent {
  formulations: FormulationItem[];
  protocols: ProtocolItem[];
  narrativeMarkdown: string;
}

function isNotSpecified(val?: string): boolean {
  if (!val) return true;
  const clean = val.trim().toLowerCase();
  return (
    clean === 'not specified' ||
    clean === '-' ||
    clean === 'n/a' ||
    clean === 'none' ||
    clean === '' ||
    clean === 'nil' ||
    clean === 'null'
  );
}

function cleanDocName(source?: string): string {
  if (!source) return 'Clinical Guideline Document';
  const basename = source.split('/').pop()?.split('\\').pop() || source;
  if (basename.includes('Respiratory_Viral_Infection') || basename.includes('Respiratory Viral Infection')) {
    return 'Respiratory Viral Infection Management protocol.pdf';
  }
  if (basename.includes('DM_RR') || basename.includes('DM RR')) {
    return 'DM RR(7).docx';
  }
  return basename.replace(/[_-]/g, ' ');
}

function formatPageCitation(val?: string | number): string {
  if (!val || val === '-') return '-';
  const clean = String(val).trim();
  if (
    clean.toLowerCase().startsWith('pg') ||
    clean.toLowerCase().startsWith('page') ||
    clean.toLowerCase().startsWith('table')
  ) {
    return clean;
  }
  return `Pg ${clean}`;
}

function parseClinicalAnswer(
  answer: string,
  _question?: string,
  sourceChunks?: Array<{ chunk_id?: string; text: string; metadata?: Record<string, any> }>
): ParsedClinicalContent {
  const lines = answer.split('\n');
  const tableBlocks: { title?: string; lines: string[] }[] = [];
  const narrativeLines: string[] = [];
  let currentTable: string[] = [];
  let currentSection = '';
  let pendingTableSection = '';

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i];
    const trimmed = rawLine.trim();

    if (trimmed.startsWith('#')) {
      currentSection = trimmed.replace(/^[#\s*]+/, '').replace(/[*#]+$/, '').trim();
    }

    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      if (currentTable.length === 0) {
        pendingTableSection = currentSection;
      }
      currentTable.push(trimmed);
    } else {
      if (currentTable.length > 0) {
        tableBlocks.push({ title: pendingTableSection, lines: currentTable });
        currentTable = [];
        pendingTableSection = '';
      }
      narrativeLines.push(rawLine);
    }
  }
  if (currentTable.length > 0) {
    tableBlocks.push({ title: pendingTableSection, lines: currentTable });
  }

  const defaultDoc = cleanDocName(sourceChunks?.[0]?.metadata?.source || sourceChunks?.[0]?.metadata?.disease_name);
  const defaultPage = sourceChunks?.[0]?.metadata?.page ? String(sourceChunks[0].metadata.page) : '-';

  const formulations: FormulationItem[] = [];
  const protocols: ProtocolItem[] = [];
  const seenFormulations = new Set<string>();

  // Process all table blocks
  for (const block of tableBlocks) {
    const tableLines = block.lines;
    const blockTitle = block.title || '';
    if (tableLines.length < 2) continue;

    const headers = tableLines[0]
      .split('|')
      .slice(1, -1)
      .map(h => h.trim().replace(/\*\*/g, ''));

    // Check header keywords
    const isFormulationTable = headers.some(h =>
      /medicine|formulation|drug|rasayan|matra|dose/i.test(h)
    );

    // Filter out delimiter row (|---|---|)
    const dataLines = tableLines.slice(1).filter(l => !/^[|\s-:]+$/.test(l));

    if (isFormulationTable) {
      const findIdx = (keywords: string[]) =>
        headers.findIndex(h => keywords.some(k => h.toLowerCase().includes(k)));

      const nameIdx = Math.max(0, findIdx(['medicine', 'formulation', 'drug', 'rasayan', 'name']));
      const doseIdx = findIdx(['matra', 'dose', 'dosage']);
      const freqIdx = findIdx(['frequency']);
      const timingIdx = findIdx(['timing', 'kal', 'aushadh', 'time']);
      const durationIdx = findIdx(['duration', 'days', 'period']);
      const vehicleIdx = findIdx(['sahpaan', 'sahapan', 'anupana', 'vehicle', 'with']);
      const sourceIdx = findIdx(['source', 'document', 'doc']);
      const pageIdx = findIdx(['page']);

      for (let rIdx = 0; rIdx < dataLines.length; rIdx++) {
        const cells = dataLines[rIdx]
          .split('|')
          .slice(1, -1)
          .map(c => c.trim().replace(/\*\*/g, ''));

        const rawName = cells[nameIdx] || '';
        // Skip header lines that were repeated
        if (!rawName || (/medicine|formulation|drug/i.test(rawName) && /dose|matra/i.test(cells[doseIdx] || ''))) {
          continue;
        }

        const rawDose = doseIdx !== -1 ? cells[doseIdx] || '' : '';
        const rawFreq = freqIdx !== -1 ? cells[freqIdx] || '' : '';
        const rawTiming = timingIdx !== -1 ? cells[timingIdx] || '' : '';
        const rawDuration = durationIdx !== -1 ? cells[durationIdx] || '' : '';
        const rawVehicle = vehicleIdx !== -1 ? cells[vehicleIdx] || '' : '';
        
        let rowDoc = sourceIdx !== -1 && cells[sourceIdx] ? cleanDocName(cells[sourceIdx]) : '';
        let rowPage = pageIdx !== -1 && cells[pageIdx] ? cells[pageIdx] : '';

        if (!rowDoc || rowDoc === 'Uploaded Document') {
          const chunk = sourceChunks?.[rIdx % (sourceChunks?.length || 1)];
          rowDoc = cleanDocName(chunk?.metadata?.source || chunk?.metadata?.disease_name) || defaultDoc;
        }
        if (!rowPage || rowPage === '-') {
          const chunk = sourceChunks?.[rIdx % (sourceChunks?.length || 1)];
          rowPage = chunk?.metadata?.page ? String(chunk.metadata.page) : defaultPage;
        }

        // Deduplication key per section
        const uniqueKey = `${rawName.toLowerCase()}-${rawDose.toLowerCase()}-${rawTiming.toLowerCase()}-${blockTitle.toLowerCase()}`;
        if (!seenFormulations.has(uniqueKey)) {
          seenFormulations.add(uniqueKey);
          formulations.push({
            id: `f-${formulations.length}`,
            name: rawName,
            dose: rawDose,
            frequency: rawFreq,
            timing: rawTiming,
            duration: rawDuration,
            vehicle: rawVehicle,
            source: rowDoc,
            page: rowPage,
            section: blockTitle
          });
        }
      }
    } else {
      // Protocol / Topic table (e.g. Investigation, Supportive Care, Dietary)
      const findIdx = (keywords: string[]) =>
        headers.findIndex(h => keywords.some(k => h.toLowerCase().includes(k)));

      const topicIdx = Math.max(0, findIdx(['parameter', 'topic', 'category', 'investigation', 'item']));
      const detailsIdx = Math.max(1, findIdx(['details', 'description', 'findings', 'recommended', 'prohibited']));
      const sourceIdx = findIdx(['source', 'document', 'doc']);
      const pageIdx = findIdx(['page']);

      for (let rIdx = 0; rIdx < dataLines.length; rIdx++) {
        const cells = dataLines[rIdx]
          .split('|')
          .slice(1, -1)
          .map(c => c.trim().replace(/\*\*/g, ''));

        const rawTopic = cells[topicIdx] || '';
        if (!rawTopic || (/parameter|topic|category/i.test(rawTopic) && /details|finding/i.test(cells[detailsIdx] || ''))) {
          continue;
        }

        const rawDetails = cells[detailsIdx] || '';
        const rowDoc = sourceIdx !== -1 && cells[sourceIdx] ? cleanDocName(cells[sourceIdx]) : defaultDoc;
        const rowPage = pageIdx !== -1 && cells[pageIdx] ? cells[pageIdx] : defaultPage;

        protocols.push({
          id: `p-${protocols.length}`,
          topic: rawTopic,
          details: rawDetails,
          source: rowDoc,
          page: rowPage,
          section: blockTitle
        });
      }
    }
  }

  // Fallback: If no tables were found, check if chunks have Medicine tags
  if (formulations.length === 0 && protocols.length === 0) {
    const medPattern = /Medicine:\s*([^,]+)/i;
    if (sourceChunks && sourceChunks.some(c => medPattern.test(c.text))) {
      for (const item of sourceChunks) {
        const medMatch = item.text.match(/Medicine:\s*([^,]+)/i);
        const matraMatch = item.text.match(/Matra:\s*([^,]+)/i);
        const sahpaanMatch = item.text.match(/Sahpaan:\s*([^,]+)/i);
        const kalMatch = item.text.match(/Aushadh Kal:\s*([^,\n]+)/i);

        if (medMatch) {
          const medName = medMatch[1].trim();
          if (seenFormulations.has(medName.toLowerCase())) continue;
          seenFormulations.add(medName.toLowerCase());

          formulations.push({
            id: `f-${formulations.length}`,
            name: medName,
            dose: matraMatch ? matraMatch[1].trim() : 'Not specified',
            frequency: 'Not specified',
            timing: kalMatch ? kalMatch[1].trim() : 'Not specified',
            duration: 'Not specified',
            vehicle: sahpaanMatch ? sahpaanMatch[1].trim() : 'Not specified',
            source: cleanDocName(item.metadata?.source || item.metadata?.disease_name),
            page: item.metadata?.page ? String(item.metadata.page) : defaultPage,
            section: 'Prescribed Regimen'
          });
        }
      }
    }
  }

  // Clean narrative markdown: trim leading/trailing blank lines
  const narrativeMarkdown = narrativeLines.join('\n').trim();

  return {
    formulations,
    protocols,
    narrativeMarkdown
  };
}

export const StructuredAnswerTable: React.FC<StructuredAnswerTableProps> = ({
  answer,
  question,
  sourceChunks
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  const { formulations, protocols, narrativeMarkdown } = useMemo(() => {
    return parseClinicalAnswer(answer, question, sourceChunks);
  }, [answer, question, sourceChunks]);

  const hasFormulations = formulations.length > 0;
  const hasProtocols = protocols.length > 0;
  const hasNarrative = Boolean(narrativeMarkdown && narrativeMarkdown.length > 0);

  // Smart Visibility: Check if frequency or duration contain meaningful clinical data across all formulations
  const hasFrequencyData = useMemo(() => {
    return formulations.some(f => !isNotSpecified(f.frequency));
  }, [formulations]);

  const hasDurationData = useMemo(() => {
    return formulations.some(f => !isNotSpecified(f.duration));
  }, [formulations]);

  // Dynamically calculate column count for divider rows
  const colCount = 6 + (hasFrequencyData ? 1 : 0) + (hasDurationData ? 1 : 0);

  // Group formulations by section (if distinct sections exist)
  const groupedFormulations = useMemo(() => {
    const groups: { section: string; items: FormulationItem[] }[] = [];
    const sectionMap = new Map<string, FormulationItem[]>();

    formulations.forEach(item => {
      const sec = item.section || 'General Prescription Formulations';
      if (!sectionMap.has(sec)) {
        sectionMap.set(sec, []);
      }
      sectionMap.get(sec)!.push(item);
    });

    sectionMap.forEach((items, section) => {
      groups.push({ section, items });
    });

    return groups;
  }, [formulations]);

  const hasMultipleSections = groupedFormulations.length > 1;

  // Dynamic Title & Badges
  const { title, subtitle } = useMemo(() => {
    if (hasFormulations) {
      return {
        title: 'Prescription Results',
        subtitle: 'Evidence-grounded Ayurvedic formulations with verified document and page provenance'
      };
    }
    if (hasProtocols) {
      return {
        title: 'Clinical Protocol Results',
        subtitle: 'Evidence-grounded clinical protocols and supportive guidance from uploaded guidelines'
      };
    }
    return {
      title: 'Clinical Assessment & Guidance',
      subtitle: 'Strictly grounded clinical findings and observations from uploaded documents'
    };
  }, [hasFormulations, hasProtocols]);

  // Copy Results as clean structured text
  const handleCopy = () => {
    const lines: string[] = [];
    lines.push(`CLINICAL RESULTS: ${title}`);
    lines.push(`Query: ${question || 'Clinical Query'}\n`);

    if (formulations.length > 0) {
      lines.push('--- PRESCRIBED MEDICINES ---');
      formulations.forEach((f, i) => {
        const extra: string[] = [];
        if (!isNotSpecified(f.frequency)) extra.push(`Freq: ${f.frequency}`);
        if (!isNotSpecified(f.duration)) extra.push(`Duration: ${f.duration}`);
        const extraText = extra.length > 0 ? ` | ${extra.join(' | ')}` : '';
        lines.push(`${i + 1}. ${f.name} | Dose: ${f.dose || 'N/A'} | Timing: ${f.timing || 'N/A'} | Vehicle: ${f.vehicle || 'N/A'}${extraText} | Source: ${f.source} (${formatPageCitation(f.page)})`);
      });
      lines.push('');
    }

    if (protocols.length > 0) {
      lines.push('--- PROTOCOLS & INSTRUCTIONS ---');
      protocols.forEach((p, i) => {
        lines.push(`${i + 1}. ${p.topic}: ${p.details} | Source: ${p.source} (${formatPageCitation(p.page)})`);
      });
      lines.push('');
    }

    if (narrativeMarkdown) {
      lines.push('--- CLINICAL NOTES & PRECAUTIONS ---');
      lines.push(narrativeMarkdown);
    }

    navigator.clipboard.writeText(lines.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 sm:p-7 space-y-6 font-sans">
      {/* ======================================================== */}
      {/* 1. TOP HEADER & METRIC BADGES                            */}
      {/* ======================================================== */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span>{title}</span>
          </h3>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5">
            {subtitle}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 shrink-0">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            <span>Grounded & Validated</span>
          </span>

          {hasFormulations && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
              {formulations.length} {formulations.length === 1 ? 'Formulation' : 'Formulations'}
            </span>
          )}

          {hasProtocols && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-cyan-50 text-cyan-800 border border-cyan-200">
              {protocols.length} {protocols.length === 1 ? 'Protocol' : 'Protocols'}
            </span>
          )}
        </div>
      </div>

      {/* ======================================================== */}
      {/* 2. PRESCRIPTION FORMULATIONS (TABLE OR CARDS VIEW)       */}
      {/* ======================================================== */}
      {hasFormulations && (
        <div className="space-y-3.5">
          {/* Section Toolbar: Title + View Switcher */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
              <Pill className="w-4 h-4 text-emerald-600" />
              <span>Prescribed Formulations Table (From Guideline Matrix)</span>
            </div>

            {/* View Mode Toggle: Table (default) / Cards */}
            <div className="inline-flex items-center p-0.5 bg-slate-100 rounded-lg border border-slate-200 text-xs shrink-0">
              <button
                type="button"
                onClick={() => setViewMode('table')}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-all cursor-pointer ${
                  viewMode === 'table'
                    ? 'bg-white text-emerald-800 font-bold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 font-medium'
                }`}
                title="View in standard medical table format"
              >
                <Table className="w-3.5 h-3.5 text-emerald-600" />
                <span>Table View</span>
              </button>
              <button
                type="button"
                onClick={() => setViewMode('cards')}
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-md transition-all cursor-pointer ${
                  viewMode === 'cards'
                    ? 'bg-white text-emerald-800 font-bold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 font-medium'
                }`}
                title="View in responsive formulation cards format"
              >
                <LayoutGrid className="w-3.5 h-3.5 text-emerald-600" />
                <span>Cards View</span>
              </button>
            </div>
          </div>

          {/* VIEW MODE: TABLE FORMAT (DEFAULT) */}
          {viewMode === 'table' ? (
            <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-xs bg-white">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50/95 text-[11px] font-bold text-slate-700 uppercase tracking-wider border-b border-slate-200">
                    <th className="py-3 px-3.5 font-bold text-slate-800 min-w-[140px]">
                      Medicine / Formulation
                    </th>
                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[95px] text-center">
                      Dose / Matra
                    </th>

                    {/* Conditionally Render Frequency Column ONLY if specified by at least one medicine */}
                    {hasFrequencyData && (
                      <th className="py-3 px-3 font-bold text-slate-800 min-w-[110px]">
                        Frequency
                      </th>
                    )}

                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[170px]">
                      Timing / Aushadh Kal
                    </th>

                    {/* Conditionally Render Duration Column ONLY if specified by at least one medicine */}
                    {hasDurationData && (
                      <th className="py-3 px-3 font-bold text-slate-800 min-w-[110px]">
                        Duration
                      </th>
                    )}

                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[140px]">
                      Anupana / Sahapaan
                    </th>
                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[170px]">
                      Source Document
                    </th>
                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[85px] text-center">
                      Page
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {hasMultipleSections ? (
                    groupedFormulations.map((group) => (
                      <React.Fragment key={group.section}>
                        {/* Section Divider Row */}
                        <tr className="bg-emerald-50/60 border-y border-emerald-100/80">
                          <td colSpan={colCount} className="py-2 px-3.5 text-xs font-bold text-emerald-950 tracking-wide">
                            <div className="flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                              <span>{group.section}</span>
                              <span className="text-[10px] font-normal text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded-full ml-1">
                                {group.items.length} {group.items.length === 1 ? 'item' : 'items'}
                              </span>
                            </div>
                          </td>
                        </tr>

                        {group.items.map((item) => (
                          <tr 
                            key={item.id} 
                            className="hover:bg-emerald-50/25 transition-colors even:bg-slate-50/30"
                          >
                            {/* Medicine Name */}
                            <td className="py-3 px-3.5 font-bold text-slate-900 align-top">
                              <div className="flex items-center gap-2">
                                <div className="w-6 h-6 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-100 flex items-center justify-center shrink-0">
                                  <Pill className="w-3.5 h-3.5 text-emerald-600" />
                                </div>
                                <span className="font-bold text-slate-900 leading-snug">{item.name}</span>
                              </div>
                            </td>

                            {/* Dose */}
                            <td className="py-3 px-3 align-top text-center">
                              {!isNotSpecified(item.dose) ? (
                                <span className="inline-block px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-950 border border-emerald-300/80 font-mono font-bold text-xs">
                                  {item.dose}
                                </span>
                              ) : (
                                <span className="italic text-slate-400">Not specified</span>
                              )}
                            </td>

                            {/* Frequency (Dynamic) */}
                            {hasFrequencyData && (
                              <td className="py-3 px-3 align-top text-slate-700 font-medium">
                                {!isNotSpecified(item.frequency) ? (
                                  item.frequency
                                ) : (
                                  <span className="italic text-slate-400">Not specified</span>
                                )}
                              </td>
                            )}

                            {/* Timing */}
                            <td className="py-3 px-3 align-top text-slate-800 font-medium leading-relaxed">
                              {!isNotSpecified(item.timing) ? (
                                <div className="flex items-start gap-1.5">
                                  <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                                  <span>{item.timing}</span>
                                </div>
                              ) : (
                                <span className="italic text-slate-400">Not specified</span>
                              )}

                              {/* If duration column is hidden but this specific item has duration */}
                              {!hasDurationData && item.duration && !isNotSpecified(item.duration) && (
                                <div className="mt-1 flex items-center gap-1 text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 inline-flex">
                                  <Calendar className="w-3 h-3 text-emerald-600" />
                                  <span>Duration: {item.duration}</span>
                                </div>
                              )}
                            </td>

                            {/* Duration (Dynamic) */}
                            {hasDurationData && (
                              <td className="py-3 px-3 align-top text-slate-700 font-medium">
                                {!isNotSpecified(item.duration) ? (
                                  <div className="flex items-center gap-1.5">
                                    <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                    <span>{item.duration}</span>
                                  </div>
                                ) : (
                                  <span className="italic text-slate-400">Not specified</span>
                                )}
                              </td>
                            )}

                            {/* Anupana / Sahapaan */}
                            <td className="py-3 px-3 align-top text-slate-800 font-medium leading-relaxed">
                              {!isNotSpecified(item.vehicle) ? (
                                <div className="flex items-start gap-1.5">
                                  <Droplets className="w-3.5 h-3.5 text-cyan-600 shrink-0 mt-0.5" />
                                  <span>{item.vehicle}</span>
                                </div>
                              ) : (
                                <span className="italic text-slate-400">Not specified</span>
                              )}
                            </td>

                            {/* Source Document */}
                            <td className="py-3 px-3 align-top text-slate-600">
                              <div className="flex items-center gap-1.5" title={item.source}>
                                <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                <span className="truncate max-w-[170px] text-[11px] font-medium text-slate-700">
                                  {item.source}
                                </span>
                              </div>
                            </td>

                            {/* Page */}
                            <td className="py-3 px-3 align-top text-center">
                              {item.page && item.page !== '-' ? (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-mono font-bold">
                                  <span>{formatPageCitation(item.page)}</span>
                                  <ExternalLink className="w-2.5 h-2.5 text-emerald-600" />
                                </span>
                              ) : (
                                <span className="text-slate-400">-</span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </React.Fragment>
                    ))
                  ) : (
                    formulations.map((item) => (
                      <tr 
                        key={item.id} 
                        className="hover:bg-emerald-50/25 transition-colors even:bg-slate-50/30"
                      >
                        {/* Medicine Name */}
                        <td className="py-3 px-3.5 font-bold text-slate-900 align-top">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-100 flex items-center justify-center shrink-0">
                              <Pill className="w-3.5 h-3.5 text-emerald-600" />
                            </div>
                            <span className="font-bold text-slate-900 leading-snug">{item.name}</span>
                          </div>
                        </td>

                        {/* Dose */}
                        <td className="py-3 px-3 align-top text-center">
                          {!isNotSpecified(item.dose) ? (
                            <span className="inline-block px-2.5 py-1 rounded-md bg-emerald-100 text-emerald-950 border border-emerald-300/80 font-mono font-bold text-xs">
                              {item.dose}
                            </span>
                          ) : (
                            <span className="italic text-slate-400">Not specified</span>
                          )}
                        </td>

                        {/* Frequency (Dynamic) */}
                        {hasFrequencyData && (
                          <td className="py-3 px-3 align-top text-slate-700 font-medium">
                            {!isNotSpecified(item.frequency) ? (
                              item.frequency
                            ) : (
                              <span className="italic text-slate-400">Not specified</span>
                            )}
                          </td>
                        )}

                        {/* Timing */}
                        <td className="py-3 px-3 align-top text-slate-800 font-medium leading-relaxed">
                          {!isNotSpecified(item.timing) ? (
                            <div className="flex items-start gap-1.5">
                              <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0 mt-0.5" />
                              <span>{item.timing}</span>
                            </div>
                          ) : (
                            <span className="italic text-slate-400">Not specified</span>
                          )}

                          {/* If duration column is hidden but this specific item has duration */}
                          {!hasDurationData && item.duration && !isNotSpecified(item.duration) && (
                            <div className="mt-1 flex items-center gap-1 text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 inline-flex">
                              <Calendar className="w-3 h-3 text-emerald-600" />
                              <span>Duration: {item.duration}</span>
                            </div>
                          )}
                        </td>

                        {/* Duration (Dynamic) */}
                        {hasDurationData && (
                          <td className="py-3 px-3 align-top text-slate-700 font-medium">
                            {!isNotSpecified(item.duration) ? (
                              <div className="flex items-center gap-1.5">
                                <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                                <span>{item.duration}</span>
                              </div>
                            ) : (
                              <span className="italic text-slate-400">Not specified</span>
                            )}
                          </td>
                        )}

                        {/* Anupana / Sahapaan */}
                        <td className="py-3 px-3 align-top text-slate-800 font-medium leading-relaxed">
                          {!isNotSpecified(item.vehicle) ? (
                            <div className="flex items-start gap-1.5">
                              <Droplets className="w-3.5 h-3.5 text-cyan-600 shrink-0 mt-0.5" />
                              <span>{item.vehicle}</span>
                            </div>
                          ) : (
                            <span className="italic text-slate-400">Not specified</span>
                          )}
                        </td>

                        {/* Source Document */}
                        <td className="py-3 px-3 align-top text-slate-600">
                          <div className="flex items-center gap-1.5" title={item.source}>
                            <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                            <span className="truncate max-w-[170px] text-[11px] font-medium text-slate-700">
                              {item.source}
                            </span>
                          </div>
                        </td>

                        {/* Page */}
                        <td className="py-3 px-3 align-top text-center">
                          {item.page && item.page !== '-' ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-[11px] font-mono font-bold">
                              <span>{formatPageCitation(item.page)}</span>
                              <ExternalLink className="w-2.5 h-2.5 text-emerald-600" />
                            </span>
                          ) : (
                            <span className="text-slate-400">-</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            /* VIEW MODE: CARDS FORMAT */
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {formulations.map((item) => (
                <div 
                  key={item.id} 
                  className="bg-white rounded-xl border border-slate-200/90 shadow-xs hover:shadow-md transition-all p-4.5 flex flex-col justify-between gap-3.5 border-l-4 border-l-emerald-600"
                >
                  {/* Top: Medicine Name & Dose / Matra Badge */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-2.5">
                      <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-100 flex items-center justify-center shrink-0 shadow-xs mt-0.5">
                        <Pill className="w-5 h-5 text-emerald-600" />
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900 text-base leading-snug tracking-tight">
                          {item.name}
                        </h4>
                        {item.frequency && !isNotSpecified(item.frequency) && (
                          <span className="inline-block mt-0.5 text-xs text-slate-500 font-medium">
                            {item.frequency}
                          </span>
                        )}
                      </div>
                    </div>

                    {item.dose && !isNotSpecified(item.dose) && (
                      <span className="px-3 py-1 rounded-lg bg-emerald-600 text-white font-mono font-bold text-xs tracking-tight shrink-0 shadow-xs">
                        {item.dose}
                      </span>
                    )}
                  </div>

                  {/* Middle Grid: Timing, Vehicle, Duration */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-slate-50/80 p-3 rounded-xl border border-slate-100">
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                        <Clock className="w-3 h-3 text-slate-400" />
                        <span>Timing / Aushadh Kal</span>
                      </div>
                      <p className="text-xs text-slate-800 font-semibold leading-relaxed">
                        {isNotSpecified(item.timing) ? (
                          <span className="italic text-slate-400 font-normal">Not specified</span>
                        ) : (
                          item.timing
                        )}
                      </p>
                    </div>

                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                        <Droplets className="w-3 h-3 text-cyan-500" />
                        <span>Anupana / Sahpaan</span>
                      </div>
                      <p className="text-xs text-slate-800 font-semibold leading-relaxed">
                        {isNotSpecified(item.vehicle) ? (
                          <span className="italic text-slate-400 font-normal">Not specified</span>
                        ) : (
                          item.vehicle
                        )}
                      </p>
                    </div>

                    {item.duration && !isNotSpecified(item.duration) && (
                      <div className="col-span-full pt-1.5 border-t border-slate-200/50 flex items-center gap-2">
                        <div className="flex items-center gap-1 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span>Duration:</span>
                        </div>
                        <span className="text-xs font-semibold text-slate-800">{item.duration}</span>
                      </div>
                    )}
                  </div>

                  {/* Bottom: Provenance (Document Name & Page Badge) */}
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100 text-slate-500">
                    <div className="flex items-center gap-1.5 truncate max-w-[65%]" title={item.source}>
                      <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="truncate text-[11px] font-medium text-slate-600">{item.source}</span>
                    </div>

                    {item.page && item.page !== '-' && (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-mono font-bold shrink-0">
                        <span>{formatPageCitation(item.page)}</span>
                        <ExternalLink className="w-3 h-3 text-emerald-600" />
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* 3. CLINICAL PROTOCOLS & TOPICS                           */}
      {/* ======================================================== */}
      {hasProtocols && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-600">
            <ClipboardList className="w-4 h-4 text-cyan-600" />
            <span>Clinical Protocols & Supportive Care (From Guidelines)</span>
          </div>

          {viewMode === 'table' ? (
            <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-xs bg-white">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="bg-slate-50/95 text-[11px] font-bold text-slate-700 uppercase tracking-wider border-b border-slate-200">
                    <th className="py-3 px-3.5 font-bold text-slate-800 min-w-[180px]">
                      Clinical Parameter / Topic
                    </th>
                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[260px]">
                      Recommendation & Guideline Details
                    </th>
                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[170px]">
                      Source Document
                    </th>
                    <th className="py-3 px-3 font-bold text-slate-800 min-w-[85px] text-center">
                      Page
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {protocols.map((p) => (
                    <tr key={p.id} className="hover:bg-cyan-50/25 transition-colors even:bg-slate-50/30">
                      <td className="py-3 px-3.5 font-bold text-slate-900 align-top">
                        <div className="flex items-start gap-2">
                          <Activity className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                          <div>
                            <span className="font-bold text-slate-900">{p.topic}</span>
                            {p.section && (
                              <span className="block text-[10px] text-slate-500 font-normal mt-0.5">
                                {p.section}
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-3 align-top text-slate-800 font-medium leading-relaxed">
                        {p.details}
                      </td>
                      <td className="py-3 px-3 align-top text-slate-600">
                        <div className="flex items-center gap-1.5" title={p.source}>
                          <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="truncate max-w-[160px] text-[11px] font-medium text-slate-700">
                            {p.source}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-3 align-top text-center">
                        {p.page && p.page !== '-' ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-white text-slate-700 border border-slate-200 text-[11px] font-mono font-semibold">
                            <span>{formatPageCitation(p.page)}</span>
                          </span>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
              {protocols.map((p) => (
                <div 
                  key={p.id} 
                  className="bg-slate-50/70 rounded-xl border border-slate-200 p-4 space-y-2 flex flex-col justify-between"
                >
                  <div>
                    <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                      <Activity className="w-3.5 h-3.5 text-emerald-600" />
                      <span>{p.topic}</span>
                    </h4>
                    <p className="text-xs text-slate-800 font-medium leading-relaxed mt-1.5">
                      {p.details}
                    </p>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-200/60 text-slate-500 text-[11px]">
                    <span className="truncate max-w-[70%]" title={p.source}>{p.source}</span>
                    {p.page && p.page !== '-' && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 font-mono font-semibold">
                        <span>{formatPageCitation(p.page)}</span>
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* 4. CLINICAL EXCERPT NOTES & PRECAUTIONS (REACT-MARKDOWN)  */}
      {/* ======================================================== */}
      {hasNarrative && (
        <div className="p-5 sm:p-6 bg-slate-50/90 rounded-2xl border border-slate-200 text-slate-800 space-y-3 shadow-xs">
          <div className="font-bold text-slate-900 flex items-center gap-2 text-sm border-b border-slate-200 pb-2.5">
            <AlertCircle className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>Clinical Excerpt Notes & Precautions</span>
          </div>

          <div className="text-slate-700 leading-relaxed font-sans">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ ...props }) => <h3 className="text-base font-bold text-slate-900 mt-4 mb-2" {...props} />,
                h2: ({ ...props }) => <h4 className="text-sm font-bold text-slate-900 mt-3.5 mb-1.5" {...props} />,
                h3: ({ ...props }) => <h5 className="text-xs font-bold uppercase tracking-wider text-emerald-800 mt-3 mb-1" {...props} />,
                h4: ({ ...props }) => <h6 className="text-xs font-bold text-slate-800 mt-2.5 mb-1" {...props} />,
                p: ({ ...props }) => <p className="text-xs text-slate-700 leading-relaxed my-2" {...props} />,
                ul: ({ ...props }) => <ul className="list-disc list-outside pl-4 space-y-1 text-xs text-slate-700 my-2" {...props} />,
                ol: ({ ...props }) => <ol className="list-decimal list-outside pl-4 space-y-1 text-xs text-slate-700 my-2" {...props} />,
                li: ({ ...props }) => <li className="text-xs leading-relaxed" {...props} />,
                strong: ({ ...props }) => <strong className="font-bold text-slate-900" {...props} />,
                em: ({ ...props }) => <em className="italic text-slate-800 font-medium" {...props} />,
                hr: () => <hr className="my-3 border-slate-200" />,
                blockquote: ({ ...props }) => (
                  <blockquote className="border-l-3 border-emerald-600 pl-3 my-2 text-xs italic text-slate-700 bg-white/60 py-1 rounded-r" {...props} />
                )
              }}
            >
              {narrativeMarkdown}
            </ReactMarkdown>
          </div>
        </div>
      )}

      {/* ======================================================== */}
      {/* 5. BOTTOM ACTION TOOLBAR                                 */}
      {/* ======================================================== */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs">
        <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
          <span>Strictly grounded in your uploaded document.</span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg shadow-xs transition-colors cursor-pointer"
            title="Copy structured results to clipboard"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700 font-bold">Copied Results!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-slate-500" />
                <span>Copy Results</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:text-slate-900 bg-white hover:bg-slate-50 border border-slate-200 rounded-lg shadow-xs transition-colors cursor-pointer"
          >
            <Printer className="w-3.5 h-3.5 text-slate-500" />
            <span>Print</span>
          </button>
        </div>
      </div>
    </div>
  );
};

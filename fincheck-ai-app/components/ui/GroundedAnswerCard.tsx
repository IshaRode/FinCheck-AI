'use client';

import React, { useState } from 'react';
import {
  Sparkles,
  ShieldCheck,
  AlertTriangle,
  Copy,
  Check,
  BookOpen,
  ArrowDown,
  Info,
} from 'lucide-react';
import type { GenerateResponse } from '@/lib/generation';

interface GroundedAnswerCardProps {
  data: GenerateResponse;
  onSelectSource?: (sourceId: number) => void;
}

export function GroundedAnswerCard({ data, onSelectSource }: GroundedAnswerCardProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(data.answer);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCitationClick = (sourceId: number) => {
    if (onSelectSource) {
      onSelectSource(sourceId);
    }
    const element = document.getElementById(`source-card-${sourceId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      element.classList.add('ring-2', 'ring-blue-500', 'ring-offset-2');
      setTimeout(() => {
        element.classList.remove('ring-2', 'ring-blue-500', 'ring-offset-2');
      }, 2500);
    }
  };

  /**
   * Parses text and renders markdown bolding along with interactive [Source N] citation pills.
   */
  const renderFormattedLine = (line: string) => {
    // Split by citation pattern [Source N]
    const citationRegex = /(\[Source\s+\d+\])/g;
    const parts = line.split(citationRegex);

    return parts.map((part, pIdx) => {
      const match = part.match(/\[Source\s+(\d+)\]/i);
      if (match) {
        const sourceNum = parseInt(match[1], 10);
        return (
          <button
            key={`cite-${pIdx}`}
            onClick={() => handleCitationClick(sourceNum)}
            className="inline-flex items-center gap-1 mx-1 px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 hover:border-blue-300 transition-all cursor-pointer shadow-xs"
            title={`Jump to Source ${sourceNum} verification chunk`}
          >
            <BookOpen size={10} className="text-blue-500" />
            Source {sourceNum}
          </button>
        );
      }

      // Parse bold **text**
      const boldParts = part.split(/(\*\*[^*]+\*\*)/g);
      return boldParts.map((bPart, bIdx) => {
        if (bPart.startsWith('**') && bPart.endsWith('**')) {
          return (
            <strong key={`b-${bIdx}`} className="font-semibold text-gray-900">
              {bPart.slice(2, -2)}
            </strong>
          );
        }
        return bPart;
      });
    });
  };

  const renderContent = () => {
    const blocks = data.answer.split(/\n{2,}/).filter((b) => b.trim().length > 0);

    return (
      <div className="space-y-3 text-sm text-gray-800 leading-relaxed">
        {blocks.map((block, idx) => {
          const trimmed = block.trim();

          // Heading 3 or 4
          if (trimmed.startsWith('###')) {
            const hText = trimmed.replace(/^###\s*/, '');
            return (
              <h4 key={idx} className="text-sm font-bold text-gray-900 pt-2 pb-1 border-b border-gray-100">
                {renderFormattedLine(hText)}
              </h4>
            );
          }

          // Bullet point lists
          if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            const items = trimmed.split('\n').filter(Boolean);
            return (
              <ul key={idx} className="space-y-1.5 pl-1.5">
                {items.map((item, iIdx) => (
                  <li key={iIdx} className="flex items-start gap-2 text-gray-700">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 mt-2 flex-shrink-0" />
                    <span className="flex-1 leading-relaxed">
                      {renderFormattedLine(item.replace(/^[-*]\s+/, ''))}
                    </span>
                  </li>
                ))}
              </ul>
            );
          }

          // Regular paragraph
          return (
            <p key={idx} className="text-gray-700 leading-relaxed">
              {renderFormattedLine(trimmed)}
            </p>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-white border border-blue-100 rounded-xl shadow-sm overflow-hidden transition-all">
      {/* Card Header */}
      <div className="bg-gradient-to-r from-blue-50/80 via-indigo-50/40 to-white px-5 py-3.5 border-b border-blue-100/80 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
            <Sparkles size={15} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-gray-900">FinCheck AI Grounded Answer</h3>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                <ShieldCheck size={11} className="text-emerald-600" />
                {data.is_grounded ? 'Verified Grounded' : 'Caution Advised'}
              </span>
            </div>
            <p className="text-[11px] text-gray-500">
              Generated by <span className="font-mono text-gray-700 font-medium">{data.model}</span> strictly from retrieved bank documents
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {data.cited_source_ids.length > 0 && (
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200">
              <BookOpen size={11} />
              {data.cited_source_ids.length} Sources Cited
            </span>
          )}

          <button
            onClick={handleCopy}
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-medium text-gray-600 hover:text-gray-900 bg-white hover:bg-gray-50 border border-gray-200 transition-colors shadow-xs"
            title="Copy answer text"
          >
            {copied ? (
              <>
                <Check size={12} className="text-emerald-600" />
                <span className="text-emerald-600 font-semibold">Copied</span>
              </>
            ) : (
              <>
                <Copy size={12} />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Insufficient Context Warning Banner */}
      {data.is_insufficient_context && (
        <div className="mx-5 mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2.5 text-xs text-amber-900">
          <AlertTriangle size={16} className="text-amber-600 mt-0.5 flex-shrink-0" />
          <div className="space-y-1">
            <span className="font-semibold block text-amber-950">
              Insufficient Information in Bank Corpus
            </span>
            <span className="text-amber-800 block leading-relaxed">
              The verified internal documents do not contain definitive policy guidelines to fully answer this question. Advisors are advised not to extrapolate or assume statutory thresholds without consulting compliance.
            </span>
          </div>
        </div>
      )}

      {/* Main Answer Content */}
      <div className="px-5 py-4">
        {renderContent()}
      </div>

      {/* Footer Info & Quick Jump */}
      <div className="px-5 py-2.5 bg-gray-50/60 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500 flex-wrap gap-2">
        <div className="flex items-center gap-2 text-[11px]">
          <Info size={12} className="text-gray-400" />
          <span>Click any <span className="font-mono font-semibold text-blue-600">[Source N]</span> chip above to jump to the authoritative text passage.</span>
        </div>

        {data.sources.length > 0 && (
          <a
            href="#sources-section"
            className="inline-flex items-center gap-1 text-[11px] font-medium text-blue-600 hover:text-blue-800 transition-colors"
          >
            <span>Review all {data.sources.length} retrieved sources</span>
            <ArrowDown size={11} />
          </a>
        )}
      </div>
    </div>
  );
}

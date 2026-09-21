// components/ui/RetrievedSourceCard.tsx
'use client';

import React, { useState } from 'react';
import { FileText, Copy, Check, ChevronDown, ChevronUp, BookOpen, Layers, ShieldAlert, Sparkles, ArrowUpRight } from 'lucide-react';
import type { RetrievedChunk } from '@/lib/retrieval';

interface RetrievedSourceCardProps {
  chunk: RetrievedChunk;
}

function cleanPassageText(text: string): string {
  return text
    .replace(/<span[^>]*><\/span>/gi, '')
    .replace(/<span[^>]*>/gi, '')
    .replace(/<\/span>/gi, '')
    .replace(/!\[.*?\]\(.*?\)/gi, '')
    .replace(/[\ufffd\uFFFD]/g, '')
    .trim();
}

function parseMarkdownBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold text-gray-900">{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function FormattedPassage({ content }: { content: string }) {
  const cleaned = cleanPassageText(content);
  const blocks = cleaned.split(/\n{2,}/).filter((b) => b.trim().length > 0);

  return (
    <div className="space-y-2.5 text-xs text-gray-700 leading-relaxed">
      {blocks.map((block, idx) => {
        const trimmed = block.trim();

        // 1. Heading detection (e.g. ### **Annex**, #### **I. Paragraph 10**)
        if (trimmed.startsWith('#')) {
          const headingText = trimmed.replace(/^#+\s*/, '').replace(/^\*\*/, '').replace(/\*\*$/, '');
          return (
            <div
              key={idx}
              className="font-semibold text-gray-900 text-xs tracking-tight pt-1.5 pb-0.5 border-b border-gray-200/60 flex items-center gap-1.5"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600"></span>
              <span>{headingText}</span>
            </div>
          );
        }

        // 2. Caution or statutory notice callout
        if (trimmed.toLowerCase().includes('caution: rbi never') || trimmed.toLowerCase().startsWith('"caution:')) {
          return (
            <div
              key={idx}
              className="p-2.5 bg-amber-50/70 border border-amber-200/80 rounded-lg text-[11px] text-amber-900 flex items-start gap-2"
            >
              <ShieldAlert size={14} className="text-amber-600 flex-shrink-0 mt-0.5" />
              <span>{trimmed.replace(/^"/, '').replace(/"$/, '')}</span>
            </div>
          );
        }

        // 3. Official signatory footer (e.g. "Yours faithfully, ... Chief General Manager")
        if (trimmed.toLowerCase().startsWith('yours faithfully') || trimmed.toLowerCase().includes('chief general manager')) {
          return (
            <div key={idx} className="p-2 bg-gray-50 border border-gray-100 rounded text-[11px] text-gray-500 italic">
              {trimmed.split('\n').map((line, lIdx) => (
                <div key={lIdx}>{line}</div>
              ))}
            </div>
          );
        }

        // 4. Bullet points list
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          const items = trimmed.split('\n').filter(Boolean);
          return (
            <ul key={idx} className="list-disc list-inside space-y-1 pl-1">
              {items.map((item, iIdx) => (
                <li key={iIdx} className="text-gray-700">
                  {parseMarkdownBold(item.replace(/^[-*]\s+/, ''))}
                </li>
              ))}
            </ul>
          );
        }

        // 5. Regular paragraph
        return (
          <p key={idx} className="text-gray-700">
            {parseMarkdownBold(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

export function RetrievedSourceCard({ chunk }: RetrievedSourceCardProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const cleaned = cleanPassageText(chunk.content);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(cleaned);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isLongContent = cleaned.length > 340;
  const displayContent = isLongContent && !isExpanded
    ? `${cleaned.slice(0, 340)}...`
    : cleaned;

  const datasetLabel = chunk.source_dataset === 'rbi' ? 'RBI Circular' : 'Indian Finance';
  const similarityPct = Math.round(chunk.similarity * 100);

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:border-blue-200 transition-colors">
      {/* Top Header */}
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Rank Badge */}
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
            Source {chunk.rank}
          </span>

          {/* Dataset Tag */}
          <span
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border ${
              chunk.source_dataset === 'rbi'
                ? 'bg-purple-50 text-purple-700 border-purple-100'
                : 'bg-emerald-50 text-emerald-700 border-emerald-100'
            }`}
          >
            <BookOpen size={10} />
            {datasetLabel}
          </span>

          {/* Rank Movement Indicator if reranked from a different vector rank */}
          {Boolean(chunk.initial_rank && chunk.initial_rank !== chunk.rank) && (
            <span
              className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[10px] font-medium border ${
                chunk.initial_rank! > chunk.rank
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-gray-50 text-gray-600 border-gray-200'
              }`}
              title={`Promoted by NVIDIA Reranker from initial vector rank #${chunk.initial_rank} to #${chunk.rank}`}
            >
              <ArrowUpRight size={10} className={chunk.initial_rank! > chunk.rank ? 'text-amber-600' : 'text-gray-400 rotate-90'} />
              <span>Vector #{chunk.initial_rank}</span>
            </span>
          )}
        </div>

        {/* Scores: Rerank Score & Similarity Score */}
        <div className="flex items-center gap-2 flex-shrink-0 flex-wrap justify-end">
          {chunk.rerank_score != null && (
            <div className="flex items-center gap-1">
              <span className="text-[11px] font-medium text-indigo-600 flex items-center gap-0.5">
                <Sparkles size={11} className="text-indigo-500" />
                Rerank:
              </span>
              <span
                className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-semibold bg-indigo-50 text-indigo-700 border border-indigo-100"
                title={chunk.rerank_logit != null ? `Logit: ${chunk.rerank_logit > 0 ? `+${chunk.rerank_logit.toFixed(3)}` : chunk.rerank_logit.toFixed(3)}` : undefined}
              >
                {chunk.rerank_logit != null
                  ? (chunk.rerank_logit > 0 ? `+${chunk.rerank_logit.toFixed(2)}` : chunk.rerank_logit.toFixed(2))
                  : `${Math.round(chunk.rerank_score * 100)}%`}
              </span>
            </div>
          )}

          <div className="flex items-center gap-1.5">
            <span className="text-[11px] font-medium text-gray-500">Vector Sim:</span>
            <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium bg-gray-100 text-gray-700">
              {chunk.similarity.toFixed(4)}
            </span>
            <span className="text-[10px] text-gray-400">({similarityPct}%)</span>
          </div>
        </div>
      </div>

      {/* Document Title */}
      <div className="flex items-start gap-2 mb-2">
        <FileText size={15} className="text-gray-400 mt-0.5 flex-shrink-0" />
        <h4 className="text-sm font-semibold text-gray-900 leading-snug">
          {chunk.document_name}
        </h4>
      </div>

      {/* Retrieved Passage with Clean Formatting */}
      <div className="bg-gray-50/70 border border-gray-100 rounded-lg p-3.5 my-2.5">
        <FormattedPassage content={displayContent} />
      </div>

      {/* Footer Controls / Metadata */}
      <div className="flex items-center justify-between pt-2 text-xs text-gray-400 border-t border-gray-100">
        <div className="flex items-center gap-2 text-[11px]">
          <span className="flex items-center gap-1">
            <Layers size={11} />
            <code className="text-[10px] text-gray-500">{chunk.chunk_id}</code>
          </span>
          {Boolean(chunk.metadata?.section) && (
            <span className="hidden sm:inline text-gray-400">
              · {String(chunk.metadata?.section)}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {isLongContent && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 font-medium transition-colors"
            >
              {isExpanded ? (
                <>
                  Show less <ChevronUp size={12} />
                </>
              ) : (
                <>
                  Read full passage <ChevronDown size={12} />
                </>
              )}
            </button>
          )}

          <button
            onClick={handleCopy}
            className="flex items-center gap-1 text-[11px] text-gray-500 hover:text-gray-700 transition-colors ml-2"
            title="Copy passage to clipboard"
          >
            {copied ? (
              <>
                <Check size={12} className="text-emerald-600" />
                <span className="text-emerald-600 font-medium">Copied</span>
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
    </div>
  );
}

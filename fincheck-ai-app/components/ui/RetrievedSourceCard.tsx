// components/ui/RetrievedSourceCard.tsx
'use client';

import React, { useState } from 'react';
import { FileText, Copy, Check, ChevronDown, ChevronUp, BookOpen, Layers } from 'lucide-react';
import type { RetrievedChunk } from '@/lib/retrieval';

interface RetrievedSourceCardProps {
  chunk: RetrievedChunk;
}

export function RetrievedSourceCard({ chunk }: RetrievedSourceCardProps) {
  const [copied, setCopied] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(chunk.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isLongContent = chunk.content.length > 320;
  const displayContent = isLongContent && !isExpanded
    ? `${chunk.content.slice(0, 320)}...`
    : chunk.content;

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
        </div>

        {/* Subtle Similarity Score */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <span className="text-[11px] font-medium text-gray-500">Similarity:</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[11px] font-mono font-medium bg-gray-100 text-gray-700">
            {chunk.similarity.toFixed(4)}
          </span>
          <span className="text-[10px] text-gray-400">({similarityPct}%)</span>
        </div>
      </div>

      {/* Document Title */}
      <div className="flex items-start gap-2 mb-2">
        <FileText size={15} className="text-gray-400 mt-0.5 flex-shrink-0" />
        <h4 className="text-sm font-semibold text-gray-900 leading-snug">
          {chunk.document_name}
        </h4>
      </div>

      {/* Retrieved Passage */}
      <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 my-2.5 text-xs text-gray-700 leading-relaxed whitespace-pre-line font-normal">
        {displayContent}
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
              className="flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 transition-colors"
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

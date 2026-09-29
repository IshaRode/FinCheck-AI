'use client';
// app/saved-answers/page.tsx
import React, { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/ui/Card';
import { FileText, Bookmark, ExternalLink, Search } from 'lucide-react';
import { savedAnswers } from '@/lib/mock-data';
import { getSavedAnswers, removeSavedAnswer, type StoredSavedAnswer } from '@/lib/saved-answers';
import { sortSavedAnswers } from '@/lib/saved-answer-helpers';

function parseMarkdownBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

type SavedAnswerSort = 'newest' | 'oldest' | 'document';

export default function SavedAnswersPage() {
  const router = useRouter();
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set(savedAnswers.map((s) => s.id)));
  const [localAnswers, setLocalAnswers] = useState<StoredSavedAnswer[]>(() => getSavedAnswers());
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState<SavedAnswerSort>('newest');

  const toggleSave = (id: string) => {
    setSavedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filtered = savedAnswers.filter(
    (a) =>
      search === '' ||
      a.question.toLowerCase().includes(search.toLowerCase()) ||
      a.sourceDocument.toLowerCase().includes(search.toLowerCase())
  );

  const visible = useMemo(
    () => sortSavedAnswers(filtered.filter((a) => savedIds.has(a.id)), sortBy),
    [filtered, savedIds, sortBy]
  );

  const filteredLocalAnswers = useMemo(
    () =>
      sortSavedAnswers(
        localAnswers.filter(
          (answer) =>
            search === '' ||
            answer.question.toLowerCase().includes(search.toLowerCase()) ||
            answer.data.sources.some((source) => source.document_name.toLowerCase().includes(search.toLowerCase()))
        ),
        sortBy
      ),
    [localAnswers, search, sortBy]
  );

  const removeLocalAnswer = (id: string) => {
    removeSavedAnswer(id);
    setLocalAnswers((previous) => previous.filter((answer) => answer.id !== id));
  };

  const clearAllSaved = () => {
    setSavedIds(new Set());
    setLocalAnswers([]);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem('fincheck-saved-answers', JSON.stringify([]));
    }
  };

  return (
    <MainLayout title="Saved Answers" subtitle="Your bookmarked AI responses">
      <div className="px-7 py-7">
        {/* Header row */}
        <div className="flex items-center justify-between mb-5">
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search saved answers..."
              className="pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg text-gray-700 placeholder-gray-400 focus:outline-none focus:border-blue-400 transition-colors w-56 bg-white"
              aria-label="Search saved answers"
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-[10px] uppercase tracking-[0.15em] text-gray-400">
              <span>Sort</span>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SavedAnswerSort)}
                className="appearance-none border border-gray-200 rounded-lg bg-white px-2 py-1.5 text-[11px] text-gray-700 uppercase tracking-normal focus:outline-none focus:border-blue-400"
                aria-label="Sort saved answers"
              >
                <option value="newest">Newest</option>
                <option value="oldest">Oldest</option>
                <option value="document">Document</option>
              </select>
            </label>
            <button
              type="button"
              onClick={clearAllSaved}
              disabled={visible.length + filteredLocalAnswers.length === 0}
              className="px-2.5 py-1.5 text-[11px] font-medium rounded-lg border border-red-200 text-red-600 bg-red-50 hover:bg-red-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Clear all
            </button>
          </div>

          <span className="text-xs text-gray-400">{visible.length + filteredLocalAnswers.length} saved</span>
        </div>

        {/* Cards */}
        {visible.length === 0 && filteredLocalAnswers.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
              <Bookmark size={20} className="text-gray-400" />
            </div>
            <h3 className="text-sm font-semibold text-gray-600 mb-1">No saved answers</h3>
            <p className="text-xs text-gray-400 max-w-xs">
              Answers you save from Ask FinCheck AI will appear here.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredLocalAnswers.map((answer) => (
              <Card key={answer.id} padding="md">
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">{answer.question}</h3>
                    <p className="text-sm text-gray-600 leading-relaxed mb-3 line-clamp-2">
                      {parseMarkdownBold(answer.data.answer)}
                    </p>
                    <div className="flex items-center gap-3 flex-wrap">
                      <div className="flex items-center gap-1.5">
                        <FileText size={12} className="text-blue-500" />
                        <span className="text-xs text-gray-700 font-medium">
                          {answer.data.sources[0]?.document_name ?? 'No source document'}
                        </span>
                      </div>
                      <span className="text-gray-300">·</span>
                      <span className="text-xs text-gray-400">
                        Saved {new Date(answer.savedAt).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => router.push(`/ask?q=${encodeURIComponent(answer.question)}`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-gray-200 rounded-lg text-gray-700 hover:border-blue-300 hover:text-blue-600 transition-colors"
                      aria-label={`View full answer for: ${answer.question}`}
                    >
                      <ExternalLink size={12} />
                      View
                    </button>
                    <button
                      onClick={() => removeLocalAnswer(answer.id)}
                      aria-label="Remove bookmark"
                      className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-blue-600 hover:border-red-300 hover:text-red-500 transition-colors"
                    >
                      <Bookmark size={13} className="fill-blue-600 hover:fill-none" />
                    </button>
                  </div>
                </div>
              </Card>
            ))}
            {visible.map((answer) => (
              <Card key={answer.id} padding="md">
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    {/* Question */}
                    <h3 className="text-sm font-semibold text-gray-900 mb-2">{answer.question}</h3>

                    {/* Answer preview */}
                    <p className="text-sm text-gray-600 leading-relaxed mb-3 line-clamp-2">
                      {parseMarkdownBold(answer.answerPreview)}
                    </p>

                    {/* Source + meta */}
                    <div className="flex items-center gap-3 flex-wrap">
                      <div className="flex items-center gap-1.5">
                        <FileText size={12} className="text-blue-500" />
                        <span className="text-xs text-gray-700 font-medium">
                          {answer.sourceDocument}
                        </span>
                        <span className="text-xs text-gray-400">{answer.documentVersion}</span>
                      </div>
                      <span className="text-gray-300">·</span>
                      <span className="text-xs text-gray-400">Saved {answer.savedDate}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => router.push(`/ask?q=${encodeURIComponent(answer.question)}`)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-gray-200 rounded-lg text-gray-700 hover:border-blue-300 hover:text-blue-600 transition-colors"
                      aria-label={`View full answer for: ${answer.question}`}
                    >
                      <ExternalLink size={12} />
                      View
                    </button>
                    <button
                      onClick={() => toggleSave(answer.id)}
                      aria-label="Remove bookmark"
                      className="w-7 h-7 rounded-lg border border-gray-200 flex items-center justify-center text-blue-600 hover:border-red-300 hover:text-red-500 transition-colors"
                    >
                      <Bookmark size={13} className="fill-blue-600 hover:fill-none" />
                    </button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </MainLayout>
  );
}

'use client';
// app/recent-questions/page.tsx
import React, { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Search, FileText, ArrowRight, ChevronDown, ChevronUp, MessageSquare } from 'lucide-react';
import { questions, questionStats } from '@/lib/mock-data';

type FilterKey = 'All' | 'Answered' | 'Insufficient';

function parseMarkdownBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

export default function RecentQuestionsPage() {
  const router = useRouter();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<FilterKey>('All');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    return questions.filter((q) => {
      const matchSearch =
        search === '' ||
        q.text.toLowerCase().includes(search.toLowerCase()) ||
        q.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));
      const matchFilter =
        filter === 'All' ||
        (filter === 'Answered' && q.status === 'Answered') ||
        (filter === 'Insufficient' && q.status === 'Insufficient Info');
      return matchSearch && matchFilter;
    });
  }, [search, filter]);

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  return (
    <MainLayout title="Recent Questions" subtitle="Your question history">
      <div className="px-7 py-7">
        {/* KPI Cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-white border border-gray-200 rounded-xl p-5">
            <div className="text-3xl font-bold text-blue-600 mb-0.5">{questionStats.total}</div>
            <div className="text-sm text-gray-500">Total questions</div>
          </div>
          <div className="bg-white border border-green-200 rounded-xl p-5">
            <div className="text-3xl font-bold text-emerald-600 mb-0.5">{questionStats.answered}</div>
            <div className="text-sm text-gray-500">Answered</div>
          </div>
          <div className="bg-white border border-amber-200 rounded-xl p-5">
            <div className="text-3xl font-bold text-amber-600 mb-0.5">{questionStats.insufficientInfo}</div>
            <div className="text-sm text-gray-500">Insufficient info</div>
          </div>
        </div>

        {/* Search + Filter */}
        <Card padding="none">
          <div className="px-5 pt-4 pb-0 flex items-center gap-3 flex-wrap">
            <div className="relative">
              <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search questions..."
                className="pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg text-gray-700 placeholder-gray-400 focus:outline-none focus:border-blue-400 transition-colors w-52 bg-gray-50 focus:bg-white"
                aria-label="Search questions"
              />
            </div>

            {/* Filter buttons */}
            <div className="flex items-center rounded-lg border border-gray-200 overflow-hidden">
              {(['All', 'Answered', 'Insufficient'] as FilterKey[]).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                    filter === f
                      ? 'bg-gray-900 text-white'
                      : 'bg-white text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            <span className="ml-auto text-xs text-gray-400">{filtered.length} questions</span>
          </div>

          {/* Accordion list */}
          <div className="mt-3 divide-y divide-gray-100">
            {filtered.length > 0 ? (
              filtered.map((q) => {
                const isExpanded = expandedId === q.id;
                return (
                  <div key={q.id}>
                    {/* Row header */}
                    <button
                      className="w-full text-left px-5 py-4 hover:bg-gray-50 transition-colors flex items-start gap-3"
                      onClick={() => toggleExpand(q.id)}
                      aria-expanded={isExpanded}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-gray-900 font-medium mb-1.5">{q.text}</p>
                        <div className="flex items-center gap-2 flex-wrap">
                          <Badge variant={q.status === 'Answered' ? 'answered' : 'insufficient'} />
                          {q.tags.map((tag) => (
                            <span
                              key={tag}
                              className="px-2 py-0.5 text-[11px] bg-gray-100 text-gray-600 rounded-full"
                            >
                              {tag}
                            </span>
                          ))}
                          <span className="text-xs text-gray-400 ml-auto">
                            {q.date} · {q.time}
                          </span>
                        </div>
                      </div>
                      <span className="text-gray-400 mt-0.5 flex-shrink-0">
                        {isExpanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                      </span>
                    </button>

                    {/* Expanded answer */}
                    {isExpanded && (
                      <div className="px-5 pb-5 bg-gray-50 border-t border-gray-100">
                        <div className="pt-4">
                          {/* Answer text */}
                          <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm mb-3">
                            <div className="flex items-center gap-2 mb-3">
                              <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                                <MessageSquare size={11} className="text-white" />
                              </div>
                              <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">FinCheck AI Answer</span>
                            </div>
                            {q.answer ? (
                              <div className="text-sm text-gray-800 leading-relaxed space-y-2">
                                {q.answer.split('\n\n').filter(Boolean).map((para, i) => (
                                  <p key={i}>{parseMarkdownBold(para)}</p>
                                ))}
                              </div>
                            ) : (
                              <p className="text-sm text-gray-400 italic">No answer available.</p>
                            )}
                          </div>

                          {/* Sources */}
                          {q.sources && q.sources.length > 0 && (
                            <div className="mb-3">
                              <p className="text-[10px] font-semibold tracking-widest text-gray-400 uppercase flex items-center gap-1.5 mb-2">
                                <FileText size={11} />
                                Sources ({q.sources.length})
                              </p>
                              <div className="space-y-1.5">
                                {q.sources.map((src) => (
                                  <div
                                    key={src.id}
                                    className="flex items-center gap-2.5 px-3 py-2 bg-blue-50 border border-blue-100 rounded-lg"
                                  >
                                    <div className="w-6 h-6 rounded bg-blue-100 flex items-center justify-center flex-shrink-0">
                                      <FileText size={11} className="text-blue-600" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <span className="text-xs font-medium text-gray-900">{src.documentName}</span>
                                      <span className="text-xs text-gray-500 ml-1.5">{src.version}</span>
                                      <p className="text-[11px] text-gray-400 mt-0.5">
                                        {src.pageRef} · {src.section}
                                      </p>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Re-ask action */}
                          <button
                            onClick={() => router.push(`/ask?q=${encodeURIComponent(q.text)}`)}
                            className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors"
                            aria-label={`Re-ask: ${q.text}`}
                          >
                            <ArrowRight size={12} />
                            Re-ask in FinCheck AI
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="py-12 text-center text-sm text-gray-400">
                No questions match your filters.
              </div>
            )}
          </div>
        </Card>
      </div>
    </MainLayout>
  );
}

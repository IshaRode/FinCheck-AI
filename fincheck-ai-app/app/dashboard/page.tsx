'use client';
// app/dashboard/page.tsx
import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/ui/Card';
import { KpiCard } from '@/components/ui/KpiCard';
import { Badge } from '@/components/ui/Badge';
import {
  Search,
  ArrowRight,
  FileText,
  BookOpen,
  Receipt,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import { quickQuestions, questions, knowledgeBaseStats } from '@/lib/mock-data';

export default function DashboardPage() {
  const router = useRouter();
  const [question, setQuestion] = useState('');

  const handleAskAI = () => {
    const q = question.trim();
    if (q) {
      router.push(`/ask?q=${encodeURIComponent(q)}`);
    } else {
      router.push('/ask');
    }
  };

  const handleQuickQuestion = (q: string) => {
    router.push(`/ask?q=${encodeURIComponent(q)}`);
  };

  const recentQuestions = questions.slice(0, 4);

  return (
    <MainLayout title="Dashboard" subtitle="FinCheck AI · Wealth Division">
      <div className="px-7 py-7">
        {/* Greeting */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Good morning, Isha 👋</h2>
          <p className="text-gray-500 text-sm mt-1">
            Find trusted answers from approved financial documents.
          </p>
        </div>

        {/* Ask FinCheck AI Card */}
        <Card className="mb-7" padding="lg">
          <div className="flex items-start gap-3 mb-4">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center flex-shrink-0">
              <Search size={16} className="text-blue-500" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-gray-900">Ask FinCheck AI</h3>
              <p className="text-xs text-gray-500 mt-0.5">Answers are grounded in approved bank documents</p>
            </div>
          </div>

          {/* Search input */}
          <div className="flex items-center gap-3 mb-4">
            <div className="flex-1 relative">
              <Search size={14} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAskAI()}
                placeholder="Ask a question about products, policies, tax rules or eligibility..."
                className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-lg text-gray-700 placeholder-gray-400 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-colors bg-gray-50 focus:bg-white"
                aria-label="Ask a financial question"
              />
            </div>
            <button
              id="dashboard-ask-ai-btn"
              onClick={handleAskAI}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold text-white whitespace-nowrap transition-colors hover:opacity-90"
              style={{ backgroundColor: '#0f1629' }}
            >
              <ArrowRight size={15} />
              Ask AI
            </button>
          </div>

          {/* Quick questions */}
          <div>
            <p className="text-[10px] font-semibold tracking-widest text-gray-400 uppercase mb-2">
              Quick Questions
            </p>
            <div className="flex flex-wrap gap-2">
              {quickQuestions.map((q) => (
                <button
                  key={q}
                  onClick={() => handleQuickQuestion(q)}
                  className="px-3 py-1.5 text-xs border border-gray-200 rounded-full text-gray-700 hover:border-blue-300 hover:text-blue-700 hover:bg-blue-50 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </Card>

        {/* Bottom row: KB Overview + Recent Questions */}
        <div className="grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-6">
          {/* Knowledge Base Overview */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-900">Knowledge Base Overview</h3>
              <button
                onClick={() => router.push('/knowledge-base')}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-0.5 transition-colors"
              >
                View all <ChevronRight size={13} />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <KpiCard
                value={knowledgeBaseStats.total}
                label="Approved Documents"
                icon={<FileText size={16} />}
                variant="default"
              />
              <KpiCard
                value={knowledgeBaseStats.currentPolicies}
                label="Current Policies"
                icon={<BookOpen size={16} />}
                variant="green"
              />
              <KpiCard
                value={knowledgeBaseStats.productBrochures}
                label="Product Brochures"
                icon={<Receipt size={16} />}
                variant="default"
              />
              <KpiCard
                value={knowledgeBaseStats.taxCompliance}
                label="Tax &amp; Compliance"
                icon={<ShieldCheck size={16} />}
                variant="amber"
              />
            </div>
          </div>

          {/* Recent Questions */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-900">Recent Questions</h3>
              <button
                onClick={() => router.push('/recent-questions')}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-0.5 transition-colors"
              >
                View all <ChevronRight size={13} />
              </button>
            </div>
            <Card padding="none">
              <ul className="divide-y divide-gray-100">
                {recentQuestions.map((q) => (
                  <li
                    key={q.id}
                    className="px-4 py-3 hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => router.push(`/recent-questions`)}
                  >
                    <p className="text-sm text-gray-800 leading-snug mb-1.5 line-clamp-2">
                      {q.text}
                    </p>
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge
                        variant={q.status === 'Answered' ? 'answered' : 'insufficient'}
                      />
                      {q.sourceCount > 0 && (
                        <span className="text-xs text-gray-400">
                          {q.sourceCount} {q.sourceCount === 1 ? 'source' : 'sources'}
                        </span>
                      )}
                      <span className="text-xs text-gray-400 ml-auto">{q.date}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

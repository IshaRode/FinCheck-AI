'use client';
// app/ask/page.tsx
import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import {
  Send,
  Loader2,
  MessageSquare,
  Search,
  AlertCircle,
  Database,
  Info,
  RotateCcw,
  Sparkles,
} from 'lucide-react';
import { retrieveSources, type RetrievedChunk } from '@/lib/retrieval';
import { generateAnswer, type GenerateResponse } from '@/lib/generation';
import { RetrievedSourceCard } from '@/components/ui/RetrievedSourceCard';
import { GroundedAnswerCard } from '@/components/ui/GroundedAnswerCard';

interface UserMessage {
  id: string;
  type: 'user';
  text: string;
  timestamp: string;
}

interface AnswerResultMessage {
  id: string;
  type: 'answer';
  question: string;
  timestamp: string;
  data: GenerateResponse;
}

interface RetrievalResultMessage {
  id: string;
  type: 'sources';
  question: string;
  timestamp: string;
  chunks: RetrievedChunk[];
}

interface ErrorMessage {
  id: string;
  type: 'error';
  question: string;
  timestamp: string;
  error: string;
}

type ChatMessage = UserMessage | AnswerResultMessage | RetrievalResultMessage | ErrorMessage;

const bankingQuickQuestions = [
  'What are the RBI rules regarding KYC requirements?',
  'What precautions should customers take to avoid digital arrest scams?',
  'What are the rules related to bank account nominee?',
  'What is the threshold for high-value suspicious transaction reporting?',
];

function RetrievedSourcesGroup({ message }: { message: RetrievalResultMessage }) {
  return (
    <div className="max-w-3xl w-full">
      <div className="flex items-start gap-3 mb-1">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm">
          <Database size={15} className="text-white" />
        </div>
        <div className="flex-1 space-y-3">
          {/* Header Card */}
          <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
            <div className="flex items-center justify-between gap-2 flex-wrap mb-1.5">
              <div className="flex items-center gap-2">
                <Search size={15} className="text-blue-600" />
                <h3 className="text-sm font-semibold text-gray-900">Retrieved Sources</h3>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-blue-100 text-blue-800">
                  {message.chunks.length} Chunks Matched
                </span>
              </div>
              <span className="text-[11px] text-gray-400 font-mono">
                {message.timestamp}
              </span>
            </div>

            <p className="text-xs text-gray-500 leading-relaxed">
              Below are the top relevant passages retrieved using two-stage financial RAG:
              <strong className="text-gray-700 font-medium"> NVIDIA Nemotron embeddings (2048-dim)</strong>,
              <strong className="text-gray-700 font-medium"> Supabase pgvector (HNSW)</strong>, and cross-encoder
              <strong className="text-gray-700 font-medium"> NVIDIA Nemotron Reranking</strong>.
            </p>

            {/* Subtle Phase notice */}
            <div className="mt-3 flex items-start gap-2 p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-[11px] text-amber-800">
              <Info size={14} className="text-amber-600 mt-0.5 flex-shrink-0" />
              <span>
                <strong>Semantic Retrieval Phase:</strong> The authoritative source passages below are displayed directly from the knowledge corpus. AI Answer generation will be enabled in Phase 6.
              </span>
            </div>
          </div>

          {/* Empty result handling */}
          {message.chunks.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-xl p-6 text-center shadow-sm">
              <Search size={24} className="mx-auto text-gray-400 mb-2" />
              <h4 className="text-sm font-medium text-gray-800">No matching sources found</h4>
              <p className="text-xs text-gray-500 mt-1">
                No document chunks exceeded the similarity threshold. Please try rephrasing your question.
              </p>
            </div>
          ) : (
            /* Chunks list */
            <div className="space-y-2.5">
              {message.chunks.map((chunk) => (
                <RetrievedSourceCard key={chunk.chunk_id} chunk={chunk} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AnswerResultGroup({ message }: { message: AnswerResultMessage }) {
  const [showSources, setShowSources] = useState(true);

  return (
    <div className="max-w-3xl w-full">
      <div className="flex items-start gap-3 mb-1">
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5 shadow-sm text-white">
          <Sparkles size={15} />
        </div>
        <div className="flex-1 space-y-4">
          {/* Grounded Answer Card */}
          <GroundedAnswerCard data={message.data} />

          {/* Collapsible Verified Sources Section */}
          {message.data.sources && message.data.sources.length > 0 && (
            <div id="sources-section" className="space-y-3 pt-2">
              <div className="flex items-center justify-between px-1">
                <div className="flex items-center gap-2">
                  <Database size={13} className="text-blue-600" />
                  <h4 className="text-xs font-semibold text-gray-800 tracking-tight">
                    Retrieved Bank Source Chunks ({message.data.sources.length})
                  </h4>
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                    Two-stage pgvector + NVIDIA Reranked
                  </span>
                </div>
                <button
                  onClick={() => setShowSources(!showSources)}
                  className="text-[11px] font-medium text-blue-600 hover:text-blue-800 transition-colors cursor-pointer"
                >
                  {showSources ? 'Hide source passages' : `Show ${message.data.sources.length} source passages`}
                </button>
              </div>

              {showSources && (
                <div className="space-y-2.5">
                  {message.data.sources.map((chunk) => (
                    <RetrievedSourceCard key={chunk.chunk_id} chunk={chunk} />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ErrorCard({
  message,
  onRetry,
}: {
  message: ErrorMessage;
  onRetry: (question: string) => void;
}) {
  return (
    <div className="max-w-2xl">
      <div className="flex items-start gap-3 mb-1">
        <div className="w-8 h-8 rounded-full bg-red-100 border border-red-200 flex items-center justify-center flex-shrink-0 mt-0.5">
          <AlertCircle size={16} className="text-red-600" />
        </div>
        <div className="flex-1 bg-white border border-red-200 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-sm font-semibold text-red-800">Retrieval Service Error</h4>
            <span className="text-[11px] text-gray-400">{message.timestamp}</span>
          </div>
          <p className="text-xs text-gray-600 leading-relaxed mb-3">
            {message.error}
          </p>
          <button
            onClick={() => onRetry(message.question)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-red-50 text-red-700 border border-red-200 hover:bg-red-100 transition-colors"
          >
            <RotateCcw size={12} />
            Retry Query
          </button>
        </div>
      </div>
    </div>
  );
}

function AskPageContent() {
  const searchParams = useSearchParams();
  const initialQuestion = searchParams.get('q') ?? '';
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const initialSentRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSend = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || isLoading) return;

    const timeStr = new Date().toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });

    const userMsg: UserMessage = {
      id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      type: 'user',
      text: q,
      timestamp: timeStr,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await generateAnswer(q);
      const resultMsg: AnswerResultMessage = {
        id: `ans-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        type: 'answer',
        question: q,
        timestamp: new Date().toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        }),
        data: response,
      };
      setMessages((prev) => [...prev, resultMsg]);
    } catch (err: unknown) {
      const errorMsg: ErrorMessage = {
        id: `err-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        type: 'error',
        question: q,
        timestamp: new Date().toLocaleTimeString('en-US', {
          hour: '2-digit',
          minute: '2-digit',
        }),
        error: err instanceof Error ? err.message : 'Failed to generate answer from backend.',
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuestion && !initialSentRef.current) {
      initialSentRef.current = true;
      handleSend(initialQuestion);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuestion]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0 && !isLoading;

  return (
    <MainLayout title="Ask FinCheck AI" subtitle="Grounded in approved bank documents">
      <div className="flex flex-col" style={{ height: 'calc(100vh - 60px)' }}>
        {/* Top bar inside page */}
        <div className="px-7 pt-5 pb-3 flex items-center justify-between flex-shrink-0 border-b border-gray-100 bg-white">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center flex-shrink-0">
              <MessageSquare size={15} className="text-blue-500" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-900">Ask FinCheck AI</h2>
              <p className="text-xs text-gray-500">
                Semantic retrieval across 7,301 chunks & Gemini grounded answer generation
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs text-gray-600 font-medium">pgvector, NVIDIA Reranker & Gemini active</span>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-7 py-4 space-y-6">
          {isEmpty && (
            <div className="flex flex-col items-center justify-center h-full text-center py-10">
              <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-3 shadow-sm">
                <Search size={22} className="text-blue-600" />
              </div>
              <h3 className="text-base font-semibold text-gray-800 mb-1">
                Ask a banking or regulatory question
              </h3>
              <p className="text-xs text-gray-500 max-w-md mb-6 leading-relaxed">
                Query across 7,301 embedded chunks from RBI Circulars and Indian Financial Inclusion documents for verified, grounded answers with citations.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-xl">
                {bankingQuickQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="px-3.5 py-2 text-xs border border-gray-200 bg-white rounded-lg text-gray-700 hover:border-blue-400 hover:text-blue-700 hover:bg-blue-50 shadow-sm transition-all cursor-pointer"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={`${msg.id}-${idx}`}>
              {msg.type === 'user' ? (
                /* User bubble */
                <div className="flex justify-end">
                  <div className="max-w-lg">
                    <div
                      className="px-4 py-3 rounded-2xl text-sm text-white leading-relaxed shadow-sm"
                      style={{ backgroundColor: '#0f1629' }}
                    >
                      {msg.text}
                    </div>
                    <p className="text-[10px] text-gray-400 text-right mt-1">{msg.timestamp}</p>
                  </div>
                </div>
              ) : msg.type === 'answer' ? (
                /* Grounded Answer with collapsible sources */
                <AnswerResultGroup message={msg} />
              ) : msg.type === 'sources' ? (
                /* Retrieved sources group fallback */
                <RetrievedSourcesGroup message={msg} />
              ) : (
                /* Error card */
                <ErrorCard message={msg} onRetry={handleSend} />
              )}
            </div>
          ))}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center gap-3 p-4 bg-blue-50/60 border border-blue-100 rounded-xl max-w-md animate-pulse">
              <Loader2 size={16} className="animate-spin text-blue-600" />
              <div>
                <p className="text-xs font-medium text-gray-800">
                  Generating grounded answer...
                </p>
                <p className="text-[11px] text-gray-500">
                  Two-stage retrieval (pgvector + NVIDIA reranker) & Google Gemini synthesis
                </p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Bottom input */}
        <div className="flex-shrink-0 border-t border-gray-200 bg-white">
          <div className="px-7 py-3">
            <div className="flex items-center gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask about RBI circulars, KYC norms, fraud prevention..."
                className="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-lg text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-colors"
                aria-label="Ask a financial or regulatory question"
                disabled={isLoading}
              />
              <span className="text-xs text-gray-400 whitespace-nowrap hidden sm:block">↵ to send</span>
              <button
                id="ask-send-btn"
                onClick={() => handleSend()}
                disabled={isLoading || !input.trim()}
                aria-label="Send question"
                className="w-9 h-9 rounded-lg flex items-center justify-center text-white transition-colors disabled:opacity-40 shadow-sm"
                style={{ backgroundColor: '#0f1629' }}
              >
                <Send size={15} />
              </button>
            </div>
          </div>
          <div className="px-7 pb-3 text-center">
            <p className="text-[11px] text-gray-400">
              FinCheck AI searches 7,301 approved banking document chunks. Retrieved passages should be verified before use in client wealth advice.
            </p>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default function AskPage() {
  return (
    <Suspense fallback={<div />}>
      <AskPageContent />
    </Suspense>
  );
}

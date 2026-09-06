'use client';
// app/ask/page.tsx
import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { MainLayout } from '@/components/layout/MainLayout';
import {
  Send,
  Copy,
  ExternalLink,
  Bookmark,
  ThumbsUp,
  ThumbsDown,
  FileText,
  CheckCircle,
  Loader2,
  MessageSquare,
} from 'lucide-react';
import { quickQuestions, generateMockAnswer } from '@/lib/mock-data';
import type { Source } from '@/lib/mock-data';



interface Message {
  id: string;
  type: 'user' | 'ai';
  text: string;
  timestamp: string;
  sources?: Source[];
  saved?: boolean;
}

function parseMarkdownBold(text: string) {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return part;
  });
}

function SourceCard({ source }: { source: Source }) {
  return (
    <div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-100 rounded-lg">
      <div className="w-7 h-7 rounded bg-blue-100 flex items-center justify-center flex-shrink-0">
        <FileText size={13} className="text-blue-600" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-900">{source.documentName}</span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-100 text-emerald-700">
            Approved
          </span>
          <span className="text-xs text-gray-500">{source.version}</span>
        </div>
        <p className="text-xs text-gray-500 mt-0.5">
          {source.pageRef} · {source.section}
        </p>
      </div>
      <button aria-label="View source document" className="text-blue-400 hover:text-blue-600 flex-shrink-0">
        <ExternalLink size={13} />
      </button>
    </div>
  );
}

function AnswerCard({ message, onSave, onCopy }: {
  message: Message;
  onSave: (id: string) => void;
  onCopy: (text: string) => void;
}) {
  const paragraphs = message.text.split('\n\n').filter(Boolean);

  return (
    <div className="max-w-2xl">
      <div className="flex items-start gap-3 mb-1">
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0 mt-0.5">
          <MessageSquare size={13} className="text-white" />
        </div>
        <div className="flex-1 bg-white border border-gray-200 rounded-xl p-5 shadow-sm">
          {/* Answer text */}
          <div className="text-sm text-gray-800 leading-relaxed space-y-3 mb-4">
            {paragraphs.map((para, i) => (
              <p key={i}>{parseMarkdownBold(para)}</p>
            ))}
          </div>

          {/* Sources */}
          {message.sources && message.sources.length > 0 && (
            <div className="mb-4">
              <p className="text-[10px] font-semibold tracking-widest text-gray-400 uppercase flex items-center gap-1.5 mb-2">
                <FileText size={11} />
                Sources
              </p>
              <div className="space-y-2">
                {message.sources.map((src) => (
                  <SourceCard key={src.id} source={src} />
                ))}
              </div>
            </div>
          )}

          {/* Grounded indicator */}
          <div className="flex items-center gap-1.5 text-emerald-600 text-xs mb-4">
            <CheckCircle size={13} />
            <span>Answer grounded in approved documents</span>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-4 pt-3 border-t border-gray-100 text-xs text-gray-400">
            <span>{message.timestamp}</span>
            <button
              onClick={() => onCopy(message.text)}
              className="flex items-center gap-1 hover:text-gray-600 transition-colors"
              aria-label="Copy answer"
            >
              <Copy size={12} />
              Copy
            </button>
            <button
              className="flex items-center gap-1 hover:text-gray-600 transition-colors"
              aria-label="View source document"
            >
              <ExternalLink size={12} />
              View source
            </button>
            <button
              onClick={() => onSave(message.id)}
              className={`flex items-center gap-1 transition-colors ${
                message.saved ? 'text-blue-600' : 'hover:text-gray-600'
              }`}
              aria-label={message.saved ? 'Unsave answer' : 'Save answer'}
            >
              <Bookmark size={12} className={message.saved ? 'fill-blue-600' : ''} />
              {message.saved ? 'Saved' : 'Save'}
            </button>
            <span className="ml-auto flex items-center gap-3">
              <button className="flex items-center gap-1 hover:text-gray-600 transition-colors" aria-label="Helpful feedback">
                <ThumbsUp size={12} />
              </button>
              <button className="flex items-center gap-1 hover:text-gray-600 transition-colors" aria-label="Not helpful feedback">
                <ThumbsDown size={12} />
              </button>
              <span>Feedback</span>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function AskPageContent() {
  const searchParams = useSearchParams();
  const initialQuestion = searchParams.get('q') ?? '';
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [copyToast, setCopyToast] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const initialSentRef = useRef(false);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
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

  const handleSend = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || isLoading) return;

    const userMsg: Message = {
      id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
      type: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    // Simulate loading delay
    await new Promise((r) => setTimeout(r, 1200));

    const mockAnswer = generateMockAnswer(q);
    const aiMsg: Message = {
      id: `${mockAnswer.id}-${Math.random().toString(36).slice(2, 7)}`,
      type: 'ai',
      text: mockAnswer.text,
      timestamp: mockAnswer.timestamp,
      sources: mockAnswer.sources,
      saved: false,
    };

    setMessages((prev) => [...prev, aiMsg]);
    setIsLoading(false);
  };

  const handleSave = (id: string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, saved: !m.saved } : m))
    );
  };

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text.replace(/\*\*/g, ''));
    setCopyToast(true);
    setTimeout(() => setCopyToast(false), 2000);
  };

  const isEmpty = messages.length === 0 && !isLoading;

  return (
    <MainLayout title="Ask FinCheck AI" subtitle="Grounded in approved bank documents">
      <div className="flex flex-col" style={{ height: 'calc(100vh - 60px)' }}>
        {/* Top bar inside page */}
        <div className="px-7 pt-5 pb-3 flex items-center justify-between flex-shrink-0">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-50 border border-blue-100 flex items-center justify-center flex-shrink-0">
              <MessageSquare size={15} className="text-blue-500" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-gray-900">Ask FinCheck AI</h2>
              <p className="text-xs text-gray-500">Answers are grounded in approved bank documents</p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span className="text-xs text-gray-500 font-medium">47 documents active</span>
          </div>
        </div>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-7 py-4 space-y-6">
          {isEmpty && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center mb-3">
                <MessageSquare size={20} className="text-blue-500" />
              </div>
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Ask a question</h3>
              <p className="text-xs text-gray-400 max-w-xs mb-4">
                Search across 47 approved bank documents to get grounded answers instantly.
              </p>
              <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                {quickQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => handleSend(q)}
                    className="px-3 py-1.5 text-xs border border-gray-200 rounded-full text-gray-600 hover:border-blue-300 hover:text-blue-700 hover:bg-blue-50 transition-colors"
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
                      className="px-4 py-3 rounded-2xl text-sm text-white leading-relaxed"
                      style={{ backgroundColor: '#0f1629' }}
                    >
                      {msg.text}
                    </div>
                    <p className="text-[10px] text-gray-400 text-right mt-1">{msg.timestamp}</p>
                  </div>
                </div>
              ) : (
                /* AI answer */
                <AnswerCard message={msg} onSave={handleSave} onCopy={handleCopy} />
              )}
            </div>
          ))}

          {/* Loading state */}
          {isLoading && (
            <div className="flex items-center gap-2 text-gray-400">
              <Loader2 size={14} className="animate-spin" />
              <span className="text-xs">Searching approved documents...</span>
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
                placeholder="Ask a follow-up question..."
                className="flex-1 px-4 py-2.5 text-sm border border-gray-200 rounded-lg text-gray-800 placeholder-gray-400 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400 transition-colors"
                aria-label="Ask a follow-up question"
                disabled={isLoading}
              />
              <span className="text-xs text-gray-400 whitespace-nowrap hidden sm:block">⌘↵ to send</span>
              <button
                id="ask-send-btn"
                onClick={() => handleSend()}
                disabled={isLoading || !input.trim()}
                aria-label="Send question"
                className="w-9 h-9 rounded-lg flex items-center justify-center text-white transition-colors disabled:opacity-40"
                style={{ backgroundColor: '#0f1629' }}
              >
                <Send size={15} />
              </button>
            </div>
          </div>
          <div className="px-7 pb-3 text-center">
            <p className="text-[11px] text-gray-400">
              FinCheck AI searches approved documents only. Results should be verified before use in
              client advice.
            </p>
          </div>
        </div>
      </div>

      {/* Copy toast */}
      {copyToast && (
        <div className="fixed bottom-24 right-6 bg-gray-900 text-white text-xs px-3 py-1.5 rounded-lg shadow-lg">
          Copied to clipboard
        </div>
      )}
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

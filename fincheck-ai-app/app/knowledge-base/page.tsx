'use client';
// app/knowledge-base/page.tsx
import React, { useState, useMemo, useEffect } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/Badge';
import { Search, ChevronDown, FileText, MoreHorizontal, UploadCloud, Trash2, Sparkles } from 'lucide-react';
import { documents, knowledgeBaseStats } from '@/lib/mock-data';
import type { Document, DocumentStatus, DocumentType as AppDocumentType } from '@/lib/mock-data';
import { PdfUploadModal } from '@/components/ui/PdfUploadModal';
import { fetchUploadedDocuments, deleteUploadedDocument, type UploadedDocItem } from '@/lib/upload';

type TabKey = 'All' | 'Investment Policies' | 'Product Brochures' | 'Tax & Compliance' | 'Compliance Guidelines' | 'Uploaded Documents';

const TABS: TabKey[] = [
  'All',
  'Investment Policies',
  'Product Brochures',
  'Tax & Compliance',
  'Compliance Guidelines',
  'Uploaded Documents',
];

const TAB_TYPE_MAP: Partial<Record<TabKey, string[]>> = {
  'Investment Policies': ['Investment Policy'],
  'Product Brochures': ['Product Brochure'],
  'Tax & Compliance': ['Tax & Compliance'],
  'Compliance Guidelines': ['Compliance', 'Compliance Guidelines'],
  'Uploaded Documents': ['Uploaded Document'],
};

interface CombinedDoc {
  id: string;
  name: string;
  type: AppDocumentType | 'Uploaded Document' | string;
  version: string;
  status: DocumentStatus;
  updated: string;
  aiUsage: number | null;
  isUploaded?: boolean;
  documentId?: string;
  chunkCount?: number;
}

function DocRow({ doc, onDelete }: { doc: CombinedDoc; onDelete?: (id: string) => void }) {
  const isArchived = doc.status === 'Archived';
  return (
    <tr className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${isArchived ? 'opacity-60' : ''}`}>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2.5">
          <FileText size={14} className={doc.isUploaded ? 'text-indigo-600' : isArchived ? 'text-gray-400' : 'text-blue-500'} />
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className={`text-sm ${isArchived ? 'text-gray-400' : 'text-gray-900'} font-medium`}>
              {doc.name}
            </span>
            {doc.isUploaded && (
              <span className="inline-flex items-center gap-0.5 px-1.5 py-0.2 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                <Sparkles size={9} /> Uploaded RAG
              </span>
            )}
          </div>
        </div>
      </td>
      <td className="py-3 px-4 text-sm text-gray-500">{doc.type}</td>
      <td className="py-3 px-4 text-sm text-gray-500">{doc.version}</td>
      <td className="py-3 px-4">
        <StatusBadge status={doc.status} />
      </td>
      <td className="py-3 px-4 text-sm text-gray-500">{doc.updated}</td>
      <td className="py-3 px-4 text-sm text-gray-500">
        {doc.aiUsage !== null ? `${doc.aiUsage} answers` : doc.chunkCount ? `${doc.chunkCount} chunks` : '—'}
      </td>
      <td className="py-3 px-4">
        <div className="flex items-center gap-2">
          {doc.isUploaded && doc.documentId && onDelete ? (
            <button
              onClick={() => onDelete(doc.documentId!)}
              className="text-xs text-red-600 hover:text-red-700 font-medium transition-colors inline-flex items-center gap-1 p-1 hover:bg-red-50 rounded cursor-pointer"
              title="Delete uploaded document"
              aria-label={`Delete ${doc.name}`}
            >
              <Trash2 size={13} />
            </button>
          ) : (
            <>
              <button
                className="text-xs text-blue-600 hover:text-blue-700 font-medium transition-colors"
                aria-label={`View ${doc.name}`}
              >
                View
              </button>
              <button
                aria-label={`More options for ${doc.name}`}
                className="text-gray-400 hover:text-gray-600 p-0.5 rounded transition-colors"
              >
                <MoreHorizontal size={14} />
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

export default function KnowledgeBasePage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<DocumentStatus | 'All'>('All');
  const [activeTab, setActiveTab] = useState<TabKey>('All');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState<UploadedDocItem[]>([]);

  useEffect(() => {
    let ignore = false;
    fetchUploadedDocuments()
      .then((docs) => {
        if (!ignore) {
          setUploadedDocs(docs);
        }
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, []);

  const reloadUploadedDocs = async () => {
    try {
      const docs = await fetchUploadedDocuments();
      setUploadedDocs(docs);
    } catch {
      // Ignore background fetch failure
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm('Are you sure you want to remove this uploaded document from the RAG knowledge base?')) {
      return;
    }
    const ok = await deleteUploadedDocument(docId);
    if (ok) {
      setUploadedDocs((prev) => prev.filter((d) => d.document_id !== docId));
    }
  };

  const allDocuments: CombinedDoc[] = useMemo(() => {
    const uploadedAdapted: CombinedDoc[] = uploadedDocs.map((u) => ({
      id: u.document_id,
      documentId: u.document_id,
      name: u.document_name,
      type: 'Uploaded Document',
      version: 'v1.0',
      status: 'Approved',
      updated: u.created_at ? new Date(u.created_at).toLocaleDateString() : 'Today',
      aiUsage: null,
      chunkCount: u.chunk_count,
      isUploaded: true,
    }));

    return [...uploadedAdapted, ...documents];
  }, [uploadedDocs]);

  const filtered = useMemo(() => {
    return allDocuments.filter((doc) => {
      const matchSearch =
        search === '' ||
        doc.name.toLowerCase().includes(search.toLowerCase()) ||
        doc.type.toLowerCase().includes(search.toLowerCase());
      const matchStatus = statusFilter === 'All' || doc.status === statusFilter;
      const matchTab =
        activeTab === 'All' ||
        (TAB_TYPE_MAP[activeTab] ?? []).includes(doc.type);
      return matchSearch && matchStatus && matchTab;
    });
  }, [allDocuments, search, statusFilter, activeTab]);

  return (
    <MainLayout title="Knowledge Base" subtitle={`${allDocuments.length} verified & uploaded documents`}>
      <div className="px-7 py-7">
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-white border border-green-200 rounded-xl p-5 shadow-xs">
            <div className="text-3xl font-bold text-emerald-600 mb-0.5">
              {knowledgeBaseStats.approved + uploadedDocs.length}
            </div>
            <div className="text-sm text-gray-500">Active RAG Documents</div>
          </div>
          <div className="bg-white border border-indigo-200 rounded-xl p-5 shadow-xs">
            <div className="text-3xl font-bold text-indigo-600 mb-0.5">{uploadedDocs.length}</div>
            <div className="text-sm text-gray-500">User Uploaded PDFs</div>
          </div>
          <div className="bg-white border border-gray-200 rounded-xl p-5 shadow-xs">
            <div className="text-3xl font-bold text-gray-500 mb-0.5">{knowledgeBaseStats.archived}</div>
            <div className="text-sm text-gray-500">Archived Documents</div>
          </div>
          <div className="bg-white border border-amber-200 rounded-xl p-5 shadow-xs">
            <div className="text-3xl font-bold text-amber-600 mb-0.5">{knowledgeBaseStats.pendingReview}</div>
            <div className="text-sm text-gray-500">Pending Review</div>
          </div>
        </div>

        {/* Filter area + Table card */}
        <Card padding="none">
          {/* Filters & Action Bar */}
          <div className="px-5 pt-4 pb-0 flex items-center gap-3 flex-wrap justify-between">
            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative">
                <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search documents..."
                  className="pl-8 pr-3 py-1.5 text-xs border border-gray-200 rounded-lg text-gray-700 placeholder-gray-400 focus:outline-none focus:border-blue-400 transition-colors w-52 bg-gray-50 focus:bg-white"
                  aria-label="Search documents"
                />
              </div>
              {/* Status dropdown */}
              <div className="relative">
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value as DocumentStatus | 'All')}
                  className="appearance-none pl-3 pr-8 py-1.5 text-xs border border-gray-200 rounded-lg text-gray-700 focus:outline-none focus:border-blue-400 transition-colors bg-gray-50 focus:bg-white cursor-pointer"
                  aria-label="Filter by status"
                >
                  <option value="All">All statuses</option>
                  <option value="Approved">Approved</option>
                  <option value="Archived">Archived</option>
                  <option value="Pending Review">Pending Review</option>
                </select>
                <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400">{filtered.length} documents</span>
              <button
                onClick={() => setIsUploadModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-xs cursor-pointer"
              >
                <UploadCloud size={13} />
                <span>Upload PDF</span>
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="px-5 mt-3 flex items-center gap-0 border-b border-gray-100 overflow-x-auto">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2.5 text-xs font-medium border-b-2 transition-colors whitespace-nowrap cursor-pointer ${
                  activeTab === tab
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-200'
                }`}
              >
                {tab}
                {tab === 'Uploaded Documents' && uploadedDocs.length > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] bg-blue-100 text-blue-800 font-semibold">
                    {uploadedDocs.length}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full min-w-[800px]">
              <thead>
                <tr className="border-b border-gray-100">
                  <th className="text-left py-2.5 px-4 text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
                    Document Name
                  </th>
                  <th className="text-left py-2.5 px-4 text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
                    Type
                  </th>
                  <th className="text-left py-2.5 px-4 text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
                    Version
                  </th>
                  <th className="text-left py-2.5 px-4 text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
                    Status
                  </th>
                  <th className="text-left py-2.5 px-4 text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
                    Updated
                  </th>
                  <th className="text-left py-2.5 px-4 text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
                    AI Usage / Chunks
                  </th>
                  <th className="text-left py-2.5 px-4 text-[10px] font-semibold tracking-wider text-gray-400 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {filtered.length > 0 ? (
                  filtered.map((doc) => (
                    <DocRow key={doc.id} doc={doc} onDelete={handleDelete} />
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-sm text-gray-400">
                      No documents match your filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* PDF Upload Modal */}
      <PdfUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onSuccess={() => {
          reloadUploadedDocs();
          setActiveTab('Uploaded Documents');
        }}
      />
    </MainLayout>
  );
}


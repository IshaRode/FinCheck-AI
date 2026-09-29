'use client';

import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Database,
  Sparkles,
} from 'lucide-react';
import { uploadPdfDocument, type PDFUploadResult } from '@/lib/upload';

interface PdfUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (result: PDFUploadResult) => void;
}

export function PdfUploadModal({ isOpen, onClose, onSuccess }: PdfUploadModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<string>('');
  const [result, setResult] = useState<PDFUploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const resetState = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setIsUploading(false);
    setUploadStep('');
  };

  const handleClose = () => {
    if (isUploading) return;
    resetState();
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      validateAndSetFile(selected);
    }
  };

  const validateAndSetFile = (selected: File) => {
    setError(null);
    setResult(null);

    if (!selected.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF (.pdf) documents are accepted.');
      return;
    }

    if (selected.size > 20 * 1024 * 1024) {
      setError('File size exceeds the 20MB limit.');
      return;
    }

    if (selected.size === 0) {
      setError('The selected file is empty.');
      return;
    }

    setFile(selected);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) {
      validateAndSetFile(dropped);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleUpload = async () => {
    if (!file || isUploading) return;

    setIsUploading(true);
    setError(null);
    setResult(null);
    setUploadStep('Extracting text and chunking pages with PyMuPDF...');

    try {
      const stepTimer1 = setTimeout(() => {
        setUploadStep('Generating 2048-dim NVIDIA NeMo embeddings...');
      }, 1500);

      const stepTimer2 = setTimeout(() => {
        setUploadStep('Indexing halfvec vectors into Supabase pgvector...');
      }, 4000);

      const res = await uploadPdfDocument(file);

      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);

      setResult(res);
      setUploadStep('');
      if (onSuccess) {
        onSuccess(res);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload and ingestion failed.';
      setError(msg);
      setUploadStep('');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-in fade-in duration-200">
      <div
        className="bg-white rounded-2xl shadow-2xl border border-gray-100 max-w-lg w-full overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gradient-to-r from-blue-50/70 via-indigo-50/40 to-white">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-xs">
              <UploadCloud size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-gray-900">Upload Financial PDF</h3>
              <p className="text-[11px] text-gray-500">
                Automatic text extraction, NVIDIA NeMo embeddings & pgvector ingestion
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            disabled={isUploading}
            className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
            aria-label="Close upload modal"
          >
            <X size={16} />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Dropzone */}
          {!result && (
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-all ${
                isDragging
                  ? 'border-blue-500 bg-blue-50/80 scale-[0.99]'
                  : 'border-gray-200 hover:border-blue-400 bg-gray-50/60 hover:bg-blue-50/30'
              } ${isUploading ? 'pointer-events-none opacity-60' : ''}`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                className="hidden"
              />
              <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mx-auto mb-3">
                <FileText size={22} />
              </div>
              <p className="text-sm font-semibold text-gray-800 mb-1">
                {file ? file.name : 'Click to select or drag and drop PDF'}
              </p>
              <p className="text-xs text-gray-500">
                {file
                  ? `${(file.size / (1024 * 1024)).toFixed(2)} MB · Ready for ingestion`
                  : 'RBI circulars, policies, brochures or tax reports up to 20MB'}
              </p>
            </div>
          )}

          {/* Upload Progress State */}
          {isUploading && (
            <div className="p-4 bg-blue-50/80 border border-blue-100 rounded-xl space-y-2.5 animate-pulse">
              <div className="flex items-center gap-2.5 text-blue-700 font-medium text-xs">
                <Loader2 size={16} className="animate-spin text-blue-600" />
                <span>{uploadStep || 'Processing document...'}</span>
              </div>
              <div className="w-full bg-blue-200/60 rounded-full h-1.5 overflow-hidden">
                <div className="bg-blue-600 h-1.5 rounded-full w-2/3 animate-indeterminate"></div>
              </div>
              <p className="text-[11px] text-gray-500 leading-relaxed">
                Document will be chunked into 500-800 token units and embedded with 2048-dim NVIDIA NeMo Retriever.
              </p>
            </div>
          )}

          {/* Success Banner */}
          {result && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-3 animate-in fade-in">
              <div className="flex items-start gap-2.5">
                <CheckCircle2 size={18} className="text-emerald-600 mt-0.5 flex-shrink-0" />
                <div className="space-y-1">
                  <h4 className="text-xs font-bold text-emerald-950">
                    {result.status === 'already_exists' ? 'Document Already Indexed' : 'Document Ingestion Complete'}
                  </h4>
                  <p className="text-xs text-emerald-800 leading-relaxed">
                    {result.message}
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-emerald-200/60">
                <div className="bg-white/80 p-2 rounded border border-emerald-100">
                  <span className="text-gray-500 block">Total Chunks Indexed</span>
                  <span className="font-semibold text-emerald-900">{result.total_chunks} chunks</span>
                </div>
                {result.total_pages && (
                  <div className="bg-white/80 p-2 rounded border border-emerald-100">
                    <span className="text-gray-500 block">Pages Extracted</span>
                    <span className="font-semibold text-emerald-900">{result.total_pages} pages</span>
                  </div>
                )}
                {result.total_tokens && (
                  <div className="bg-white/80 p-2 rounded border border-emerald-100">
                    <span className="text-gray-500 block">Total Tokens</span>
                    <span className="font-semibold text-emerald-900">{result.total_tokens} tokens</span>
                  </div>
                )}
                <div className="bg-white/80 p-2 rounded border border-emerald-100">
                  <span className="text-gray-500 block">RAG Ready</span>
                  <span className="font-semibold text-emerald-700 flex items-center gap-1">
                    <Sparkles size={11} /> Active in pgvector
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-800 animate-in fade-in">
              <AlertCircle size={16} className="text-red-600 mt-0.5 flex-shrink-0" />
              <div className="space-y-1 flex-1">
                <span className="font-semibold block text-red-950">Ingestion Error</span>
                <span className="block text-red-700 leading-relaxed">{error}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3.5 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-1 text-[11px] text-gray-500">
            <Database size={12} className="text-blue-600" />
            <span>Integrated with NVIDIA Reranker & Gemini</span>
          </div>

          <div className="flex items-center gap-2">
            {result ? (
              <button
                onClick={handleClose}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 transition-colors shadow-xs"
              >
                Done
              </button>
            ) : (
              <>
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isUploading}
                  className="px-3.5 py-1.5 text-xs font-medium text-gray-700 hover:text-gray-900 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleUpload}
                  disabled={!file || isUploading}
                  className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors shadow-xs disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isUploading ? (
                    <>
                      <Loader2 size={13} className="animate-spin" />
                      <span>Ingesting...</span>
                    </>
                  ) : (
                    <>
                      <UploadCloud size={13} />
                      <span>Ingest PDF</span>
                    </>
                  )}
                </button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

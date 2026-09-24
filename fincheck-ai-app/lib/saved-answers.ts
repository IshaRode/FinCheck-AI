import type { GenerateResponse } from '@/lib/generation';

export interface StoredSavedAnswer {
  id: string;
  question: string;
  data: GenerateResponse;
  savedAt: string;
}

const STORAGE_KEY = 'fincheck-saved-answers';

export function getSavedAnswers(): StoredSavedAnswer[] {
  if (typeof window === 'undefined') return [];

  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    const parsed: unknown = JSON.parse(stored);
    if (!Array.isArray(parsed)) return [];
    return parsed as StoredSavedAnswer[];
  } catch {
    return [];
  }
}

export function saveAnswer(question: string, data: GenerateResponse): StoredSavedAnswer {
  const saved: StoredSavedAnswer = {
    id: `saved-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    question,
    data,
    savedAt: new Date().toISOString(),
  };

  window.localStorage.setItem(STORAGE_KEY, JSON.stringify([saved, ...getSavedAnswers()]));
  return saved;
}

export function removeSavedAnswer(id: string): void {
  window.localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(getSavedAnswers().filter((answer) => answer.id !== id))
  );
}

export function isAnswerSaved(question: string, data: GenerateResponse): boolean {
  return getSavedAnswers().some(
    (answer) => answer.question === question && answer.data.answer === data.answer
  );
}
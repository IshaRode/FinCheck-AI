// lib/mock-data.ts
// Centralized mock data for FinCheck AI — all data is fictional/synthetic demo data

export type DocumentStatus = 'Approved' | 'Archived' | 'Pending Review';
export type DocumentType =
  | 'Product Brochure'
  | 'Investment Policy'
  | 'Tax & Compliance'
  | 'Compliance'
  | 'Compliance Guidelines';

export type QuestionStatus = 'Answered' | 'Insufficient Info';

export interface Document {
  id: string;
  name: string;
  type: DocumentType;
  version: string;
  status: DocumentStatus;
  updated: string;
  aiUsage: number | null;
  isSuperseded?: boolean;
}

export interface QuestionTag {
  label: string;
}

export interface Question {
  id: string;
  text: string;
  date: string;
  time: string;
  status: QuestionStatus;
  sourceCount: number;
  tags: string[];
  answer?: string;
  sources?: Source[];
}

export interface Source {
  id: string;
  documentName: string;
  version: string;
  status: 'Approved' | 'Archived';
  pageRef: string;
  section: string;
}

export interface Answer {
  id: string;
  questionId: string;
  text: string;
  sources: Source[];
  timestamp: string;
}

export interface SavedAnswer {
  id: string;
  question: string;
  answerPreview: string;
  sourceDocument: string;
  documentVersion: string;
  savedDate: string;
  fullAnswer: string;
}

export interface ActivityDataPoint {
  label: string;
  questions: number;
  answered: number;
}

// ─── Documents ───────────────────────────────────────────────────────────────

export const documents: Document[] = [
  { id: 'doc-1', name: 'Product X Brochure', type: 'Product Brochure', version: 'v3', status: 'Approved', updated: 'Aug 2026', aiUsage: 24 },
  { id: 'doc-2', name: 'Investment Policy Manual', type: 'Investment Policy', version: 'v5', status: 'Approved', updated: 'Aug 2026', aiUsage: 41 },
  { id: 'doc-3', name: 'Tax Guidelines 2026', type: 'Tax & Compliance', version: 'v2', status: 'Approved', updated: 'Jul 2026', aiUsage: 18 },
  { id: 'doc-4', name: 'Compliance Framework', type: 'Compliance', version: 'v4', status: 'Approved', updated: 'Jul 2026', aiUsage: 33 },
  { id: 'doc-5', name: 'Product Eligibility Guidelines', type: 'Product Brochure', version: 'v2', status: 'Approved', updated: 'Jun 2026', aiUsage: 15 },
  { id: 'doc-6', name: 'Premium Portfolio Brochure', type: 'Product Brochure', version: 'v1', status: 'Approved', updated: 'Jun 2026', aiUsage: 9 },
  { id: 'doc-11', name: 'Capital Protected Note Brochure', type: 'Product Brochure', version: 'v2', status: 'Approved', updated: 'May 2026', aiUsage: 12 },
  { id: 'doc-12', name: 'AML & CFT Policy', type: 'Compliance Guidelines', version: 'v3', status: 'Approved', updated: 'May 2026', aiUsage: 7 },
  { id: 'doc-13', name: 'Equity-Linked Note Prospectus', type: 'Product Brochure', version: 'v1', status: 'Approved', updated: 'Apr 2026', aiUsage: 5 },
  { id: 'doc-14', name: 'Market-Linked Deposit Terms', type: 'Investment Policy', version: 'v2', status: 'Approved', updated: 'Apr 2026', aiUsage: 19 },
  { id: 'doc-15', name: 'Client Suitability Assessment Framework', type: 'Compliance Guidelines', version: 'v2', status: 'Approved', updated: 'Mar 2026', aiUsage: 28 },
  { id: 'doc-16', name: 'Balanced Growth Fund Prospectus v2', type: 'Product Brochure', version: 'v2', status: 'Approved', updated: 'Mar 2026', aiUsage: 11 },
  { id: 'doc-17', name: 'Wealth Division Investment Policy 2026', type: 'Investment Policy', version: 'v1', status: 'Approved', updated: 'Jan 2026', aiUsage: 36 },
  { id: 'doc-18', name: 'Foreign Currency Risk Disclosure', type: 'Compliance Guidelines', version: 'v1', status: 'Approved', updated: 'Jan 2026', aiUsage: 8 },
  { id: 'doc-7', name: 'Product X Brochure (Superseded)', type: 'Product Brochure', version: 'v2', status: 'Archived', updated: 'May 2026', aiUsage: null, isSuperseded: true },
  { id: 'doc-8', name: 'Tax Guidelines 2025', type: 'Tax & Compliance', version: 'v1', status: 'Archived', updated: 'Jan 2026', aiUsage: null, isSuperseded: true },
  { id: 'doc-19', name: 'Investment Policy Manual v4', type: 'Investment Policy', version: 'v4', status: 'Archived', updated: 'Dec 2025', aiUsage: null, isSuperseded: true },
  { id: 'doc-9', name: 'AML Compliance Policy 2026', type: 'Compliance Guidelines', version: 'v1', status: 'Pending Review', updated: 'Sep 2026', aiUsage: null },
  { id: 'doc-10', name: 'Balanced Growth Fund Prospectus v3', type: 'Product Brochure', version: 'v3', status: 'Pending Review', updated: 'Sep 2026', aiUsage: null },
  { id: 'doc-20', name: 'Digital Advisory Service Guidelines', type: 'Compliance Guidelines', version: 'v1', status: 'Pending Review', updated: 'Aug 2026', aiUsage: null },
];

// ─── Sources ─────────────────────────────────────────────────────────────────

export const sources: Source[] = [
  { id: 'src-1', documentName: 'Product X Brochure', version: 'v3', status: 'Approved', pageRef: 'Page 12', section: 'Investment Requirements' },
  { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' },
  { id: 'src-3', documentName: 'Tax Guidelines 2026', version: 'v2', status: 'Approved', pageRef: 'Page 8', section: 'Tax Benefits & Exemptions' },
  { id: 'src-4', documentName: 'Product Eligibility Guidelines', version: 'v2', status: 'Approved', pageRef: 'Page 3', section: 'Retail Product Thresholds' },
  { id: 'src-5', documentName: 'Compliance Framework', version: 'v4', status: 'Approved', pageRef: 'Page 22', section: 'KYC Documentation Standards' },
  { id: 'src-6', documentName: 'Premium Portfolio Brochure', version: 'v1', status: 'Approved', pageRef: 'Page 7', section: 'Joint Account Terms' },
  { id: 'src-7', documentName: 'Capital Protected Note Brochure', version: 'v2', status: 'Approved', pageRef: 'Page 5', section: 'Lock-in Period & Redemption' },
  { id: 'src-8', documentName: 'Client Suitability Assessment Framework', version: 'v2', status: 'Approved', pageRef: 'Page 14', section: 'Risk Profiling Requirements' },
];

// ─── Questions ────────────────────────────────────────────────────────────────

export const questions: Question[] = [
  {
    id: 'q-1', text: 'What are the eligibility criteria for Product X?', date: 'Today', time: '10:42 AM',
    status: 'Answered', sourceCount: 2, tags: ['Eligibility', 'Product X'],
    answer: 'To be eligible for Product X, investors must meet the following criteria: (1) Minimum net worth of SGD 250,000 in investable assets; (2) Must be classified as an Accredited Investor under MAS guidelines; (3) Must have completed the Customer Risk Profiling questionnaire within the last 12 months; (4) Residency requirements apply — non-Singapore residents must provide additional documentation as outlined in the Product Eligibility Guidelines.',
    sources: [{ id: 'src-1', documentName: 'Product X Brochure', version: 'v3', status: 'Approved', pageRef: 'Page 12', section: 'Investment Requirements' }, { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' }],
  },
  {
    id: 'q-2', text: 'What tax benefits apply to the Balanced Growth Fund?', date: 'Today', time: '9:15 AM',
    status: 'Answered', sourceCount: 1, tags: ['Tax', 'Balanced Growth Fund'],
    answer: "The Balanced Growth Fund qualifies for the following tax treatment under Singapore tax law: Capital gains on the fund are not taxable for individual investors. Dividend distributions from the fund may be subject to withholding tax depending on the investor's residency status. Please refer to the Tax Guidelines 2026 for complete details on applicable exemptions.",
    sources: [{ id: 'src-3', documentName: 'Tax Guidelines 2026', version: 'v2', status: 'Approved', pageRef: 'Page 8', section: 'Tax Benefits & Exemptions' }],
  },
  {
    id: 'q-3', text: 'What is the expected return of Product X next year?', date: 'Yesterday', time: '4:30 PM',
    status: 'Insufficient Info', sourceCount: 0, tags: ['Returns', 'Product X'],
    answer: 'The approved documents do not contain projections for expected returns for Product X in the upcoming year. Past performance data is available in the Product X Brochure, however forward-looking projections are not included in the approved knowledge base. Please consult the investment team directly for performance forecasts.',
    sources: [],
  },
  {
    id: 'q-4', text: 'Minimum investment thresholds for all retail products?', date: 'Yesterday', time: '2:10 PM',
    status: 'Answered', sourceCount: 3, tags: ['Investment', 'Retail Products'],
    answer: 'Minimum investment thresholds vary by product: Product X — SGD 50,000 initial, SGD 10,000 subsequent; Premium Portfolio — SGD 100,000 initial, SGD 25,000 subsequent; Balanced Growth Fund — SGD 10,000 initial, SGD 5,000 subsequent; Capital Protected Note — SGD 50,000 initial (lump sum only). These thresholds are set by the Head of Wealth Products and are reviewed annually.',
    sources: [
      { id: 'src-1', documentName: 'Product X Brochure', version: 'v3', status: 'Approved', pageRef: 'Page 12', section: 'Investment Requirements' },
      { id: 'src-4', documentName: 'Product Eligibility Guidelines', version: 'v2', status: 'Approved', pageRef: 'Page 3', section: 'Retail Product Thresholds' },
      { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' },
    ],
  },
  {
    id: 'q-5', text: 'What KYC documentation is required for non-residents?', date: '2 Sep', time: '3:45 PM',
    status: 'Answered', sourceCount: 2, tags: ['KYC', 'Compliance'],
    answer: 'Non-resident investors are required to provide the following KYC documentation: (1) Valid passport (certified copy); (2) Proof of residential address dated within 3 months; (3) Source of funds declaration; (4) Tax Identification Number (TIN) from country of residence; (5) Completed W-8BEN form (for US persons). Additional documentation may be required at the discretion of the compliance team.',
    sources: [
      { id: 'src-5', documentName: 'Compliance Framework', version: 'v4', status: 'Approved', pageRef: 'Page 22', section: 'KYC Documentation Standards' },
      { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' },
    ],
  },
  {
    id: 'q-6', text: 'What are the redemption fees for Product X early exit?', date: '1 Sep', time: '11:20 AM',
    status: 'Answered', sourceCount: 1, tags: ['Fees', 'Product X'],
    answer: 'Product X imposes a tiered early redemption fee structure: Year 1 exit — 3% of net asset value; Year 2 exit — 2% of NAV; Year 3 exit — 1% of NAV; After Year 3 — No redemption fee. Redemption requests must be submitted in writing with a minimum 5 business days notice. The fee is deducted from the redemption proceeds at settlement.',
    sources: [{ id: 'src-1', documentName: 'Product X Brochure', version: 'v3', status: 'Approved', pageRef: 'Page 12', section: 'Investment Requirements' }],
  },
  {
    id: 'q-7', text: 'Is the Premium Portfolio available to joint account holders?', date: '1 Sep', time: '9:00 AM',
    status: 'Answered', sourceCount: 2, tags: ['Premium Portfolio', 'Joint Accounts'],
    answer: 'Yes, the Premium Portfolio is available to joint account holders subject to the following conditions: Both account holders must individually meet the Accredited Investor criteria; Both parties must complete the Customer Risk Profiling questionnaire; Joint subscription requires signatures from all account holders on the application form; The primary account holder is responsible for all correspondence.',
    sources: [
      { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' },
      { id: 'src-6', documentName: 'Premium Portfolio Brochure', version: 'v1', status: 'Approved', pageRef: 'Page 7', section: 'Joint Account Terms' },
    ],
  },
  {
    id: 'q-8', text: 'What are the lock-in periods for structured products?', date: '31 Aug', time: '2:30 PM',
    status: 'Answered', sourceCount: 1, tags: ['Structured Products', 'Lock-in'],
    answer: 'Lock-in periods for structured products vary: Capital Protected Notes — 3 years minimum lock-in, no early redemption permitted; Market-Linked Deposits — 6 to 18 months depending on the tranche; Equity-Linked Notes — 1 to 2 years with early exit subject to market price. Please refer to the relevant product brochure for specific terms.',
    sources: [{ id: 'src-7', documentName: 'Capital Protected Note Brochure', version: 'v2', status: 'Approved', pageRef: 'Page 5', section: 'Lock-in Period & Redemption' }],
  },
  {
    id: 'q-9', text: 'What risk profile is required for the Premium Portfolio?', date: '30 Aug', time: '10:00 AM',
    status: 'Answered', sourceCount: 2, tags: ['Risk Profile', 'Premium Portfolio'],
    answer: 'The Premium Portfolio requires a minimum risk profile of "Balanced" or higher as determined by the Customer Risk Profiling questionnaire. Clients with a "Conservative" profile are not eligible to subscribe. Risk profiling must be completed within the last 12 months and must not have been overridden by a client waiver.',
    sources: [
      { id: 'src-8', documentName: 'Client Suitability Assessment Framework', version: 'v2', status: 'Approved', pageRef: 'Page 14', section: 'Risk Profiling Requirements' },
      { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' },
    ],
  },
  {
    id: 'q-10', text: 'Are capital gains from structured products taxable?', date: '29 Aug', time: '3:10 PM',
    status: 'Insufficient Info', sourceCount: 0, tags: ['Tax', 'Structured Products'],
    answer: 'The approved knowledge base does not contain a definitive ruling on the taxability of capital gains from all structured products. The Tax Guidelines 2026 cover general fund and equity investment tax treatment, but structured product-specific guidance is not yet included. Please refer directly to the tax advisory team or the IRAS website for current rulings.',
    sources: [],
  },
];

// ─── AI Answer Templates ──────────────────────────────────────────────────────

export const answers: Answer[] = [
  {
    id: 'ans-1', questionId: 'q-1',
    text: 'The minimum initial investment amount for Product X is **SGD 50,000**. Subsequent top-up contributions must be a minimum of **SGD 10,000** per transaction.\n\nThese thresholds apply to both individual and joint account subscriptions and may not be waived without prior written approval from the Head of Wealth Products.\n\nPlease note that the minimum subscription amount is distinct from the minimum net worth eligibility requirement (SGD 250,000).',
    sources: [{ id: 'src-1', documentName: 'Product X Brochure', version: 'v3', status: 'Approved', pageRef: 'Page 12', section: 'Investment Requirements' }],
    timestamp: '10:44 AM',
  },
  {
    id: 'ans-2', questionId: 'q-5',
    text: 'Non-resident investors are required to provide the following **KYC documentation**:\n\n(1) Valid passport — certified copy required; (2) Proof of residential address dated within 3 months; (3) Source of funds declaration form; (4) **Tax Identification Number (TIN)** from country of residence; (5) Completed W-8BEN form (for US persons only).\n\nAdditional documentation may be requested at the discretion of the compliance team based on risk classification.',
    sources: [
      { id: 'src-5', documentName: 'Compliance Framework', version: 'v4', status: 'Approved', pageRef: 'Page 22', section: 'KYC Documentation Standards' },
      { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' },
    ],
    timestamp: '3:46 PM',
  },
  {
    id: 'ans-3', questionId: 'q-2',
    text: "The Balanced Growth Fund qualifies for favorable **tax treatment** under Singapore law:\n\n**Capital gains** on the fund are **not taxable** for individual investors. Dividend distributions may be subject to withholding tax depending on the investor\'s residency status and applicable tax treaties.\n\nFor non-Singapore tax residents, the withholding rate varies by treaty jurisdiction. Please refer to the Tax Guidelines 2026 for jurisdiction-specific rates and exemption procedures.",
    sources: [{ id: 'src-3', documentName: 'Tax Guidelines 2026', version: 'v2', status: 'Approved', pageRef: 'Page 8', section: 'Tax Benefits & Exemptions' }],
    timestamp: '9:16 AM',
  },
  {
    id: 'ans-4', questionId: 'q-4',
    text: 'Minimum investment thresholds for retail products as at August 2026:\n\n**Product X** — SGD 50,000 initial · SGD 10,000 subsequent\n**Premium Portfolio** — SGD 100,000 initial · SGD 25,000 subsequent\n**Balanced Growth Fund** — SGD 10,000 initial · SGD 5,000 subsequent\n**Capital Protected Note** — SGD 50,000 initial (lump sum only, no subsequent)\n\nThresholds are reviewed annually by the Head of Wealth Products. Exceptions require Head of Division approval.',
    sources: [
      { id: 'src-1', documentName: 'Product X Brochure', version: 'v3', status: 'Approved', pageRef: 'Page 12', section: 'Investment Requirements' },
      { id: 'src-4', documentName: 'Product Eligibility Guidelines', version: 'v2', status: 'Approved', pageRef: 'Page 3', section: 'Retail Product Thresholds' },
      { id: 'src-2', documentName: 'Investment Policy Manual', version: 'v5', status: 'Approved', pageRef: 'Page 4', section: 'Eligibility Criteria' },
    ],
    timestamp: '2:11 PM',
  },
  {
    id: 'ans-insufficient', questionId: 'q-3',
    text: "The approved knowledge base does not contain sufficient information to answer this question.\n\nForward-looking return projections and performance forecasts are not included in the approved document set. Past performance data is available in the **Product X Brochure v3** (Page 18), however this should not be used as an indicator of future performance.\n\nFor investment performance forecasts, please consult the Wealth Products team directly or refer to the fund manager\'s latest factsheet.",
    sources: [],
    timestamp: '',
  },
];

// ─── Quick Questions ──────────────────────────────────────────────────────────

export const quickQuestions: string[] = [
  'What are the eligibility criteria for Product X?',
  'What is the minimum investment amount for the Premium Portfolio?',
  'What tax benefits apply to the Balanced Growth Fund?',
  'What are the risks associated with Product X?',
];

// ─── Saved Answers ────────────────────────────────────────────────────────────

export const savedAnswers: SavedAnswer[] = [
  {
    id: 'saved-1', question: 'What is the minimum investment amount for Product X?',
    answerPreview: 'The minimum initial investment amount for Product X is SGD 50,000. Subsequent top-up contributions must be a minimum of SGD 10,000 per transaction.',
    sourceDocument: 'Product X Brochure', documentVersion: 'v3', savedDate: 'Today, 10:44 AM',
    fullAnswer: 'The minimum initial investment amount for Product X is **SGD 50,000**. Subsequent top-up contributions must be a minimum of **SGD 10,000** per transaction.\n\nThese thresholds apply to both individual and joint account subscriptions and may not be waived without prior written approval from the Head of Wealth Products.\n\nPlease note that the minimum subscription amount is distinct from the minimum net worth eligibility requirement (SGD 250,000).',
  },
  {
    id: 'saved-2', question: 'What are the eligibility criteria for Product X?',
    answerPreview: 'To be eligible for Product X, investors must meet minimum net worth of SGD 250,000, be classified as an Accredited Investor under MAS guidelines, and have completed the Customer Risk Profiling questionnaire within the last 12 months.',
    sourceDocument: 'Product Eligibility Guidelines', documentVersion: 'v2', savedDate: 'Today, 10:42 AM',
    fullAnswer: 'To be eligible for Product X, investors must meet the following criteria: (1) Minimum net worth of **SGD 250,000** in investable assets; (2) Must be classified as an **Accredited Investor** under MAS guidelines; (3) Must have completed the Customer Risk Profiling questionnaire within the last 12 months; (4) Residency requirements apply — non-Singapore residents must provide additional documentation.',
  },
  {
    id: 'saved-3', question: 'What KYC documentation is required for non-residents?',
    answerPreview: 'Non-resident investors are required to provide valid passport (certified copy), proof of residential address dated within 3 months, source of funds declaration, and Tax Identification Number from country of residence.',
    sourceDocument: 'Compliance Framework', documentVersion: 'v4', savedDate: '2 Sep, 3:45 PM',
    fullAnswer: 'Non-resident investors are required to provide the following KYC documentation: (1) Valid passport (certified copy); (2) Proof of residential address dated within 3 months; (3) Source of funds declaration; (4) **Tax Identification Number (TIN)** from country of residence; (5) Completed W-8BEN form (for US persons).',
  },
  {
    id: 'saved-4', question: 'What tax benefits apply to the Balanced Growth Fund?',
    answerPreview: 'The Balanced Growth Fund qualifies for capital gains exemption under Singapore tax law. Dividend distributions may be subject to withholding tax depending on investor residency status.',
    sourceDocument: 'Tax Guidelines 2026', documentVersion: 'v2', savedDate: 'Today, 9:15 AM',
    fullAnswer: "The Balanced Growth Fund qualifies for the following tax treatment under Singapore tax law: Capital gains on the fund are **not taxable** for individual investors. Dividend distributions from the fund may be subject to withholding tax depending on the investor\'s residency status.",
  },
];

// ─── KPI Stats (derived from actual data for consistency) ────────────────────

export const knowledgeBaseStats = {
  total: documents.length,
  currentPolicies: documents.filter((d) => d.type === 'Investment Policy' && d.status === 'Approved').length,
  productBrochures: documents.filter((d) => d.type === 'Product Brochure' && d.status === 'Approved').length,
  taxCompliance: documents.filter((d) =>
    (d.type === 'Tax & Compliance' || d.type === 'Compliance' || d.type === 'Compliance Guidelines') &&
    d.status === 'Approved'
  ).length,
  approved: documents.filter((d) => d.status === 'Approved').length,
  archived: documents.filter((d) => d.status === 'Archived').length,
  pendingReview: documents.filter((d) => d.status === 'Pending Review').length,
};

export const questionStats = {
  total: questions.length,
  answered: questions.filter((q) => q.status === 'Answered').length,
  insufficientInfo: questions.filter((q) => q.status === 'Insufficient Info').length,
};

// ─── Activity Data (for dashboard usage chart) ───────────────────────────────

export const activityData: ActivityDataPoint[] = [
  { label: 'Mon', questions: 3, answered: 3 },
  { label: 'Tue', questions: 5, answered: 4 },
  { label: 'Wed', questions: 7, answered: 6 },
  { label: 'Thu', questions: 4, answered: 3 },
  { label: 'Fri', questions: 9, answered: 8 },
  { label: 'Sat', questions: 2, answered: 2 },
  { label: 'Today', questions: 4, answered: 3 },
];

// ─── Mock AI answer generator (keyword-varied responses) ─────────────────────

export function generateMockAnswer(question: string): Answer {
  const q = question.toLowerCase();
  const now = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  const uniqueId = `ans-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;

  if (q.includes('kyc') || q.includes('non-resident') || q.includes('documentation')) {
    return { ...answers[1], id: uniqueId, timestamp: now };
  }
  if (q.includes('tax') || q.includes('taxable') || q.includes('withholding')) {
    return { ...answers[2], id: uniqueId, timestamp: now };
  }
  if (q.includes('minimum') || q.includes('threshold') || q.includes('investment amount')) {
    return { ...answers[3], id: uniqueId, timestamp: now };
  }
  if (q.includes('return') || q.includes('forecast') || q.includes('performance') || q.includes('expected')) {
    return { ...answers[4], id: uniqueId, timestamp: now };
  }
  return { ...answers[0], id: uniqueId, timestamp: now };
}

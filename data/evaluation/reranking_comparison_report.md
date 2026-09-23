# FinCheck AI — Phase 5 Reranking Comparative Benchmark Report

- **Total Questions Evaluated:** 15
- **Top-1 Rank Promotion Rate:** 40.0% (6 queries promoted a more precise passage to #1)
- **Average Vector Latency:** 1173.5 ms
- **Average Reranker Latency:** 231.7 ms

## Comparison Table

| ID | Category | Query | Vector Top 1 | Reranked Top 1 (Logit) | Rank Movement |
|:---|:---|:---|:---|:---|:---|
| Q01 | KYC & Customer Due Diligence | What are the RBI rules regarding KYC requirements? | [indian_finance] KYC & Compliance (Banking and Di... (0.551) | [indian_finance] KYC and Identity Verification - ... (-1.72) | ▲ Vector #3 promoted to #1 |
| Q02 | KYC Periodic Updates | Under RBI guidelines, how often must high-risk customer KYC be updated? | [indian_finance] KYC & Compliance (Banking and Di... (0.707) | [indian_finance] KYC & Compliance (Banking and Di... (+6.47) | = Top 1 maintained |
| Q03 | Cyber Safety & Fraud | What precautions should customers take to avoid digital arrest scams? | [indian_finance] Digital Arrest Scams (Cyber Frau... (0.573) | [indian_finance] Digital Arrest Fraud (Fraud and ... (+0.39) | ▲ Vector #3 promoted to #1 |
| Q04 | Fraud Reporting & Redressal | What should a customer do if an unauthorized AePS withdrawal occurs? | [indian_finance] AePS Fraud (Fraud and Cyber Safe... (0.613) | [indian_finance] AePS Fraud (Fraud and Cyber Safe... (+4.95) | = Top 1 maintained |
| Q05 | Account Nomination | What are the rules related to bank account nominee? | [indian_finance] Bank Accounts - Nomination (Bank... (0.540) | [indian_finance] Pension & Senior Citizen Banking... (-3.06) | ▲ Vector #4 promoted to #1 |
| Q06 | Deceased Depositor Claims | What is the RBI procedure for settlement of claims in deceased depositors' accounts? | [indian_finance] Death Claim Settlement Process (... (0.523) | [rbi_circular_qa] RBI_2024-2025_104Ref.No.DoS.CO.P... (-1.94) | ▲ Vector #7 promoted to #1 |
| Q07 | Wire Transfers & Payments | How do RTGS and NEFT relate to India's electronic funds transfer infrastructure? | [indian_finance] Money Transfers - NEFT vs RTGS D... (0.566) | [indian_finance] Mobile & Internet Banking - RTGS... (-1.13) | ▲ Vector #4 promoted to #1 |
| Q08 | Payment Limits & Charges | What is the difference between NEFT and RTGS for a regular user transferring small amounts? | [indian_finance] Money Transfers - NEFT vs RTGS D... (0.775) | [indian_finance] Money Transfers - NEFT vs RTGS D... (+13.14) | = Top 1 maintained |
| Q09 | Lending & Interest Rates | What are the RBI rules regarding loan foreclosure charges on floating rate term loans? | [indian_finance] Personal Loan (Credit and Borrow... (0.575) | [indian_finance] Personal Loan (Credit and Borrow... (+1.19) | = Top 1 maintained |
| Q10 | Loan Restructuring & DCCO | What is the asset classification of project loans when the DCCO is extended? | [rbi_circular_qa] RBI_2022-2023_15DOR.STR.REC.4_21... (0.602) | [rbi_circular_qa] RBI_2022-2023_15DOR.STR.REC.4_21... (+3.17) | = Top 1 maintained |
| Q11 | Deposit Insurance | What is the maximum deposit insurance coverage provided by DICGC per depositor? | [indian_finance] DICGC Deposit Insurance (Insuran... (0.723) | [indian_finance] DICGC Deposit Insurance (Insuran... (+4.26) | = Top 1 maintained |
| Q12 | Liquid Funds & Wealth Parking | What is a liquid fund, and is it safe to park money in it for 1-3 months? | [indian_finance] Mutual Funds - SIP (Investment)... (0.604) | [indian_finance] Mutual Funds - SIP (Investment)... (+2.14) | = Top 1 maintained |
| Q13 | Currency Management | Why is it important for banks to maintain data on the amount of ₹2000 banknotes exchanged and deposited? | [rbi_circular_qa] RBI_2023-2024_33DCM(Plg) No.S-23... (0.739) | [rbi_circular_qa] RBI_2023-2024_33DCM(Plg) No.S-23... (-1.01) | = Top 1 maintained |
| Q14 | Startup & Wealth Taxation | Does Angel Tax under Section 56(2)(viib) apply to LLPs? | [indian_finance] Angel Tax Regulations & Business... (0.755) | [indian_finance] Angel Tax Legal Scope (Entrepren... (+5.89) | ▲ Vector #3 promoted to #1 |
| Q15 | Grievance Redressal | What measures should banks take to handle pensioner complaints and assess the quality of pension-related services? | [rbi_circular_qa] RBI_2025-2026_05CO.DGBA.GBD.No.S... (0.535) | [rbi_circular_qa] RBI_2025-2026_05CO.DGBA.GBD.No.S... (+2.66) | = Top 1 maintained |

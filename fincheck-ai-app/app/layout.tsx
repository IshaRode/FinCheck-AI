import type { Metadata } from 'next';
import './globals.css';
import { SidebarProvider } from '@/components/layout/SidebarContext';

export const metadata: Metadata = {
  title: 'FinCheck AI — Retrieve. Verify. Advise.',
  description:
    'AI-powered financial knowledge assistant for the Wealth Division. Access approved investment policies, tax rules, product brochures, and compliance guidelines instantly.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <SidebarProvider>{children}</SidebarProvider>
      </body>
    </html>
  );
}

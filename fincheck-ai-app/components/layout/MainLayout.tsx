'use client';
// components/layout/MainLayout.tsx
import React from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useSidebar } from './SidebarContext';

interface MainLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}

export function MainLayout({ children, title, subtitle }: MainLayoutProps) {
  const { isCollapsed, mounted } = useSidebar();

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#f0f2f7' }}>
      <Sidebar />
      <div
        className={`${
          mounted ? 'transition-all duration-300 ease-in-out' : ''
        } ${isCollapsed ? 'ml-[72px]' : 'ml-[260px]'}`}
      >
        <Header title={title} subtitle={subtitle} />
        <main className="pt-[60px] min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
}

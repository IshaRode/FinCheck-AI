'use client';
import React from 'react';
import Link from 'next/link';
import { Search, LogOut, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useSidebar } from './SidebarContext';

interface HeaderProps {
  title: string;
  subtitle: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { isCollapsed, toggleSidebar, mounted } = useSidebar();

  return (
    <header
      className={`fixed top-0 right-0 h-[60px] bg-white border-b border-gray-200 flex items-center px-6 gap-4 z-20 ${mounted ? 'transition-all duration-300 ease-in-out' : ''
        } ${isCollapsed ? 'left-[72px]' : 'left-[260px]'}`}
    >
      {/* Left: Sidebar toggle + Title + subtitle */}
      <div className="flex items-center gap-3 flex-1 min-w-0">
        <button
          onClick={toggleSidebar}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="p-1.5 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors flex-shrink-0"
        >
          {isCollapsed ? <PanelLeftOpen size={18} /> : <PanelLeftClose size={18} />}
        </button>
        <div className="min-w-0">
          <h1 className="text-sm font-semibold text-gray-900 leading-tight truncate">{title}</h1>
          <p className="text-xs text-gray-400 leading-tight truncate">{subtitle}</p>
        </div>
      </div>

      {/* Right: Search + notification + divider + user + logout */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <div className="relative">
          <Search
            size={14}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            placeholder="Search documents, questions..."
            className="pl-8 pr-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-700 placeholder-gray-400 focus:outline-none focus:border-blue-400 focus:bg-white transition-colors w-56"
            aria-label="Search documents and questions"
          />
        </div>

        {/* Vertical divider */}
        <div className="w-px h-6 bg-gray-200" />

        {/* User */}
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center flex-shrink-0">
            <span className="text-white text-xs font-semibold">IS</span>
          </div>
          <div className="hidden sm:block">
            <div className="text-xs font-semibold text-gray-900 leading-tight">Isha Rode</div>
            <div className="text-[10px] text-gray-400 leading-tight">Wealth Division</div>
          </div>
        </div>

        {/* Logout Button */}
        <Link
          href="/"
          title="Sign out of FinCheck AI"
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:text-rose-600 hover:bg-rose-50 transition-all border border-gray-200 hover:border-rose-200 ml-1"
        >
          <LogOut size={13} className="text-slate-500 group-hover:text-rose-600" />
          <span className="hidden md:inline">Log Out</span>
        </Link>
      </div>
    </header>
  );
}

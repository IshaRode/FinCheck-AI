'use client';
import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  MessageSquare,
  BookOpen,
  Clock,
  Bookmark,
  Settings,
  LogOut,
} from 'lucide-react';
import { useSidebar } from './SidebarContext';

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

const mainNav: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard', icon: <LayoutDashboard size={16} /> },
  { label: 'Ask FinCheck', href: '/ask', icon: <MessageSquare size={16} /> },
  { label: 'Knowledge Base', href: '/knowledge-base', icon: <BookOpen size={16} /> },
];

const historyNav: NavItem[] = [
  { label: 'Recent Questions', href: '/recent-questions', icon: <Clock size={16} /> },
  { label: 'Saved Answers', href: '/saved-answers', icon: <Bookmark size={16} /> },
];

const systemNav: NavItem[] = [
  { label: 'Settings', href: '/settings', icon: <Settings size={16} /> },
];

function NavGroup({
  label,
  items,
  isCollapsed,
}: {
  label: string;
  items: NavItem[];
  isCollapsed: boolean;
}) {
  const pathname = usePathname();
  return (
    <div className="mb-4">
      {!isCollapsed ? (
        <p className="text-[10px] font-semibold tracking-widest text-slate-500 uppercase px-3 mb-1.5 truncate">
          {label}
        </p>
      ) : (
        <div className="w-6 h-px bg-white/10 mx-auto my-2" />
      )}
      <ul className="space-y-0.5">
        {items.map((item) => {
          const isActive = pathname === item.href;
          return (
            <li key={item.href}>
              <Link
                href={item.href}
                title={isCollapsed ? item.label : undefined}
                className={`flex items-center rounded-lg text-sm transition-all group relative ${isCollapsed ? 'justify-center p-2.5' : 'gap-2.5 px-3 py-2'
                  } ${isActive
                    ? 'bg-[#1e2d4a] text-white font-medium'
                    : 'text-slate-400 hover:bg-[#1a2540] hover:text-slate-200'
                  }`}
              >
                <span
                  className={`flex-shrink-0 ${isActive ? 'text-blue-400' : 'text-slate-500 group-hover:text-slate-300'
                    }`}
                >
                  {item.icon}
                </span>
                {!isCollapsed && (
                  <>
                    <span className="flex-1 truncate">{item.label}</span>
                    {isActive && <span className="sidebar-active-dot" />}
                  </>
                )}
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function Sidebar() {
  const { isCollapsed, mounted } = useSidebar();

  return (
    <aside
      className={`fixed left-0 top-0 h-screen flex flex-col z-30 ${mounted ? 'transition-all duration-300 ease-in-out' : ''
        } ${isCollapsed ? 'w-[72px]' : 'w-[260px]'}`}
      style={{ backgroundColor: '#0f1629' }}
    >
      {/* Logo */}
      <div
        className={`flex items-center border-b border-white/5 transition-all ${isCollapsed ? 'justify-center px-2 py-5' : 'gap-3 px-4 py-5'
          }`}
      >
        <div className="w-10 h-10 rounded-full overflow-hidden flex items-center justify-center flex-shrink-0 ring-1 ring-blue-500/20 shadow-md shadow-blue-500/20">
          <Image
            src="/logo.png"
            alt="FinCheck AI"
            width={40}
            height={40}
            className="w-full h-full object-cover"
          />
        </div>
        {!isCollapsed && (
          <div className="min-w-0 transition-opacity duration-200">
            <div className="text-white font-semibold text-sm leading-tight truncate">
              FinCheck AI
            </div>
            <div className="text-[9px] font-medium tracking-widest text-slate-500 uppercase mt-0.5 truncate">
              RETRIEVE. VERIFY. ADVISE.
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 pt-4 pb-2">
        <NavGroup label="Main" items={mainNav} isCollapsed={isCollapsed} />
        <NavGroup label="History" items={historyNav} isCollapsed={isCollapsed} />
        <NavGroup label="System" items={systemNav} isCollapsed={isCollapsed} />
      </nav>

      {/* User footer */}
      <div
        className={`border-t border-white/5 transition-all ${isCollapsed
          ? 'p-2 flex flex-col items-center gap-2.5'
          : 'px-3 py-3 flex items-center gap-2.5'
          }`}
      >
        <div
          title="Isha Rode"
          className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0"
        >
          <span className="text-white text-xs font-semibold">IS</span>
        </div>
        {!isCollapsed && (
          <div className="flex-1 min-w-0">
            <div className="text-white text-xs font-medium truncate">Isha Rode</div>
            <div className="text-slate-500 text-[10px] truncate">Relationship Manager</div>
          </div>
        )}
        <Link
          href="/"
          title="Sign out of FinCheck AI"
          aria-label="Log Out"
          className="w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-rose-400 hover:bg-rose-500/15 transition-all flex-shrink-0"
        >
          <LogOut size={15} />
        </Link>
      </div>
    </aside>
  );
}

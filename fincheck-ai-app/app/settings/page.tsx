'use client';
// app/settings/page.tsx
import React, { useState } from 'react';
import { MainLayout } from '@/components/layout/MainLayout';
import { Card } from '@/components/ui/Card';
import { User, Bell, Shield, LogOut, ChevronRight } from 'lucide-react';
import { useRouter } from 'next/navigation';

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="flex items-center gap-2.5 mb-4">
      <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center text-gray-600">
        {icon}
      </div>
      <h2 className="text-sm font-semibold text-gray-900">{title}</h2>
    </div>
  );
}

function SettingRow({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 last:border-0">
      <div className="min-w-0">
        <div className="text-sm text-gray-800">{label}</div>
        {description && <div className="text-xs text-gray-400 mt-0.5">{description}</div>}
      </div>
      {children && <div className="flex-shrink-0 ml-4">{children}</div>}
    </div>
  );
}

function Toggle({
  checked,
  onChange,
  id,
}: {
  checked: boolean;
  onChange: () => void;
  id: string;
}) {
  return (
    <button
      id={id}
      role="switch"
      aria-checked={checked}
      onClick={onChange}
      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
        checked ? 'bg-blue-600' : 'bg-gray-300'
      }`}
    >
      <span className="sr-only">Toggle</span>
      <span
        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow transition-transform ${
          checked ? 'translate-x-4' : 'translate-x-1'
        }`}
      />
    </button>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const [notifications, setNotifications] = useState(true);
  const [rememberQuestions, setRememberQuestions] = useState(true);
  const [conciseStyle, setConciseStyle] = useState(false);

  return (
    <MainLayout title="Settings" subtitle="Manage your preferences">
      <div className="px-7 py-7 max-w-2xl">
        {/* Profile */}
        <Card className="mb-5">
          <SectionHeader icon={<User size={15} />} title="Profile" />
          <SettingRow label="Name">
            <input
              type="text"
              defaultValue="Isha Rode"
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-900 focus:outline-none focus:border-blue-400 transition-colors w-48"
              aria-label="Full name"
            />
          </SettingRow>
          <SettingRow label="Work Email">
            <input
              type="email"
              defaultValue="isha.rode@bankname.com"
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-500 focus:outline-none focus:border-blue-400 transition-colors w-48 bg-gray-50"
              aria-label="Work email"
              readOnly
            />
          </SettingRow>
          <SettingRow label="Department">
            <input
              type="text"
              defaultValue="Wealth Division"
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-900 focus:outline-none focus:border-blue-400 transition-colors w-48"
              aria-label="Department"
            />
          </SettingRow>
          <SettingRow label="Role">
            <input
              type="text"
              defaultValue="Relationship Manager"
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-900 focus:outline-none focus:border-blue-400 transition-colors w-48"
              aria-label="Role"
            />
          </SettingRow>
          <div className="mt-4">
            <button className="px-4 py-2 text-xs font-semibold rounded-lg text-white transition-colors hover:opacity-90" style={{ backgroundColor: '#0f1629' }}>
              Save Changes
            </button>
          </div>
        </Card>

        {/* Preferences */}
        <Card className="mb-5">
          <SectionHeader icon={<Bell size={15} />} title="Preferences" />
          <SettingRow
            label="Default response style"
            description="How FinCheck AI formats its answers"
          >
            <select
              className="text-xs border border-gray-200 rounded-lg px-3 py-1.5 text-gray-700 focus:outline-none focus:border-blue-400 transition-colors bg-gray-50"
              aria-label="Response style"
            >
              <option>Detailed</option>
              <option>Concise</option>
              <option>Bullet points</option>
            </select>
          </SettingRow>
          <SettingRow
            label="Notifications"
            description="Receive alerts about document updates"
          >
            <Toggle
              id="notifications-toggle"
              checked={notifications}
              onChange={() => setNotifications(!notifications)}
            />
          </SettingRow>
          <SettingRow
            label="Remember recent questions"
            description="Save question history for quick access"
          >
            <Toggle
              id="remember-questions-toggle"
              checked={rememberQuestions}
              onChange={() => setRememberQuestions(!rememberQuestions)}
            />
          </SettingRow>
        </Card>

        {/* Security */}
        <Card>
          <SectionHeader icon={<Shield size={15} />} title="Security" />
          <SettingRow
            label="Current session"
            description="Signed in since today at 9:00 AM · Singapore"
          >
            <span className="text-xs text-emerald-600 font-medium flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              Active
            </span>
          </SettingRow>
          <SettingRow label="Password" description="Last changed 3 months ago">
            <button className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-0.5 transition-colors">
              Change <ChevronRight size={12} />
            </button>
          </SettingRow>
          <SettingRow label="Two-factor authentication" description="Add an extra layer of security">
            <button className="text-xs text-blue-600 hover:text-blue-700 font-medium flex items-center gap-0.5 transition-colors">
              Set up <ChevronRight size={12} />
            </button>
          </SettingRow>
          <div className="mt-4">
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg text-red-600 border border-red-200 hover:bg-red-50 transition-colors"
              aria-label="Sign out"
            >
              <LogOut size={13} />
              Sign Out
            </button>
          </div>
        </Card>
      </div>
    </MainLayout>
  );
}

// components/ui/Badge.tsx
import React from 'react';
import { CheckCircle, AlertTriangle, Archive, Clock } from 'lucide-react';

type BadgeVariant = 'approved' | 'archived' | 'pending' | 'answered' | 'insufficient';

interface BadgeProps {
  variant: BadgeVariant;
  children?: React.ReactNode;
  showIcon?: boolean;
  className?: string;
}

const variantConfig: Record<
  BadgeVariant,
  { bg: string; text: string; border: string; icon: React.ReactNode; label: string }
> = {
  approved: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    icon: <CheckCircle size={11} />,
    label: 'Approved',
  },
  archived: {
    bg: 'bg-gray-100',
    text: 'text-gray-500',
    border: 'border-gray-200',
    icon: <Archive size={11} />,
    label: 'Archived',
  },
  pending: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
    icon: <Clock size={11} />,
    label: 'Pending Review',
  },
  answered: {
    bg: 'bg-emerald-50',
    text: 'text-emerald-700',
    border: 'border-emerald-200',
    icon: <CheckCircle size={11} />,
    label: 'Answered',
  },
  insufficient: {
    bg: 'bg-amber-50',
    text: 'text-amber-700',
    border: 'border-amber-200',
    icon: <AlertTriangle size={11} />,
    label: 'Insufficient Info',
  },
};

export function Badge({ variant, children, showIcon = true, className = '' }: BadgeProps) {
  const config = variantConfig[variant];
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium border ${config.bg} ${config.text} ${config.border} ${className}`}
    >
      {showIcon && config.icon}
      {children ?? config.label}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, BadgeVariant> = {
    Approved: 'approved',
    Archived: 'archived',
    'Pending Review': 'pending',
    Answered: 'answered',
    'Insufficient Info': 'insufficient',
  };
  const variant = map[status] ?? 'archived';
  return <Badge variant={variant} />;
}

// components/ui/KpiCard.tsx
import React from 'react';

interface KpiCardProps {
  value: number | string;
  label: string;
  icon?: React.ReactNode;
  valueColor?: string;
  variant?: 'default' | 'green' | 'gray' | 'amber';
  className?: string;
}

const variantStyles: Record<string, { border: string; valueCls: string }> = {
  default: { border: 'border-gray-200', valueCls: 'text-blue-600' },
  green: { border: 'border-green-200', valueCls: 'text-emerald-600' },
  gray: { border: 'border-gray-200', valueCls: 'text-gray-500' },
  amber: { border: 'border-amber-200', valueCls: 'text-amber-600' },
};

export function KpiCard({ value, label, icon, variant = 'default', className = '' }: KpiCardProps) {
  const styles = variantStyles[variant];
  return (
    <div
      className={`bg-white border ${styles.border} rounded-xl p-5 flex flex-col gap-3 ${className}`}
    >
      {icon && (
        <div className="w-9 h-9 rounded-lg bg-gray-50 border border-gray-200 flex items-center justify-center text-gray-500">
          {icon}
        </div>
      )}
      <div>
        <div className={`text-3xl font-bold ${styles.valueCls}`}>{value}</div>
        <div className="text-sm text-gray-500 mt-0.5">{label}</div>
      </div>
    </div>
  );
}

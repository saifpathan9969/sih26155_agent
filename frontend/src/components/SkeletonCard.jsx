import React from 'react';

export default function SkeletonCard({ lines = 4, className = '' }) {
  return (
    <div className={`p-4 rounded-xl border border-slate-800 bg-slate-900/40 space-y-3 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="h-4 w-32 rounded shimmer" />
        <div className="h-4 w-16 rounded-full shimmer" />
      </div>
      <div className="space-y-2 pt-1">
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className="h-3 rounded shimmer"
            style={{ width: `${Math.max(45, 95 - i * 15)}%` }}
          />
        ))}
      </div>
    </div>
  );
}

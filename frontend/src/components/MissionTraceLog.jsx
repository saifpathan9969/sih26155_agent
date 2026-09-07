import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Terminal, CheckCircle2, AlertCircle, Play, ArrowDownCircle } from 'lucide-react';

export default function MissionTraceLog({ trace = [], isRunning = false, onComplete }) {
  const [displayedLines, setDisplayedLines] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const containerRef = useRef(null);

  // Replay effect: reveal lines progressively to simulate live execution
  useEffect(() => {
    if (!trace || trace.length === 0) {
      setDisplayedLines([]);
      setCurrentIndex(0);
      return;
    }

    if (currentIndex < trace.length) {
      const timer = setTimeout(() => {
        setDisplayedLines(prev => [...prev, trace[currentIndex]]);
        setCurrentIndex(prev => prev + 1);
      }, 70); // 70ms cadence for snappy yet realistic live terminal feed

      return () => clearTimeout(timer);
    } else if (onComplete && currentIndex === trace.length) {
      onComplete();
    }
  }, [trace, currentIndex, onComplete]);

  // Auto-scroll to bottom as lines appear
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [displayedLines]);

  const getLineStyle = (line) => {
    if (line.startsWith('[') && line.includes(']')) {
      return 'text-brand-300 font-semibold border-l-2 border-brand-500 pl-2 my-1';
    }
    if (line.includes('CONFIRMED') || line.includes('✓') || line.includes('[OK]')) {
      return 'text-emerald-400 font-medium pl-4';
    }
    if (line.includes('REJECTED') || line.includes('✗') || line.includes('NO MAPPING')) {
      return 'text-amber-400 font-medium pl-4';
    }
    if (line.startsWith('=')) {
      return 'text-slate-600';
    }
    return 'text-slate-300 pl-4';
  };

  return (
    <div className="glass-panel rounded-xl overflow-hidden border border-slate-800 bg-[#060a14] shadow-2xl flex flex-col h-[460px]">
      {/* Terminal Title Bar */}
      <div className="bg-[#0b1120] px-4 py-2.5 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-rose-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>
          <span className="text-xs font-mono text-slate-400 ml-2 flex items-center gap-1.5">
            <Terminal className="w-3.5 h-3.5 text-brand-400" />
            SECURITY AGENT ORCHESTRATION TRACE
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-mono text-slate-400">
            {displayedLines.length}/{trace.length} events
          </span>
          {currentIndex < trace.length ? (
            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-brand-400 bg-brand-950/60 px-2 py-0.5 rounded border border-brand-500/30 animate-pulse">
              <Play className="w-2.5 h-2.5" /> REPLAYING
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] font-mono text-emerald-400 bg-emerald-950/60 px-2 py-0.5 rounded border border-emerald-500/30">
              <CheckCircle2 className="w-2.5 h-2.5" /> COMPLETE
            </span>
          )}
        </div>
      </div>

      {/* Terminal Body */}
      <div
        ref={containerRef}
        className="p-4 font-mono text-xs overflow-y-auto flex-1 terminal-scroll space-y-1 select-text"
      >
        {displayedLines.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs gap-2">
            <Terminal className="w-8 h-8 opacity-30 text-brand-400" />
            <span>Click "▶ START AUTONOMOUS AUDIT" to run the mission pipeline</span>
          </div>
        )}

        {displayedLines.map((line, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.15 }}
            className={`leading-relaxed ${getLineStyle(line)}`}
          >
            {line}
          </motion.div>
        ))}

        {currentIndex < trace.length && (
          <motion.span
            animate={{ opacity: [1, 0, 1] }}
            transition={{ repeat: Infinity, duration: 0.8 }}
            className="inline-block w-2 h-4 bg-brand-400 align-middle ml-1"
          />
        )}
      </div>
    </div>
  );
}

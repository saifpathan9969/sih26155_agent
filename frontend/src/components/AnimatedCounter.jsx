import React, { useState, useEffect } from 'react';

/**
 * High-performance 60fps cubic ease-out counter component
 * Derived from the Master Animation Engine (Section 3.4 of ANIMATIONS_DOCUMENTATION.md)
 */
export default function AnimatedCounter({
  target = 0,
  duration = 1500,
  prefix = '',
  suffix = '',
  className = '',
}) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    // If target is not a numeric type, parse it or display directly
    const numericTarget = typeof target === 'number' ? target : parseFloat(String(target).replace(/[^0-9.-]+/g, ''));

    if (isNaN(numericTarget)) {
      setDisplayValue(target);
      return;
    }

    const start = 0;
    const startTime = performance.now();
    let animId;

    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Cubic ease out: 1 - (1 - t)^3
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(start + (numericTarget - start) * easeOut);
      setDisplayValue(current);

      if (progress < 1) {
        animId = requestAnimationFrame(update);
      } else {
        setDisplayValue(numericTarget);
      }
    }

    animId = requestAnimationFrame(update);

    return () => {
      if (animId) cancelAnimationFrame(animId);
    };
  }, [target, duration]);

  return (
    <span className={`animate-count-up ${className}`}>
      {prefix}
      {typeof displayValue === 'number' ? displayValue.toLocaleString() : displayValue}
      {suffix}
    </span>
  );
}

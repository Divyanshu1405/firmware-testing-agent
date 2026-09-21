import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';

/**
 * Apple-style metric display — large number with label, minimal chrome.
 */
export default function MetricCard({ label, value, suffix = '', icon: Icon, delay = 0 }) {
  const [displayValue, setDisplayValue] = useState(0);
  const numericValue = typeof value === 'number' ? value : parseFloat(value) || 0;

  useEffect(() => {
    if (numericValue === 0) { setDisplayValue(0); return; }
    const duration = 800;
    const startTime = Date.now();
    const animate = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(eased * numericValue * 10) / 10);
      if (progress < 1) requestAnimationFrame(animate);
      else setDisplayValue(numericValue);
    };
    const timer = setTimeout(() => requestAnimationFrame(animate), delay * 1000);
    return () => clearTimeout(timer);
  }, [numericValue, delay]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-primary)',
        borderRadius: 'var(--radius-lg)',
        padding: '24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <span className="text-overline">{label}</span>
        {Icon && <Icon size={16} style={{ color: 'var(--text-muted)' }} />}
      </div>
      <div style={{ fontSize: '2.25rem', fontWeight: 700, letterSpacing: '-0.04em', color: 'var(--text-primary)' }}>
        {Number.isInteger(numericValue) ? Math.round(displayValue) : displayValue.toFixed(1)}
        {suffix && <span style={{ fontSize: '1.25rem', fontWeight: 500, marginLeft: 2, opacity: 0.6 }}>{suffix}</span>}
      </div>
    </motion.div>
  );
}

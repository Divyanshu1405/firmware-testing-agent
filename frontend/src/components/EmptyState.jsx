import React from 'react';
import { motion } from 'framer-motion';
import { Inbox } from 'lucide-react';

export default function EmptyState({
  icon: Icon = Inbox,
  title = 'No data yet',
  description = 'Run a pipeline to generate results.',
  action,
  actionLabel = 'Get Started',
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', padding: '80px 24px', textAlign: 'center',
      }}
    >
      <div style={{
        width: 56, height: 56, borderRadius: '50%',
        border: '1px solid var(--border-primary)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        marginBottom: 24,
      }}>
        <Icon size={24} style={{ color: 'var(--text-muted)' }} />
      </div>
      <h3 style={{ fontSize: '1.125rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
        {title}
      </h3>
      <p style={{ fontSize: '0.9375rem', color: 'var(--text-tertiary)', maxWidth: 360, lineHeight: 1.5, marginBottom: action ? 24 : 0 }}>
        {description}
      </p>
      {action && (
        <button className="btn btn-primary" onClick={action}>{actionLabel}</button>
      )}
    </motion.div>
  );
}

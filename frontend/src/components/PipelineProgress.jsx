import React from 'react';
import { motion } from 'framer-motion';
import { PIPELINE_STAGES } from '../utils/constants';
import { CheckCircle2 } from 'lucide-react';

/**
 * Apple-style pipeline progress — clean horizontal steps with minimal lines.
 */
export default function PipelineProgress({ currentStage = 0, status = 'idle' }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 0, width: '100%' }}>
      {PIPELINE_STAGES.map((stage, idx) => {
        const isCompleted = currentStage > stage.id;
        const isCurrent = currentStage === stage.id;
        const isError = status === 'error' && isCurrent;

        let dotColor = 'var(--border-primary)';
        let textColor = 'var(--text-muted)';
        let lineColor = 'var(--border-primary)';

        if (isCompleted) {
          dotColor = 'var(--text-primary)';
          textColor = 'var(--text-secondary)';
          lineColor = 'var(--text-muted)';
        } else if (isCurrent && !isError) {
          dotColor = 'var(--text-primary)';
          textColor = 'var(--text-primary)';
        } else if (isError) {
          dotColor = 'var(--accent-danger)';
          textColor = 'var(--accent-danger)';
        }

        return (
          <React.Fragment key={stage.id}>
            {idx > 0 && (
              <div style={{
                flex: '0 0 auto', width: 32, height: 1,
                background: lineColor,
                transition: 'background 0.4s ease',
              }} />
            )}
            <div style={{
              flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column',
              alignItems: 'center', gap: 8, textAlign: 'center',
            }}>
              <motion.div
                animate={{ scale: isCurrent && status === 'running' ? [1, 1.2, 1] : 1 }}
                transition={{ duration: 1.5, repeat: isCurrent && status === 'running' ? Infinity : 0 }}
                style={{
                  width: 28, height: 28, borderRadius: '50%',
                  border: `1.5px solid ${dotColor}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: isCompleted ? 'var(--text-primary)' : 'transparent',
                  transition: 'all 0.3s ease',
                }}
              >
                {isCompleted ? (
                  <CheckCircle2 size={14} style={{ color: 'var(--black)' }} />
                ) : (
                  <span style={{
                    fontSize: '0.6875rem', fontWeight: 600, color: textColor,
                    fontFamily: '-apple-system, sans-serif',
                  }}>
                    {stage.id}
                  </span>
                )}
              </motion.div>
              <div style={{
                fontSize: '0.6875rem', fontWeight: 600, color: textColor,
                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%',
              }}>
                {stage.name}
              </div>
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ClipboardList } from 'lucide-react';
import Card from '../components/GlassCard';
import EmptyState from '../components/EmptyState';
import { usePipeline } from '../hooks/usePipeline';
import { ROUTES } from '../utils/constants';

export default function RequirementsPage() {
  const navigate = useNavigate();
  const pipeline = usePipeline();
  const reqs = pipeline.requirements || [];

  if (reqs.length === 0) {
    return (
      <div className="page-container">
        <div className="page-header"><h1>Requirements</h1><p>Extracted operational constraints.</p></div>
        <EmptyState icon={ClipboardList} title="No requirements" description="Run the pipeline to extract requirements from your specification."
          action={() => navigate(ROUTES.PIPELINE)} actionLabel="Run Pipeline" />
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
          <div><h1>Requirements</h1><p>Extracted operational constraints.</p></div>
          <span className="badge badge-neutral">{reqs.length} total</span>
        </div>
      </div>

      <Card delay={0.05}>
        <div style={{ overflowX: 'auto' }}>
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Description</th>
                <th>Source</th>
                <th>Threshold</th>
                <th>Time</th>
                <th>Ambiguous</th>
              </tr>
            </thead>
            <tbody>
              {reqs.map((req, idx) => (
                <motion.tr key={req.id || idx} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: idx * 0.03 }}>
                  <td><span className="font-mono" style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{req.id}</span></td>
                  <td style={{ maxWidth: 400, lineHeight: 1.5 }}>{req.description}</td>
                  <td><span className="font-mono text-caption">{req.source}:{req.source_line}</span></td>
                  <td>{req.threshold != null ? <span className="font-mono">{req.threshold}°C</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                  <td>{req.time_value_ms != null ? <span className="font-mono">{req.time_value_ms} ms</span> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                  <td>{req.ambiguous ? <span className="badge badge-inconclusive" style={{ fontSize: '0.5625rem', padding: '2px 6px' }}>Yes</span> : <span className="text-caption">No</span>}</td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
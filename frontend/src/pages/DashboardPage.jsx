import React, { useEffect, useState } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Cpu, Activity, ShieldCheck, Clock, ChevronRight } from 'lucide-react';
import Card from '../components/GlassCard';
import MetricCard from '../components/MetricCard';
import PipelineProgress from '../components/PipelineProgress';
import { usePipeline } from '../hooks/usePipeline';
import { fetchApi } from '../hooks/useApi';
import { API, ROUTES } from '../utils/constants';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { healthData } = useOutletContext();
  const pipeline = usePipeline();
  const [fwCount, setFwCount] = useState(0);

  useEffect(() => {
    fetchApi(API.FIRMWARE_LIST).then((l) => setFwCount(l.length)).catch(() => {});
  }, []);

  const hasResults = pipeline.status === 'completed' && pipeline.summary;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>System overview and pipeline controls.</p>
      </div>

      {/* Metrics */}
      <div className="grid-4" style={{ marginBottom: 32 }}>
        <MetricCard label="Firmware" value={fwCount} icon={Cpu} delay={0.05} />
        <MetricCard
          label="System"
          value={healthData?.status === 'healthy' ? 1 : 0}
          suffix={healthData?.status === 'healthy' ? ' Active' : ' Down'}
          icon={Activity}
          delay={0.1}
        />
        <MetricCard label="Verdicts" value={hasResults ? pipeline.summary.total_verdicts : 0} icon={ShieldCheck} delay={0.15} />
        <MetricCard label="Pass Rate" value={hasResults ? pipeline.summary.verdict_rate : 0} suffix="%" delay={0.2} />
      </div>

      {/* Pipeline Status */}
      {pipeline.status !== 'idle' && (
        <Card delay={0.25} style={{ marginBottom: 32 }}>
          <h3 style={{ marginBottom: 16 }}>Pipeline Status</h3>
          <PipelineProgress currentStage={pipeline.currentStage} status={pipeline.status} />
        </Card>
      )}

      {/* Quick Launch or Results */}
      <div className="grid-2" style={{ marginBottom: 32 }}>
        <Card delay={0.3} variant="interactive" onClick={() => navigate(ROUTES.PIPELINE)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ marginBottom: 8 }}>Run Pipeline</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
                Configure firmware target, set execution mode, and launch the autonomous verification pipeline.
              </p>
            </div>
            <ArrowRight size={18} style={{ color: 'var(--text-muted)', flexShrink: 0, marginTop: 4 }} />
          </div>
        </Card>

        <Card delay={0.35} variant="interactive" onClick={() => navigate(ROUTES.FIRMWARE)}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ marginBottom: 8 }}>Firmware</h3>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
                Browse available binaries or upload custom .elf / .bin files for testing.
              </p>
            </div>
            <ArrowRight size={18} style={{ color: 'var(--text-muted)', flexShrink: 0, marginTop: 4 }} />
          </div>
        </Card>
      </div>

      {/* Results Summary */}
      {hasResults && (
        <>
          <Card delay={0.4} style={{ marginBottom: 32 }}>
            <h3 style={{ marginBottom: 20 }}>Verdict Breakdown</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {[
                { label: 'Passed', value: pipeline.summary.passed, color: 'var(--accent-success)' },
                { label: 'Failed', value: pipeline.summary.failed, color: 'var(--accent-danger)' },
                { label: 'Inconclusive', value: pipeline.summary.inconclusive, color: 'var(--accent-warning)' },
              ].map((item) => (
                <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <span style={{ fontSize: '0.8125rem', color: 'var(--text-tertiary)', minWidth: 100 }}>{item.label}</span>
                  <div style={{ flex: 1, height: 4, borderRadius: 2, background: 'var(--bg-surface)', overflow: 'hidden' }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${pipeline.summary.total_verdicts > 0 ? (item.value / pipeline.summary.total_verdicts) * 100 : 0}%` }}
                      transition={{ duration: 1, delay: 0.4, ease: [0.25, 0.1, 0.25, 1] }}
                      style={{ height: '100%', borderRadius: 2, background: item.color }}
                    />
                  </div>
                  <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--text-primary)', minWidth: 28, textAlign: 'right' }}>
                    {item.value}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {[
              { label: 'Requirements', route: ROUTES.REQUIREMENTS, count: pipeline.requirements.length },
              { label: 'Traces', route: ROUTES.TRACES, count: pipeline.traces.length },
              { label: 'Verdicts', route: ROUTES.VERDICTS, count: pipeline.verdicts.length },
              { label: 'Report', route: ROUTES.REPORT },
            ].map((link, idx) => (
              <motion.div
                key={link.route}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + idx * 0.05 }}
                onClick={() => navigate(link.route)}
                style={{
                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                  padding: '16px 0', borderBottom: '1px solid var(--border-subtle)',
                  cursor: 'pointer', transition: 'opacity 0.15s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.opacity = '0.7'}
                onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}
              >
                <span style={{ fontSize: '0.9375rem', fontWeight: 500 }}>{link.label}</span>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {link.count != null && (
                    <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{link.count}</span>
                  )}
                  <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                </div>
              </motion.div>
            ))}
          </div>
        </>
      )}

      {pipeline.lastRunAt && (
        <div style={{ marginTop: 32, display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          <Clock size={12} />
          <span>Last run: {new Date(pipeline.lastRunAt).toLocaleString()} · {pipeline.mode} · {pipeline.firmware}</span>
        </div>
      )}
    </div>
  );
}

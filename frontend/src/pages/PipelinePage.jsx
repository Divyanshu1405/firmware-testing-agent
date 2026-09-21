import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play, Wifi, WifiOff, ArrowRight, Loader2, AlertTriangle } from 'lucide-react';
import Card from '../components/GlassCard';
import PipelineProgress from '../components/PipelineProgress';
import MetricCard from '../components/MetricCard';
import { usePipeline } from '../hooks/usePipeline';
import { fetchApi } from '../hooks/useApi';
import { API, ROUTES } from '../utils/constants';

export default function PipelinePage() {
  const navigate = useNavigate();
  const pipeline = usePipeline();
  const [firmwares, setFirmwares] = useState([]);
  const [selectedFw, setSelectedFw] = useState(pipeline.firmware);
  const [mode, setMode] = useState(pipeline.mode);
  const [specText, setSpecText] = useState(pipeline.specText);

  useEffect(() => {
    fetchApi(API.FIRMWARE_LIST).then(setFirmwares).catch(() => {});
    if (!specText) fetchApi(API.SPEC).then((d) => setSpecText(d.spec_text || '')).catch(() => {});
  }, []);

  const handleRun = async () => {
    try { await pipeline.runPipeline(selectedFw, specText, mode); } catch {}
  };

  const isRunning = pipeline.status === 'running';
  const isCompleted = pipeline.status === 'completed';
  const isError = pipeline.status === 'error';

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Pipeline</h1>
        <p>Configure and execute autonomous verification.</p>
      </div>

      {/* Progress */}
      <Card delay={0.05} style={{ marginBottom: 32 }}>
        <PipelineProgress currentStage={pipeline.currentStage} status={pipeline.status} />
      </Card>

      <div className="grid-2">
        {/* Config */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Card delay={0.1}>
            <h3 style={{ marginBottom: 12 }}>Target</h3>
            <select value={selectedFw} onChange={(e) => setSelectedFw(e.target.value)} disabled={isRunning}>
              {firmwares.map((fw) => (
                <option key={fw.path} value={fw.path}>
                  {fw.name} ({fw.category}{fw.size_bytes ? ` · ${Math.round(fw.size_bytes / 1024)} KB` : ''})
                </option>
              ))}
            </select>
          </Card>

          <Card delay={0.15}>
            <h3 style={{ marginBottom: 12 }}>Mode</h3>
            {[
              { value: 'offline', title: 'Offline', desc: 'Deterministic · No API keys', icon: WifiOff },
              { value: 'live', title: 'Live LLM', desc: 'Gemini / OpenAI · Requires key', icon: Wifi },
            ].map((opt) => (
              <label key={opt.value} style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 14px', borderRadius: 'var(--radius-sm)', marginBottom: 6,
                background: mode === opt.value ? 'rgba(255,255,255,0.04)' : 'transparent',
                border: `1px solid ${mode === opt.value ? 'var(--border-strong)' : 'var(--border-subtle)'}`,
                cursor: isRunning ? 'not-allowed' : 'pointer', opacity: isRunning ? 0.5 : 1,
                transition: 'all 0.15s ease',
              }}>
                <input type="radio" name="mode" value={opt.value} checked={mode === opt.value}
                  onChange={() => setMode(opt.value)} disabled={isRunning}
                  style={{ accentColor: '#fff' }} />
                <opt.icon size={15} style={{ color: 'var(--text-muted)' }} />
                <div>
                  <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>{opt.title}</div>
                  <div className="text-caption">{opt.desc}</div>
                </div>
              </label>
            ))}
          </Card>

          <motion.button
            className="btn btn-primary btn-lg"
            onClick={handleRun} disabled={isRunning}
            whileHover={!isRunning ? { scale: 1.02 } : {}}
            whileTap={!isRunning ? { scale: 0.98 } : {}}
            style={{ width: '100%' }}
          >
            {isRunning ? (
              <><span className="spinner" style={{ borderTopColor: '#000', borderColor: 'rgba(0,0,0,0.2)' }} /> Running...</>
            ) : (
              <><Play size={16} /> Run Pipeline</>
            )}
          </motion.button>

          {isError && pipeline.error && (
            <div style={{
              padding: '14px 16px', borderRadius: 'var(--radius-sm)',
              border: '1px solid rgba(255,69,58,0.2)', fontSize: '0.8125rem',
              color: 'var(--accent-danger)', display: 'flex', alignItems: 'flex-start', gap: 10,
            }}>
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 1 }} />
              <span>{pipeline.error}</span>
            </div>
          )}
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {isCompleted && pipeline.summary ? (
            <>
              <div className="grid-2">
                <MetricCard label="Verdicts" value={pipeline.summary.total_verdicts} delay={0.2} />
                <MetricCard label="Pass Rate" value={pipeline.summary.verdict_rate} suffix="%" delay={0.25} />
              </div>
              <Card delay={0.3}>
                <h3 style={{ marginBottom: 16 }}>Results</h3>
                {[
                  { label: 'Requirements', route: ROUTES.REQUIREMENTS, count: pipeline.requirements.length },
                  { label: 'Traces', route: ROUTES.TRACES, count: pipeline.traces.length },
                  { label: 'Verdicts', route: ROUTES.VERDICTS, count: pipeline.verdicts.length },
                  { label: 'Report', route: ROUTES.REPORT },
                ].map((link) => (
                  <div key={link.route} onClick={() => navigate(link.route)} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '12px 0', borderBottom: '1px solid var(--border-subtle)',
                    cursor: 'pointer', transition: 'opacity 0.15s',
                  }} onMouseEnter={(e) => e.currentTarget.style.opacity = '0.6'} onMouseLeave={(e) => e.currentTarget.style.opacity = '1'}>
                    <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{link.label}</span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      {link.count != null && <span className="text-caption">{link.count}</span>}
                      <ArrowRight size={14} style={{ color: 'var(--text-muted)' }} />
                    </div>
                  </div>
                ))}
              </Card>
            </>
          ) : isRunning ? (
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px 0', gap: 16 }}>
                <div className="spinner spinner-lg" />
                <div style={{ fontSize: '0.9375rem', fontWeight: 500, color: 'var(--text-secondary)' }}>Executing pipeline...</div>
              </div>
            </Card>
          ) : (
            <Card>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '60px 0', gap: 12, textAlign: 'center' }}>
                <Play size={28} style={{ color: 'var(--text-muted)' }} />
                <div style={{ fontSize: '0.9375rem', color: 'var(--text-tertiary)' }}>
                  Configure target and mode, then run the pipeline.
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, AlertTriangle } from 'lucide-react';
import Card from '../components/GlassCard';
import JsonViewer from '../components/JsonViewer';
import EmptyState from '../components/EmptyState';
import StatusBadge from '../components/StatusBadge';
import { usePipeline } from '../hooks/usePipeline';
import { ROUTES, EVENT_KIND_COLORS } from '../utils/constants';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

export default function TracesPage() {
  const navigate = useNavigate();
  const pipeline = usePipeline();
  const traces = pipeline.traces || [];
  const [selectedIdx, setSelectedIdx] = useState(0);

  if (traces.length === 0) {
    return (
      <div className="page-container">
        <div className="page-header"><h1>Traces</h1><p>Simulation execution traces.</p></div>
        <EmptyState icon={Activity} title="No traces" description="Run the pipeline to capture simulation traces."
          action={() => navigate(ROUTES.PIPELINE)} actionLabel="Run Pipeline" />
      </div>
    );
  }

  const trace = traces[selectedIdx];

  // Build chart data from samples
  const chartData = (trace.samples || [])
    .filter((s) => typeof s.value === 'number')
    .map((s) => ({ t_ms: s.t_ms, value: s.value, channel: s.channel, dir: s.dir }));

  // Group by channel for lines
  const channels = [...new Set(chartData.map((d) => d.channel))];

  // Build per-channel series
  const seriesMap = {};
  chartData.forEach((d) => {
    if (!seriesMap[d.t_ms]) seriesMap[d.t_ms] = { t_ms: d.t_ms };
    seriesMap[d.t_ms][d.channel] = d.value;
  });
  const series = Object.values(seriesMap).sort((a, b) => a.t_ms - b.t_ms);

  const lineColors = ['#f5f5f7', '#6e6e73', '#a1a1a6', '#48484a'];

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Traces</h1>
        <p>Simulation execution traces and sensor data.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: 24 }}>
        {/* Trace Selector */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span className="text-overline" style={{ padding: '0 0 8px' }}>Test Traces</span>
          {traces.map((t, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedIdx(idx)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '10px 12px', borderRadius: 'var(--radius-sm)',
                background: selectedIdx === idx ? 'rgba(255,255,255,0.06)' : 'transparent',
                border: `1px solid ${selectedIdx === idx ? 'var(--border-strong)' : 'transparent'}`,
                color: selectedIdx === idx ? 'var(--text-primary)' : 'var(--text-tertiary)',
                cursor: 'pointer', fontSize: '0.8125rem', fontWeight: selectedIdx === idx ? 600 : 400,
                transition: 'all 0.15s ease', textAlign: 'left', width: '100%',
                fontFamily: "'SF Mono', monospace",
              }}
            >
              {t.test_id}
            </button>
          ))}
        </div>

        {/* Trace Detail */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* Meta */}
          <Card delay={0.05}>
            <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
              {[
                { label: 'Test ID', value: trace.test_id },
                { label: 'Firmware', value: trace.firmware },
                { label: 'Simulator', value: trace.sim },
                { label: 'Seed', value: trace.seed },
                { label: 'End Reason', value: trace.end_reason },
                { label: 'Samples', value: trace.samples?.length || 0 },
              ].map((item) => (
                <div key={item.label}>
                  <div className="text-overline" style={{ marginBottom: 4 }}>{item.label}</div>
                  <div className="font-mono" style={{ fontSize: '0.875rem', fontWeight: 600 }}>{item.value}</div>
                </div>
              ))}
            </div>
          </Card>

          {/* Chart */}
          {series.length > 0 && (
            <Card delay={0.1}>
              <h3 style={{ marginBottom: 16 }}>Samples Timeline</h3>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={series} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
                  <XAxis dataKey="t_ms" tick={{ fill: '#6e6e73', fontSize: 11 }} axisLine={{ stroke: 'var(--border-primary)' }} tickLine={false} />
                  <YAxis tick={{ fill: '#6e6e73', fontSize: 11 }} axisLine={{ stroke: 'var(--border-primary)' }} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#111', border: '1px solid var(--border-primary)', borderRadius: 8, fontSize: '0.8125rem', color: '#f5f5f7' }} />
                  {channels.map((ch, i) => (
                    <Line key={ch} type="monotone" dataKey={ch} stroke={lineColors[i % lineColors.length]} strokeWidth={1.5} dot={false} />
                  ))}
                  {(trace.events || []).map((evt, i) => (
                    <ReferenceLine key={i} x={evt.t_ms} stroke={EVENT_KIND_COLORS[evt.kind] || '#ff453a'} strokeDasharray="4 4" label={{ value: evt.kind, fill: '#ff453a', fontSize: 10 }} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* Events */}
          {trace.events && trace.events.length > 0 && (
            <Card delay={0.15}>
              <h3 style={{ marginBottom: 16 }}>Events</h3>
              {trace.events.map((evt, idx) => (
                <div key={idx} style={{
                  display: 'flex', alignItems: 'center', gap: 16,
                  padding: '10px 0', borderBottom: idx < trace.events.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                }}>
                  <AlertTriangle size={14} style={{ color: EVENT_KIND_COLORS[evt.kind] || 'var(--accent-danger)', flexShrink: 0 }} />
                  <span className="font-mono" style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', minWidth: 70 }}>{evt.t_ms} ms</span>
                  <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{evt.kind}</span>
                </div>
              ))}
            </Card>
          )}

          {/* Raw JSON */}
          <JsonViewer data={trace} title={`${trace.test_id}.json`} collapsible defaultExpanded={false} />
        </div>
      </div>
    </div>
  );
}
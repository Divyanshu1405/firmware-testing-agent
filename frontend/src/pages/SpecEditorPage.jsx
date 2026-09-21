import React, { useEffect, useState } from 'react';
import { FileText, RotateCcw, Eye } from 'lucide-react';
import Card from '../components/GlassCard';
import { usePipeline } from '../hooks/usePipeline';
import { fetchApi } from '../hooks/useApi';
import { API } from '../utils/constants';

export default function SpecEditorPage() {
  const pipeline = usePipeline();
  const [specText, setSpecText] = useState(pipeline.specText || '');
  const [previewReqs, setPreviewReqs] = useState([]);

  useEffect(() => {
    if (!specText) {
      fetchApi(API.SPEC).then((data) => {
        setSpecText(data.spec_text || '');
        pipeline.setField({ specText: data.spec_text || '' });
      }).catch(() => {});
    }
  }, []);

  useEffect(() => {
    const lines = specText.split('\n').filter((l) => l.trim());
    const reqs = [];
    lines.forEach((line, idx) => {
      const match = line.match(/^(\d+)\.\s+(.+)/);
      if (match) {
        const desc = match[2];
        const thresholdMatch = desc.match(/(\d+\.?\d*)\s*°?C/);
        const timeMatch = desc.match(/(\d+)\s*ms/);
        reqs.push({
          id: `R${match[1]}`, description: desc, source_line: idx + 1,
          threshold: thresholdMatch ? parseFloat(thresholdMatch[1]) : null,
          time_value_ms: timeMatch ? parseInt(timeMatch[1]) : null,
          ambiguous: desc.includes('SHOULD') || desc.includes('MAY'),
        });
      }
    });
    setPreviewReqs(reqs);
  }, [specText]);

  const handleReset = async () => {
    try {
      const data = await fetchApi(API.SPEC);
      setSpecText(data.spec_text || '');
      pipeline.setField({ specText: data.spec_text || '' });
    } catch {}
  };

  const handleChange = (e) => {
    setSpecText(e.target.value);
    pipeline.setField({ specText: e.target.value });
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Specification</h1>
        <p>Operational rules that define firmware behavior constraints.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Editor */}
        <Card delay={0.05}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3>Editor</h3>
            <button className="btn btn-ghost btn-sm" onClick={handleReset}>
              <RotateCcw size={13} /> Reset
            </button>
          </div>
          <textarea
            value={specText}
            onChange={handleChange}
            rows={20}
            placeholder="1. The main cooling fan MUST activate within 1000 ms..."
            style={{ minHeight: 420 }}
          />
          <div style={{ marginTop: 8, display: 'flex', gap: 16 }}>
            <span className="text-caption">{specText.split('\n').filter((l) => l.trim()).length} lines</span>
            <span className="text-caption">{specText.length} chars</span>
          </div>
        </Card>

        {/* Preview */}
        <Card delay={0.1}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <h3>Preview</h3>
            <span className="badge badge-neutral">{previewReqs.length} requirements</span>
          </div>
          <p className="text-caption" style={{ marginBottom: 20 }}>
            Client-side heuristic. Final extraction performed by LLM during pipeline execution.
          </p>

          {previewReqs.length === 0 ? (
            <div style={{ padding: '48px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
              No numbered requirements detected.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 0, maxHeight: 420, overflow: 'auto' }}>
              {previewReqs.map((req, idx) => (
                <div key={req.id} style={{
                  padding: '14px 0',
                  borderBottom: idx < previewReqs.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                      {req.id}
                    </span>
                    <span className="text-caption">Line {req.source_line}</span>
                    {req.ambiguous && <span className="badge badge-inconclusive" style={{ fontSize: '0.5625rem', padding: '2px 6px' }}>Ambiguous</span>}
                  </div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {req.description}
                  </div>
                  {(req.threshold !== null || req.time_value_ms !== null) && (
                    <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
                      {req.threshold !== null && (
                        <span className="font-mono text-caption">{req.threshold}°C</span>
                      )}
                      {req.time_value_ms !== null && (
                        <span className="font-mono text-caption">{req.time_value_ms} ms</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

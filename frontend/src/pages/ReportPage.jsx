import React, { useRef } from 'react';
import { FileBarChart, Download, Printer, ExternalLink } from 'lucide-react';
import { usePipeline } from '../hooks/usePipeline';

export default function ReportPage() {
  const pipeline = usePipeline();
  const iframeRef = useRef(null);

  const handlePrint = () => {
    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.focus();
      iframeRef.current.contentWindow.print();
    } else {
      window.open('/api/report', '_blank');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 52px)' }}>
      {/* Action Bar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '12px 40px',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <FileBarChart size={18} style={{ color: 'var(--text-muted)' }} />
          <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Verification Report</span>
          {pipeline.lastRunAt && (
            <span className="text-caption" style={{ marginLeft: 8 }}>
              Generated {new Date(pipeline.lastRunAt).toLocaleString()}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn btn-ghost btn-sm" onClick={() => window.open('/api/report', '_blank')}>
            <ExternalLink size={13} /> New Tab
          </button>
          <button className="btn btn-ghost btn-sm" onClick={handlePrint}>
            <Printer size={13} /> Print
          </button>
          <a href="/api/report/download" download="firmware_testing_report.html" className="btn btn-secondary btn-sm" style={{ textDecoration: 'none' }}>
            <Download size={13} /> Download
          </a>
        </div>
      </div>

      {/* Report iframe */}
      <div style={{ flex: 1, background: '#000' }}>
        <iframe
          ref={iframeRef}
          src="/api/report"
          title="Firmware Verification Report"
          style={{
            width: '100%', height: '100%', border: 'none',
            background: '#000',
          }}
        />
      </div>
    </div>
  );
}
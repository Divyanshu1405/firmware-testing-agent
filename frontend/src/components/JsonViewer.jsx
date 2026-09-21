import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check, ChevronDown, ChevronRight } from 'lucide-react';

export default function JsonViewer({
  data,
  title = 'JSON',
  maxHeight = '400px',
  collapsible = false,
  defaultExpanded = true,
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const [copied, setCopied] = useState(false);
  const jsonStr = typeof data === 'string' ? data : JSON.stringify(data, null, 2);

  const handleCopy = async () => {
    try { await navigator.clipboard.writeText(jsonStr); } catch { /* fallback */ }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Custom dark theme matching our monochrome palette
  const customStyle = {
    ...oneDark,
    'pre[class*="language-"]': {
      ...oneDark['pre[class*="language-"]'],
      background: '#0a0a0a',
    },
    'code[class*="language-"]': {
      ...oneDark['code[class*="language-"]'],
      background: '#0a0a0a',
    },
  };

  return (
    <div style={{
      border: '1px solid var(--border-primary)',
      borderRadius: 'var(--radius-md)',
      overflow: 'hidden',
      background: '#0a0a0a',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 14px', borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {collapsible && (
            <button onClick={() => setExpanded(!expanded)} style={{
              background: 'none', border: 'none', color: 'var(--text-muted)',
              cursor: 'pointer', padding: 0, display: 'flex',
            }}>
              {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            </button>
          )}
          <span className="font-mono" style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--text-muted)' }}>
            {title}
          </span>
        </div>
        <button onClick={handleCopy} style={{
          display: 'flex', alignItems: 'center', gap: 4, background: 'none', border: 'none',
          color: copied ? 'var(--accent-success)' : 'var(--text-muted)', cursor: 'pointer', fontSize: '0.6875rem',
        }}>
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      {(!collapsible || expanded) && (
        <div style={{ maxHeight, overflow: 'auto' }}>
          <SyntaxHighlighter language="json" style={customStyle} customStyle={{
            margin: 0, padding: '14px', background: 'transparent', fontSize: '0.8125rem', lineHeight: 1.6,
          }} showLineNumbers lineNumberStyle={{ color: 'var(--text-muted)', fontSize: '0.6875rem', minWidth: '2.5em' }}>
            {jsonStr}
          </SyntaxHighlighter>
        </div>
      )}
    </div>
  );
}

// ── API Endpoints ────────────────────────────────────────────────────────────
export const API = {
  HEALTH: '/health',
  FIRMWARE_LIST: '/api/firmware',
  SPEC: '/api/spec',
  UPLOAD: '/api/upload',
  RUN: '/api/run',
  REPORT: '/api/report',
  REPORT_DOWNLOAD: '/api/report/download',
};

// ── Frontend Routes ─────────────────────────────────────────────────────────
export const ROUTES = {
  LANDING: '/',
  DASHBOARD: '/dashboard',
  FIRMWARE: '/firmware',
  SPEC_EDITOR: '/spec',
  PIPELINE: '/pipeline',
  REQUIREMENTS: '/requirements',
  TRACES: '/traces',
  VERDICTS: '/verdicts',
  REPORT: '/report',
};

// ── Navigation Items ────────────────────────────────────────────────────────
export const NAV_ITEMS = [
  { path: ROUTES.DASHBOARD, label: 'Dashboard', icon: 'LayoutDashboard' },
  { path: ROUTES.FIRMWARE, label: 'Firmware', icon: 'Cpu' },
  { path: ROUTES.SPEC_EDITOR, label: 'Spec Editor', icon: 'FileText' },
  { path: ROUTES.PIPELINE, label: 'Pipeline', icon: 'Play' },
  { path: ROUTES.REQUIREMENTS, label: 'Requirements', icon: 'ClipboardList' },
  { path: ROUTES.TRACES, label: 'Traces', icon: 'Activity' },
  { path: ROUTES.VERDICTS, label: 'Verdicts', icon: 'ShieldCheck' },
  { path: ROUTES.REPORT, label: 'Report', icon: 'FileBarChart' },
];

// ── Pipeline Stage Definitions ──────────────────────────────────────────────
export const PIPELINE_STAGES = [
  { id: 1, key: 'spec', name: 'Spec Extraction', desc: 'NLP-based requirement parsing', icon: 'Scan' },
  { id: 2, key: 'plan', name: 'Test Planning', desc: 'Scenario & fault synthesis', icon: 'ListChecks' },
  { id: 3, key: 'timeline', name: 'Timeline Compilation', desc: 'Bounded timeline generation', icon: 'Clock' },
  { id: 4, key: 'sim', name: 'Simulation', desc: 'Renode / mock trace capture', icon: 'Zap' },
  { id: 5, key: 'explain', name: 'Verdict & Explain', desc: 'Deterministic judge evaluation', icon: 'Scale' },
  { id: 6, key: 'report', name: 'Report Generation', desc: 'HTML report rendering', icon: 'FileBarChart' },
];

// ── Verdict Result Colors ───────────────────────────────────────────────────
export const VERDICT_COLORS = {
  PASS: { bg: 'rgba(16, 185, 129, 0.15)', border: '#10b981', text: '#34d399' },
  FAIL: { bg: 'rgba(239, 68, 68, 0.15)', border: '#ef4444', text: '#f87171' },
  INCONCLUSIVE: { bg: 'rgba(245, 158, 11, 0.15)', border: '#f59e0b', text: '#fbbf24' },
};

// ── Trace Event Kind Colors ─────────────────────────────────────────────────
export const EVENT_KIND_COLORS = {
  hardfault: '#ef4444',
  reset: '#f59e0b',
  hang: '#f97316',
  invalid_memory_access: '#a855f7',
};

// ── Oracle Source Labels ────────────────────────────────────────────────────
export const ORACLE_LABELS = {
  spec: 'Specification',
  inferred: 'Inferred',
  generic: 'Generic Oracle',
};

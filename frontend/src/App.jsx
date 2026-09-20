import React, { useState, useEffect, useRef } from "react";

export default function App() {
  const [backendHealth, setBackendHealth] = useState(null);
  const [firmwares, setFirmwares] = useState([]);
  const [selectedFirmware, setSelectedFirmware] = useState(
    "firmware/inputs/firmware1.elf",
  );
  const [specText, setSpecText] = useState("");
  const [mode, setMode] = useState("offline");
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  const [running, setRunning] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0);
  const [runResult, setRunResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [reportTimestamp, setReportTimestamp] = useState(Date.now());

  const fileInputRef = useRef(null);
  const iframeRef = useRef(null);

  // Check health and load initial data
  const checkHealth = async () => {
    try {
      const res = await fetch("/health");
      if (res.ok) {
        const data = await res.json();
        setBackendHealth(data);
      } else {
        setBackendHealth(false);
      }
    } catch {
      setBackendHealth(false);
    }
  };

  const loadFirmwares = async () => {
    try {
      const res = await fetch("/api/firmware");
      if (res.ok) {
        const list = await res.json();
        setFirmwares(list);
        if (list.length > 0 && !selectedFirmware) {
          setSelectedFirmware(list[0].path);
        }
      }
    } catch (err) {
      console.error("Failed to load firmware list:", err);
    }
  };

  const loadSpec = async () => {
    try {
      const res = await fetch("/api/spec");
      if (res.ok) {
        const data = await res.json();
        setSpecText(data.spec_text || "");
      }
    } catch (err) {
      console.error("Failed to load default spec:", err);
    }
  };

  useEffect(() => {
    checkHealth();
    loadFirmwares();
    loadSpec();
    const interval = setInterval(checkHealth, 6000);
    return () => clearInterval(interval);
  }, []);

  // Handle firmware upload
  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadStatus(`Uploading ${file.name}...`);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(`Server returned status ${res.status}`);
      const data = await res.json();
      setUploadStatus(`Successfully uploaded: ${data.filename}`);
      await loadFirmwares();
      setSelectedFirmware(data.path);
    } catch (err) {
      setUploadStatus(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Run testing pipeline
  const handleRunPipeline = async () => {
    setRunning(true);
    setErrorMsg("");
    setRunResult(null);
    setPipelineStep(1);

    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          firmware: selectedFirmware,
          spec_text: specText,
          mode: mode,
        }),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(
          `Pipeline execution failed (${res.status}): ${errText}`,
        );
      }

      const data = await res.json();
      setPipelineStep(8);
      setRunResult(data);
      setReportTimestamp(Date.now());
    } catch (err) {
      setErrorMsg(err.message || "Pipeline execution encountered an error.");
      setPipelineStep(0);
    } finally {
      setRunning(false);
    }
  };

  const handlePrintReport = () => {
    if (iframeRef.current && iframeRef.current.contentWindow) {
      iframeRef.current.contentWindow.focus();
      iframeRef.current.contentWindow.print();
    } else {
      window.open("/api/report", "_blank");
    }
  };

  const stages = [
    { id: 1, name: "1. Triage", desc: "Arch & Machine" },
    { id: 2, name: "2. Profile", desc: "Peripheral Ingestion" },
    { id: 3, name: "3. Requirements", desc: "Constraint Synthesis" },
    { id: 4, name: "4. Test Planning", desc: "Scenario Synthesis" },
    { id: 5, name: "5. Timelines", desc: "Virtual Events" },
    { id: 6, name: "6. Renode Sim", desc: "Hardware Sim" },
    { id: 7, name: "7. Deterministic Judge", desc: "Evidence Verification" },
    { id: 8, name: "8. Report", desc: "Audit Report" },
  ];

  return (
    <div style={styles.container}>
      {/* Top Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <div style={styles.badge}>PS3 HARDWARE VERIFICATION</div>
          <h1 style={styles.title}>Autonomous Firmware Testing Agent</h1>
          <p style={styles.subtitle}>
            LLM-Guided Natural Language Specification $\to$ Renode Hardware
            Simulation $\to$ Automated Verdicts
          </p>
        </div>

        <div style={styles.headerRight}>
          <div style={styles.statusBox}>
            <span
              style={{
                ...styles.statusDot,
                backgroundColor:
                  backendHealth?.status === "healthy" ? "#10b981" : "#ef4444",
              }}
            />
            <span style={styles.statusText}>
              {backendHealth?.status === "healthy"
                ? "Backend Online"
                : "Backend Offline"}
            </span>
          </div>

          <div style={styles.renodeBox}>
            <span style={{ fontSize: "0.8rem", color: "#94a3b8" }}>
              Simulator:
            </span>
            <span
              style={{
                ...styles.renodeTag,
                color: backendHealth?.renode_available ? "#10b981" : "#f59e0b",
                borderColor: backendHealth?.renode_available
                  ? "#059669"
                  : "#d97706",
              }}
            >
              {backendHealth?.renode_available
                ? "Renode Virtual Hardware Active"
                : "Simulator Offline (Mock Fixture Only)"}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content Grid */}
      <div style={styles.mainGrid}>
        {/* Left Column: Configuration & Controls */}
        <div style={styles.colLeft}>
          {/* Card 1: Firmware Selection */}
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <h2 style={styles.cardTitle}>1. Target Firmware Binary</h2>
              <span style={styles.chip}>{firmwares.length} Available</span>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>Select Firmware to Test:</label>
              <select
                style={styles.select}
                value={selectedFirmware}
                onChange={(e) => setSelectedFirmware(e.target.value)}
                disabled={running}
              >
                {firmwares.map((fw) => (
                  <option key={fw.path} value={fw.path}>
                    {fw.name} ({fw.category}
                    {fw.size_bytes
                      ? ` • ${Math.round(fw.size_bytes / 1024)} KB`
                      : ""}
                    )
                  </option>
                ))}
              </select>
            </div>

            <div style={styles.fieldGroup}>
              <label style={styles.label}>
                Or Upload Custom (.elf / .bin):
              </label>
              <div style={styles.uploadRow}>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".elf,.bin,.hex,.axf"
                  style={styles.fileInput}
                  onChange={handleUpload}
                  disabled={uploading || running}
                />
              </div>
              {uploadStatus && (
                <div style={styles.uploadFeedback}>{uploadStatus}</div>
              )}
            </div>
          </div>

          {/* Card 2: Specification & Rules */}
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <h2 style={styles.cardTitle}>2. Operational Specification</h2>
              <button
                style={styles.textButton}
                onClick={loadSpec}
                disabled={running}
                title="Reset to default baseline specification"
              >
                Reset Default
              </button>
            </div>
            <p style={styles.helpText}>
              Natural language operating rules. The LLM extracts formal
              constraints, generates fault timelines, and checks simulator
              UART/telemetry.
            </p>
            <textarea
              style={styles.textarea}
              rows={6}
              value={specText}
              onChange={(e) => setSpecText(e.target.value)}
              disabled={running}
              placeholder="Enter functional requirements..."
            />
          </div>

          {/* Card 3: Execution Controls */}
          <div style={styles.card}>
            <div style={styles.cardHeader}>
              <h2 style={styles.cardTitle}>3. Test Execution Engine</h2>
            </div>

            <div style={styles.modeRow}>
              <label style={styles.modeOption}>
                <input
                  type="radio"
                  name="mode"
                  value="offline"
                  checked={mode === "offline"}
                  onChange={() => setMode("offline")}
                  disabled={running}
                />
                <div style={{ marginLeft: 8 }}>
                  <div style={styles.modeTitle}>
                    Deterministic Mode (Local Rules + Renode Hardware Sim)
                  </div>
                  <div style={styles.modeDesc}>
                    Fast deterministic rule extraction and live Renode virtual
                    hardware execution without external LLM API keys.
                  </div>
                </div>
              </label>

              <label style={styles.modeOption}>
                <input
                  type="radio"
                  name="mode"
                  value="live"
                  checked={mode === "live"}
                  onChange={() => setMode("live")}
                  disabled={running}
                />
                <div style={{ marginLeft: 8 }}>
                  <div style={styles.modeTitle}>
                    LLM-Augmented Mode (Gemini/OpenAI + Renode Hardware Sim)
                  </div>
                  <div style={styles.modeDesc}>
                    LLM reasoning for specification NLP and scenario synthesis
                    combined with live Renode hardware simulation.
                  </div>
                </div>
              </label>
            </div>

            <button
              style={{
                ...styles.runButton,
                opacity: running ? 0.7 : 1,
                cursor: running ? "not-allowed" : "pointer",
              }}
              onClick={handleRunPipeline}
              disabled={running || backendHealth?.status !== "healthy"}
            >
              {running
                ? "Executing Autonomous Testing Pipeline..."
                : "▶ Run Firmware Verification Pipeline"}
            </button>

            {errorMsg && <div style={styles.errorBox}>{errorMsg}</div>}
          </div>
        </div>

        {/* Right Column: Execution Progress & Live Results */}
        <div style={styles.colRight}>
          {/* Progress Tracker */}
          <div style={styles.card}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <h2 style={styles.cardTitle}>
                Pipeline Workflow Progress (8 Stages)
              </h2>
              {running && (
                <span
                  style={{
                    fontSize: "0.78rem",
                    color: "#38bdf8",
                    fontWeight: 600,
                  }}
                >
                  ⚙ Virtual Hardware Simulation In Progress...
                </span>
              )}
            </div>
            <div style={styles.stageGrid}>
              {stages.map((stage) => {
                const isCurrent = running;
                const isCompleted = runResult && pipelineStep >= 8;
                return (
                  <div
                    key={stage.id}
                    style={{
                      ...styles.stageCard,
                      borderColor: isCurrent
                        ? "#3b82f6"
                        : isCompleted
                          ? "#10b981"
                          : "#334155",
                      backgroundColor: isCurrent
                        ? "#1e293b"
                        : isCompleted
                          ? "#064e3b"
                          : "#0f172a",
                    }}
                  >
                    <div style={styles.stageNum}>
                      {isCompleted ? "✓" : stage.id}
                    </div>
                    <div style={styles.stageName}>{stage.name}</div>
                    <div style={styles.stageDesc}>{stage.desc}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Metric Summary Cards */}
          {runResult && (
            <div style={styles.metricsRow}>
              <div style={styles.metricCard}>
                <div style={styles.metricLabel}>Total Tests</div>
                <div style={styles.metricValue}>
                  {runResult.summary?.total_verdicts ?? 0}
                </div>
              </div>
              <div
                style={{
                  ...styles.metricCard,
                  borderLeft: "4px solid #10b981",
                }}
              >
                <div style={styles.metricLabel}>Passed</div>
                <div style={{ ...styles.metricValue, color: "#10b981" }}>
                  {runResult.summary?.passed ?? 0}
                </div>
              </div>
              <div
                style={{
                  ...styles.metricCard,
                  borderLeft: "4px solid #ef4444",
                }}
              >
                <div style={styles.metricLabel}>Failed</div>
                <div style={{ ...styles.metricValue, color: "#ef4444" }}>
                  {runResult.summary?.failed ?? 0}
                </div>
              </div>
              <div style={styles.metricCard}>
                <div style={styles.metricLabel}>Compliance Rate</div>
                <div style={{ ...styles.metricValue, color: "#38bdf8" }}>
                  {runResult.summary?.verdict_rate ?? 0}%
                </div>
              </div>
            </div>
          )}

          {/* Report Viewer & Download Bar */}
          <div
            style={{
              ...styles.card,
              flex: 1,
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={styles.reportActionsHeader}>
              <div>
                <h2 style={styles.cardTitle}>
                  Verification Report & Telemetry
                </h2>
                <span style={styles.helpText}>
                  Interactive test traces, fault timeline graphs, and
                  requirement verdicts
                </span>
              </div>
              <div style={styles.actionBtnGroup}>
                <button
                  style={styles.secondaryBtn}
                  onClick={handlePrintReport}
                  disabled={!runResult && pipelineStep === 0}
                  title="Print or Save directly as PDF"
                >
                  🖨 Save as PDF / Print
                </button>
                <a
                  href="/api/report/download"
                  download="firmware_testing_report.html"
                  style={{
                    ...styles.primaryBtn,
                    textDecoration: "none",
                    pointerEvents:
                      !runResult && pipelineStep === 0 ? "none" : "auto",
                    opacity: !runResult && pipelineStep === 0 ? 0.5 : 1,
                  }}
                >
                  ⬇ Download HTML
                </a>
              </div>
            </div>

            {/* Embedded Live Report */}
            <div style={styles.reportFrameContainer}>
              <iframe
                ref={iframeRef}
                key={reportTimestamp}
                src="/api/report"
                title="Firmware Verification Report"
                style={styles.reportFrame}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#0b0f19",
    color: "#f1f5f9",
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    display: "flex",
    flexDirection: "column",
  },
  header: {
    padding: "16px 28px",
    backgroundColor: "#111827",
    borderBottom: "1px solid #1f2937",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 16,
  },
  headerLeft: {
    display: "flex",
    flexDirection: "column",
    gap: 4,
  },
  badge: {
    alignSelf: "flex-start",
    fontSize: "0.7rem",
    fontWeight: 700,
    letterSpacing: "0.08em",
    color: "#38bdf8",
    backgroundColor: "#0369a120",
    border: "1px solid #0284c740",
    padding: "2px 8px",
    borderRadius: 4,
  },
  title: {
    margin: 0,
    fontSize: "1.45rem",
    fontWeight: 700,
    color: "#f8fafc",
  },
  subtitle: {
    margin: 0,
    fontSize: "0.85rem",
    color: "#94a3b8",
  },
  headerRight: {
    display: "flex",
    alignItems: "center",
    gap: 16,
  },
  statusBox: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    backgroundColor: "#1e293b",
    padding: "6px 12px",
    borderRadius: 6,
    border: "1px solid #334155",
  },
  statusDot: {
    width: 9,
    height: 9,
    borderRadius: "50%",
  },
  statusText: {
    fontSize: "0.85rem",
    fontWeight: 500,
  },
  renodeBox: {
    display: "flex",
    alignItems: "center",
    gap: 6,
  },
  renodeTag: {
    fontSize: "0.75rem",
    fontWeight: 600,
    padding: "3px 8px",
    borderRadius: 4,
    border: "1px solid",
    backgroundColor: "#1e293b",
  },
  mainGrid: {
    display: "grid",
    gridTemplateColumns: "420px 1fr",
    gap: 20,
    padding: 24,
    flex: 1,
    boxSizing: "border-box",
  },
  colLeft: {
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  colRight: {
    display: "flex",
    flexDirection: "column",
    gap: 20,
  },
  card: {
    backgroundColor: "#111827",
    border: "1px solid #1f2937",
    borderRadius: 8,
    padding: 18,
    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.2)",
  },
  cardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 12,
  },
  cardTitle: {
    margin: 0,
    fontSize: "1.05rem",
    fontWeight: 600,
    color: "#e2e8f0",
  },
  chip: {
    fontSize: "0.72rem",
    fontWeight: 600,
    padding: "2px 8px",
    borderRadius: 12,
    backgroundColor: "#1e293b",
    color: "#94a3b8",
    border: "1px solid #334155",
  },
  fieldGroup: {
    marginBottom: 14,
  },
  label: {
    display: "block",
    fontSize: "0.82rem",
    fontWeight: 500,
    color: "#cbd5e1",
    marginBottom: 6,
  },
  helpText: {
    margin: "0 0 10px 0",
    fontSize: "0.8rem",
    color: "#94a3b8",
    lineHeight: 1.4,
  },
  select: {
    width: "100%",
    padding: "9px 12px",
    backgroundColor: "#0f172a",
    color: "#f8fafc",
    border: "1px solid #334155",
    borderRadius: 6,
    fontSize: "0.85rem",
    outline: "none",
  },
  uploadRow: {
    display: "flex",
    gap: 8,
  },
  fileInput: {
    width: "100%",
    fontSize: "0.8rem",
    color: "#94a3b8",
  },
  uploadFeedback: {
    marginTop: 6,
    fontSize: "0.75rem",
    color: "#38bdf8",
  },
  textButton: {
    background: "none",
    border: "none",
    color: "#38bdf8",
    fontSize: "0.78rem",
    fontWeight: 500,
    cursor: "pointer",
    padding: 0,
  },
  textarea: {
    width: "100%",
    backgroundColor: "#0f172a",
    color: "#f8fafc",
    border: "1px solid #334155",
    borderRadius: 6,
    padding: 10,
    fontSize: "0.82rem",
    fontFamily: "monospace",
    resize: "vertical",
    outline: "none",
    boxSizing: "border-box",
  },
  modeRow: {
    display: "flex",
    flexDirection: "column",
    gap: 10,
    marginBottom: 16,
  },
  modeOption: {
    display: "flex",
    alignItems: "flex-start",
    backgroundColor: "#0f172a",
    border: "1px solid #1e293b",
    padding: "10px 12px",
    borderRadius: 6,
    cursor: "pointer",
  },
  modeTitle: {
    fontSize: "0.85rem",
    fontWeight: 600,
    color: "#f1f5f9",
  },
  modeDesc: {
    fontSize: "0.75rem",
    color: "#94a3b8",
    marginTop: 2,
  },
  runButton: {
    width: "100%",
    padding: "12px 16px",
    backgroundColor: "#2563eb",
    color: "#ffffff",
    border: "none",
    borderRadius: 6,
    fontSize: "0.95rem",
    fontWeight: 600,
    cursor: "pointer",
    transition: "background 0.15s ease",
  },
  errorBox: {
    marginTop: 12,
    padding: 10,
    backgroundColor: "#7f1d1d30",
    border: "1px solid #b91c1c",
    borderRadius: 6,
    color: "#fca5a5",
    fontSize: "0.8rem",
  },
  stageGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 10,
    marginTop: 8,
  },
  stageCard: {
    padding: "10px 8px",
    borderRadius: 6,
    border: "1px solid",
    textAlign: "center",
    transition: "all 0.2s ease",
  },
  stageNum: {
    fontSize: "0.85rem",
    fontWeight: 700,
    color: "#38bdf8",
    marginBottom: 4,
  },
  stageName: {
    fontSize: "0.78rem",
    fontWeight: 600,
    color: "#f1f5f9",
    whiteSpace: "nowrap",
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  stageDesc: {
    fontSize: "0.68rem",
    color: "#94a3b8",
    marginTop: 2,
  },
  metricsRow: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 12,
  },
  metricCard: {
    backgroundColor: "#111827",
    border: "1px solid #1f2937",
    borderRadius: 6,
    padding: 12,
    textAlign: "center",
  },
  metricLabel: {
    fontSize: "0.72rem",
    color: "#94a3b8",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
    marginBottom: 4,
  },
  metricValue: {
    fontSize: "1.4rem",
    fontWeight: 700,
    color: "#f8fafc",
  },
  reportActionsHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: 12,
    marginBottom: 12,
  },
  actionBtnGroup: {
    display: "flex",
    gap: 10,
  },
  secondaryBtn: {
    backgroundColor: "#1e293b",
    color: "#f1f5f9",
    border: "1px solid #334155",
    padding: "7px 14px",
    borderRadius: 6,
    fontSize: "0.8rem",
    fontWeight: 600,
    cursor: "pointer",
  },
  primaryBtn: {
    backgroundColor: "#059669",
    color: "#ffffff",
    border: "none",
    padding: "7px 14px",
    borderRadius: 6,
    fontSize: "0.8rem",
    fontWeight: 600,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
  },
  reportFrameContainer: {
    flex: 1,
    minHeight: 480,
    borderRadius: 6,
    overflow: "hidden",
    border: "1px solid #1e293b",
    backgroundColor: "#0f172a",
  },
  reportFrame: {
    width: "100%",
    height: "100%",
    minHeight: 520,
    border: "none",
    backgroundColor: "#0b0f19",
  },
};

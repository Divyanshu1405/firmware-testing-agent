import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { ShieldCheck, ChevronDown, ChevronUp } from "lucide-react";
import Card from "../components/GlassCard";
import StatusBadge from "../components/StatusBadge";
import EmptyState from "../components/EmptyState";
import { usePipeline } from "../hooks/usePipeline";
import { ROUTES } from "../utils/constants";

export default function VerdictsPage() {
  const navigate = useNavigate();
  const pipeline = usePipeline();
  const verdicts = pipeline.verdicts || [];
  const explanations = pipeline.explanations || {};
  const [expandedIdx, setExpandedIdx] = useState(null);

  if (verdicts.length === 0) {
    return (
      <div className="page-container">
        <div className="page-header">
          <h1>Verdicts</h1>
          <p>Test evaluation results.</p>
        </div>
        <EmptyState
          icon={ShieldCheck}
          title="No verdicts"
          description="Run the pipeline to generate test verdicts."
          action={() => navigate(ROUTES.PIPELINE)}
          actionLabel="Run Pipeline"
        />
      </div>
    );
  }

  const getRes = (v) =>
    typeof v?.result === "object" && v?.result !== null
      ? v.result.value
      : v?.result || "";
  const passed = verdicts.filter((v) => getRes(v) === "PASS").length;
  const failed = verdicts.filter((v) => getRes(v) === "FAIL").length;
  const inconclusive = verdicts.filter(
    (v) => getRes(v) === "INCONCLUSIVE",
  ).length;

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Verdicts</h1>
        <p>Test evaluation results and failure evidence.</p>
      </div>

      {/* Summary */}
      <div style={{ display: "flex", gap: 32, marginBottom: 40 }}>
        {[
          { label: "Total", value: verdicts.length },
          { label: "Passed", value: passed },
          { label: "Failed", value: failed },
          { label: "Inconclusive", value: inconclusive },
        ].map((stat) => (
          <div key={stat.label}>
            <div className="text-overline" style={{ marginBottom: 4 }}>
              {stat.label}
            </div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>
              {stat.value}
            </div>
          </div>
        ))}
      </div>

      {/* Verdict List */}
      <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
        {verdicts.map((v, idx) => {
          const isExpanded = expandedIdx === idx;
          const explanation = explanations[v.test_id];

          return (
            <motion.div
              key={idx}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: idx * 0.03 }}
              style={{ borderBottom: "1px solid var(--border-subtle)" }}
            >
              <div
                onClick={() => setExpandedIdx(isExpanded ? null : idx)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 16,
                  padding: "16px 0",
                  cursor: "pointer",
                  transition: "opacity 0.15s",
                }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.7")}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
              >
                <StatusBadge variant={v.result} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div
                    style={{ display: "flex", alignItems: "center", gap: 10 }}
                  >
                    <span className="font-mono" style={{ fontWeight: 700 }}>
                      {v.test_id}
                    </span>
                    <span
                      style={{
                        color: "var(--text-muted)",
                        fontSize: "0.8125rem",
                      }}
                    >
                      →
                    </span>
                    <span
                      className="font-mono"
                      style={{
                        color: "var(--text-secondary)",
                        fontSize: "0.8125rem",
                      }}
                    >
                      {v.requirement_id} / {v.monitor_id}
                    </span>
                  </div>
                </div>
                <StatusBadge variant={v.oracle_source} />
                {isExpanded ? (
                  <ChevronUp size={16} style={{ color: "var(--text-muted)" }} />
                ) : (
                  <ChevronDown
                    size={16}
                    style={{ color: "var(--text-muted)" }}
                  />
                )}
              </div>

              {isExpanded && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  style={{ paddingBottom: 16, paddingLeft: 4 }}
                >
                  <div
                    style={{
                      padding: "16px 20px",
                      borderRadius: "var(--radius-sm)",
                      background: "var(--bg-secondary)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div className="text-overline" style={{ marginBottom: 8 }}>
                      Evidence
                    </div>
                    <div
                      className="font-mono"
                      style={{
                        fontSize: "0.8125rem",
                        color: "var(--text-secondary)",
                        lineHeight: 1.6,
                      }}
                    >
                      <span style={{ color: "var(--text-muted)" }}>
                        @ {v.evidence?.t_ms} ms
                      </span>{" "}
                      — {v.evidence?.detail}
                    </div>

                    {explanation && (
                      <div style={{ marginTop: 16 }}>
                        <div
                          className="text-overline"
                          style={{ marginBottom: 8 }}
                        >
                          Hypothesis
                        </div>
                        <div
                          style={{
                            fontSize: "0.875rem",
                            color: "var(--text-secondary)",
                            lineHeight: 1.6,
                          }}
                        >
                          {explanation}
                        </div>
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

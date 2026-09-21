import React from "react";

const VARIANTS = {
  PASS: {
    color: "var(--accent-success)",
    bg: "rgba(48,209,88,0.1)",
    border: "rgba(48,209,88,0.2)",
    label: "PASS",
  },
  FAIL: {
    color: "var(--accent-danger)",
    bg: "rgba(255,69,58,0.1)",
    border: "rgba(255,69,58,0.2)",
    label: "FAIL",
  },
  INCONCLUSIVE: {
    color: "var(--accent-warning)",
    bg: "rgba(255,214,10,0.1)",
    border: "rgba(255,214,10,0.2)",
    label: "INCONCLUSIVE",
  },
  online: {
    color: "var(--accent-success)",
    bg: "rgba(48,209,88,0.1)",
    border: "rgba(48,209,88,0.2)",
    label: "Online",
  },
  offline: {
    color: "var(--accent-danger)",
    bg: "rgba(255,69,58,0.1)",
    border: "rgba(255,69,58,0.2)",
    label: "Offline",
  },
  neutral: {
    color: "var(--text-tertiary)",
    bg: "rgba(255,255,255,0.04)",
    border: "var(--border-primary)",
    label: "",
  },
  spec: {
    color: "var(--text-secondary)",
    bg: "rgba(255,255,255,0.04)",
    border: "var(--border-primary)",
    label: "Spec",
  },
  inferred: {
    color: "var(--text-tertiary)",
    bg: "rgba(255,255,255,0.04)",
    border: "var(--border-primary)",
    label: "Inferred",
  },
  generic: {
    color: "var(--text-muted)",
    bg: "rgba(255,255,255,0.04)",
    border: "var(--border-primary)",
    label: "Generic",
  },
};

export default function StatusBadge({
  variant = "neutral",
  label,
  dot = false,
  style: customStyle = {},
}) {
  const vStr =
    typeof variant === "object" && variant !== null
      ? variant.value || String(variant)
      : variant;
  const config = VARIANTS[vStr] || VARIANTS.neutral;
  const displayLabel = label || config.label || vStr;

  return (
    <span
      className="badge"
      style={{
        color: config.color,
        background: config.bg,
        borderColor: config.border,
        ...customStyle,
      }}
    >
      {dot && (
        <span
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            backgroundColor: "currentColor",
            flexShrink: 0,
          }}
        />
      )}
      {displayLabel}
    </span>
  );
}

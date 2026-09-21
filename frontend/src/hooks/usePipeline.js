import React, { createContext, useContext, useState, useCallback } from "react";
import { API } from "../utils/constants";

/**
 * Pipeline state context — persists run results across page navigation.
 * Stores requirements, test_plan, timelines, traces, verdicts, explanations, report_html.
 */
const PipelineContext = createContext(null);

export function PipelineProvider({ children }) {
  const [pipelineState, setPipelineState] = useState({
    status: "idle", // idle | running | completed | error
    currentStage: 0,
    mode: "live",
    firmware: "firmware/inputs/firmware1.elf",
    specText: "",
    // Results
    summary: null,
    requirements: [],
    testPlan: [],
    timelines: [],
    traces: [],
    verdicts: [],
    explanations: {},
    reportHtml: "",
    error: null,
    lastRunAt: null,
  });

  const setField = useCallback((updates) => {
    setPipelineState((prev) => ({ ...prev, ...updates }));
  }, []);

  const runPipeline = useCallback(async (firmware, specText, mode) => {
    setPipelineState((prev) => ({
      ...prev,
      status: "running",
      currentStage: 1,
      error: null,
      firmware,
      specText,
      mode,
    }));

    // Simulated stage progression for smooth UX
    const stageTimers = [];
    stageTimers.push(
      setTimeout(
        () => setPipelineState((p) => ({ ...p, currentStage: 2 })),
        1500,
      ),
    );
    stageTimers.push(
      setTimeout(
        () => setPipelineState((p) => ({ ...p, currentStage: 3 })),
        3500,
      ),
    );
    stageTimers.push(
      setTimeout(
        () => setPipelineState((p) => ({ ...p, currentStage: 4 })),
        5500,
      ),
    );
    stageTimers.push(
      setTimeout(
        () => setPipelineState((p) => ({ ...p, currentStage: 5 })),
        7500,
      ),
    );

    try {
      const res = await fetch(API.RUN, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ firmware, spec_text: specText, mode }),
      });

      stageTimers.forEach(clearTimeout);

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Pipeline failed (${res.status}): ${errText}`);
      }

      const data = await res.json();

      setPipelineState((prev) => ({
        ...prev,
        status: "completed",
        currentStage: 7,
        summary: data.summary,
        requirements: data.requirements || [],
        testPlan: data.test_plan || [],
        timelines: data.timelines || [],
        traces: data.traces || [],
        verdicts: data.verdicts || [],
        explanations: data.explanations || {},
        reportHtml: data.report_html || "",
        lastRunAt: new Date().toISOString(),
      }));

      return data;
    } catch (err) {
      stageTimers.forEach(clearTimeout);
      setPipelineState((prev) => ({
        ...prev,
        status: "error",
        currentStage: 0,
        error: err.message || "Pipeline execution failed",
      }));
      throw err;
    }
  }, []);

  const resetPipeline = useCallback(() => {
    setPipelineState((prev) => ({
      ...prev,
      status: "idle",
      currentStage: 0,
      error: null,
    }));
  }, []);

  return React.createElement(
    PipelineContext.Provider,
    { value: { ...pipelineState, setField, runPipeline, resetPipeline } },
    children,
  );
}

export function usePipeline() {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error("usePipeline must be used within PipelineProvider");
  return ctx;
}

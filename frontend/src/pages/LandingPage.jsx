import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, Shield, Cpu, Activity, Zap, ChevronRight } from 'lucide-react';
import { ROUTES } from '../utils/constants';

/**
 * Apple-style full-screen landing page — dramatic typography, pure black,
 * minimal content, strong CTA.
 */
export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', background: '#000', color: '#f5f5f7', overflow: 'hidden' }}>

      {/* ── Nav Bar ──────────────────────────────────────────────────────── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0 48px', height: 52,
        background: 'rgba(0,0,0,0.8)',
        backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)',
        borderBottom: '1px solid rgba(255,255,255,0.04)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Shield size={18} color="#fff" />
          <span style={{ fontSize: '0.875rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
            FW Agent
          </span>
        </div>
        <button
          className="btn btn-primary btn-sm"
          onClick={() => navigate(ROUTES.DASHBOARD)}
        >
          Open Workspace
          <ArrowRight size={14} />
        </button>
      </nav>

      {/* ── Hero Section ─────────────────────────────────────────────────── */}
      <section style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '120px 24px 80px',
        textAlign: 'center',
        position: 'relative',
      }}>
        {/* Subtle radial glow */}
        <div style={{
          position: 'absolute', top: '20%', left: '50%', transform: 'translateX(-50%)',
          width: '60vw', height: '40vh',
          background: 'radial-gradient(ellipse, rgba(255,255,255,0.03) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          style={{ position: 'relative', zIndex: 1, maxWidth: 800 }}
        >
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            padding: '6px 16px', borderRadius: 9999, marginBottom: 32,
            border: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(255,255,255,0.03)',
            fontSize: '0.8125rem', color: '#a1a1a6', fontWeight: 500,
          }}>
            <Zap size={13} />
            Autonomous Hardware Verification
          </div>

          <h1 className="display-xl" style={{ marginBottom: 24, color: '#fff' }}>
            Firmware testing,<br />
            <span style={{ color: '#a1a1a6' }}>reimagined.</span>
          </h1>

          <p style={{
            fontSize: '1.25rem', lineHeight: 1.5, color: '#6e6e73',
            maxWidth: 560, margin: '0 auto 48px',
          }}>
            From natural-language specs to deterministic verdicts.
            LLM-guided test planning meets Renode hardware simulation.
          </p>

          <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
            <motion.button
              className="btn btn-primary btn-lg"
              onClick={() => navigate(ROUTES.DASHBOARD)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
              style={{ fontWeight: 600 }}
            >
              Enter Workspace
              <ArrowRight size={18} />
            </motion.button>
            <motion.button
              className="btn btn-secondary btn-lg"
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
              }}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.98 }}
            >
              Learn More
            </motion.button>
          </div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          style={{
            position: 'absolute', bottom: 40,
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8,
          }}
        >
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <ChevronRight size={16} style={{ color: '#48484a', transform: 'rotate(90deg)' }} />
          </motion.div>
        </motion.div>
      </section>

      {/* ── Features Section ─────────────────────────────────────────────── */}
      <section
        id="features"
        style={{
          padding: '120px 48px',
          maxWidth: 1100,
          margin: '0 auto',
        }}
      >
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.7 }}
          style={{ textAlign: 'center', marginBottom: 80 }}
        >
          <h2 className="display-lg" style={{ marginBottom: 16 }}>
            Built for precision.
          </h2>
          <p style={{ fontSize: '1.125rem', color: '#6e6e73', maxWidth: 480, margin: '0 auto' }}>
            Every component designed with one goal — zero false positives, zero missed faults.
          </p>
        </motion.div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 1,
          background: 'var(--border-subtle)',
          borderRadius: 'var(--radius-xl)',
          overflow: 'hidden',
          border: '1px solid var(--border-subtle)',
        }}>
          {[
            {
              icon: Cpu,
              title: 'Renode Simulation',
              desc: 'Full STM32F4 hardware model with I2C sensor injection, UART capture, and GPIO monitoring.',
            },
            {
              icon: Shield,
              title: 'Deterministic Judge',
              desc: 'Temporal logic monitors — always, never, within, eventually — the LLM never decides pass or fail.',
            },
            {
              icon: Activity,
              title: 'Fault Injection',
              desc: '8 fault primitives: stuck-at, dropout, spike, glitch, drift, noise, oscillation, UART corruption.',
            },
          ].map((feature, idx) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: idx * 0.1 }}
              style={{
                padding: '48px 36px',
                background: 'var(--bg-primary)',
              }}
            >
              <feature.icon size={24} style={{ color: '#f5f5f7', marginBottom: 20 }} />
              <h3 style={{ fontSize: '1.125rem', fontWeight: 600, marginBottom: 10 }}>
                {feature.title}
              </h3>
              <p style={{ fontSize: '0.9375rem', color: '#6e6e73', lineHeight: 1.6 }}>
                {feature.desc}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Pipeline Section ─────────────────────────────────────────────── */}
      <section style={{ padding: '120px 48px', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ maxWidth: 1100, margin: '0 auto' }}>
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-100px' }}
            transition={{ duration: 0.7 }}
            style={{ textAlign: 'center', marginBottom: 80 }}
          >
            <h2 className="display-lg" style={{ marginBottom: 16 }}>
              Six stages. One verdict.
            </h2>
            <p style={{ fontSize: '1.125rem', color: '#6e6e73', maxWidth: 500, margin: '0 auto' }}>
              A fully autonomous pipeline from specification to report — no manual intervention required.
            </p>
          </motion.div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
            {[
              { num: '01', title: 'Spec Extraction', desc: 'Natural language requirements parsed into structured constraints.' },
              { num: '02', title: 'Test Planning', desc: 'Up to 8 test scenarios synthesized with targeted fault assignments.' },
              { num: '03', title: 'Timeline Generation', desc: 'Bounded sensor input timelines compiled and auto-healed.' },
              { num: '04', title: 'Hardware Simulation', desc: 'Renode STM32 execution with trace capture and UART monitoring.' },
              { num: '05', title: 'Deterministic Judging', desc: 'Temporal logic evaluation against every requirement monitor.' },
              { num: '06', title: 'Report Generation', desc: 'Interactive HTML report with verdicts, evidence, and provenance.' },
            ].map((step, idx) => (
              <motion.div
                key={step.num}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: idx * 0.08 }}
                style={{
                  display: 'flex',
                  alignItems: 'baseline',
                  gap: 32,
                  padding: '28px 0',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <span className="font-mono" style={{
                  fontSize: '0.8125rem', color: '#48484a', fontWeight: 500, flexShrink: 0, width: 28,
                }}>
                  {step.num}
                </span>
                <div>
                  <h3 style={{ fontSize: '1.0625rem', fontWeight: 600, marginBottom: 4 }}>{step.title}</h3>
                  <p style={{ fontSize: '0.9375rem', color: '#6e6e73' }}>{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Section ──────────────────────────────────────────────────── */}
      <section style={{
        padding: '120px 48px',
        textAlign: 'center',
        borderTop: '1px solid var(--border-subtle)',
      }}>
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
        >
          <h2 className="display-lg" style={{ marginBottom: 16 }}>
            Ready to verify.
          </h2>
          <p style={{ fontSize: '1.125rem', color: '#6e6e73', marginBottom: 40 }}>
            Upload your firmware. Define your rules. Get deterministic answers.
          </p>
          <motion.button
            className="btn btn-primary btn-lg"
            onClick={() => navigate(ROUTES.DASHBOARD)}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
          >
            Open Workspace
            <ArrowRight size={18} />
          </motion.button>
        </motion.div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer style={{
        padding: '32px 48px',
        borderTop: '1px solid var(--border-subtle)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <span style={{ fontSize: '0.75rem', color: '#48484a' }}>
          Autonomous Firmware Testing Agent — PS3 Hardware Verification
        </span>
        <span style={{ fontSize: '0.75rem', color: '#48484a' }}>
          Deterministic Judging • LangGraph Pipeline • Renode Simulation
        </span>
      </footer>
    </div>
  );
}

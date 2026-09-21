import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import * as Icons from 'lucide-react';
import { NAV_ITEMS } from '../utils/constants';

/**
 * Apple-style minimal sidebar — thin, clean, monochrome.
 */
export default function Sidebar({ healthStatus }) {
  const location = useLocation();

  return (
    <aside style={{
      width: 220,
      height: '100vh',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 50,
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--bg-primary)',
      borderRight: '1px solid var(--border-subtle)',
    }}>
      {/* Brand */}
      <div style={{
        padding: '20px 20px 16px',
        borderBottom: '1px solid var(--border-subtle)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: 'var(--white)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <Icons.Shield size={15} color="#000" />
          </div>
          <div>
            <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
              FW Agent
            </div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 10px', display: 'flex', flexDirection: 'column', gap: 1, overflowY: 'auto' }}>
        <div className="text-overline" style={{ padding: '8px 10px 6px', fontSize: '0.625rem' }}>
          Navigation
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = Icons[item.icon] || Icons.Circle;
          const isActive = location.pathname === item.path;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 10px',
                borderRadius: 'var(--radius-sm)',
                textDecoration: 'none',
                fontSize: '0.8125rem',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? 'var(--text-primary)' : 'var(--text-tertiary)',
                background: isActive ? 'rgba(255,255,255,0.06)' : 'transparent',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255,255,255,0.03)';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-tertiary)';
                }
              }}
            >
              <Icon size={16} style={{ opacity: isActive ? 1 : 0.5 }} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{ padding: '14px 20px', borderTop: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            width: 6, height: 6, borderRadius: '50%',
            backgroundColor: healthStatus ? '#30d158' : '#ff453a',
            animation: healthStatus ? 'pulse-dot 2s ease-in-out infinite' : 'none',
          }} />
          <span style={{ fontSize: '0.6875rem', color: 'var(--text-muted)', fontWeight: 500 }}>
            {healthStatus ? 'System Online' : 'Disconnected'}
          </span>
        </div>
      </div>
    </aside>
  );
}

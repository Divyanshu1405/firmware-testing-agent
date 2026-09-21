import React from 'react';
import { useLocation } from 'react-router-dom';
import { NAV_ITEMS } from '../utils/constants';
import StatusBadge from './StatusBadge';

export default function TopBar({ healthData }) {
  const location = useLocation();
  const currentNav = NAV_ITEMS.find((item) => item.path === location.pathname);

  return (
    <header style={{
      height: 52,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 40px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(0,0,0,0.85)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      position: 'sticky',
      top: 0,
      zIndex: 40,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Agent</span>
        <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>/</span>
        <span style={{ fontSize: '0.8125rem', color: 'var(--text-primary)', fontWeight: 600 }}>
          {currentNav?.label || 'Page'}
        </span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <span className="text-overline" style={{ fontSize: '0.625rem' }}>
          {healthData?.renode_available ? 'Renode' : 'Mock Engine'}
        </span>
        <StatusBadge
          variant={healthData?.status === 'healthy' ? 'online' : 'offline'}
          dot
        />
      </div>
    </header>
  );
}

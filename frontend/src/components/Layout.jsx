import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { API } from '../utils/constants';

/**
 * Workspace layout: Sidebar + TopBar + content. Used for all app pages (not landing).
 */
export default function Layout() {
  const [healthData, setHealthData] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(API.HEALTH);
        if (res.ok) setHealthData(await res.json());
        else setHealthData(null);
      } catch { setHealthData(null); }
    };
    check();
    const interval = setInterval(check, 8000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: 'flex', minHeight: '100vh', width: '100%' }}>
      <Sidebar healthStatus={healthData?.status === 'healthy'} />

      <div style={{
        flex: 1,
        marginLeft: 220,
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        background: 'var(--bg-root)',
      }}>
        <TopBar healthData={healthData} />

        <main style={{ flex: 1, overflow: 'auto' }}>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              style={{ minHeight: 'calc(100vh - 52px)' }}
            >
              <Outlet context={{ healthData }} />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}

import React, { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Upload, HardDrive, FileCode, Package } from 'lucide-react';
import Card from '../components/GlassCard';
import EmptyState from '../components/EmptyState';
import { fetchApi } from '../hooks/useApi';
import { API } from '../utils/constants';

export default function FirmwarePage() {
  const [firmwares, setFirmwares] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadMsg, setUploadMsg] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const fileRef = useRef(null);

  const loadFirmwares = async () => {
    try { setFirmwares(await fetchApi(API.FIRMWARE_LIST)); } catch {}
  };
  useEffect(() => { loadFirmwares(); }, []);

  const handleUpload = async (file) => {
    if (!file) return;
    setUploading(true);
    setUploadMsg(`Uploading ${file.name}...`);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(API.UPLOAD, { method: 'POST', body: formData });
      if (!res.ok) throw new Error(`${res.status}`);
      const data = await res.json();
      setUploadMsg(`Uploaded: ${data.filename} — ${Math.round(data.size_bytes / 1024)} KB`);
      await loadFirmwares();
    } catch (err) {
      setUploadMsg(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const catIcons = { 'Baseline Firmware': HardDrive, 'User Upload': FileCode, 'Mock Target': Package };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Firmware</h1>
        <p>Available binaries and upload interface.</p>
      </div>

      {/* Upload */}
      <div style={{ marginBottom: 40 }}>
        <div
          className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => { e.preventDefault(); setDragOver(false); handleUpload(e.dataTransfer.files?.[0]); }}
          onClick={() => fileRef.current?.click()}
        >
          <input ref={fileRef} type="file" accept=".elf,.bin,.hex,.axf" style={{ display: 'none' }} onChange={(e) => handleUpload(e.target.files?.[0])} />
          <Upload size={28} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <div style={{ fontSize: '0.9375rem', fontWeight: 500, color: 'var(--text-secondary)', marginBottom: 4 }}>
            {uploading ? 'Uploading...' : 'Drop firmware binary or click to browse'}
          </div>
          <div className="text-caption">.elf · .bin · .hex · .axf</div>
        </div>
        {uploadMsg && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} style={{
            marginTop: 12, fontSize: '0.8125rem', color: 'var(--text-secondary)',
          }}>{uploadMsg}</motion.div>
        )}
      </div>

      {/* List */}
      {firmwares.length === 0 ? (
        <EmptyState icon={Cpu} title="No firmware found" description="Upload a binary to begin." />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {firmwares.map((fw, idx) => {
            const Icon = catIcons[fw.category] || Cpu;
            return (
              <motion.div
                key={fw.path}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.04 }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 16,
                  padding: '16px 0',
                  borderBottom: '1px solid var(--border-subtle)',
                }}
              >
                <div style={{
                  width: 40, height: 40, borderRadius: 10,
                  border: '1px solid var(--border-primary)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  flexShrink: 0,
                }}>
                  <Icon size={18} style={{ color: 'var(--text-muted)' }} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.9375rem', fontWeight: 600, marginBottom: 2 }}>
                    {fw.name}
                  </div>
                  <span className="font-mono text-caption" style={{ wordBreak: 'break-all' }}>
                    {fw.path}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
                  <span className="badge badge-neutral">{fw.category}</span>
                  {fw.size_bytes > 0 && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {Math.round(fw.size_bytes / 1024)} KB
                    </span>
                  )}
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect, useRef } from 'react';
import { apiService } from './api';
import './App.css';

// Simple SVG Icons
const ShieldIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--primary)', filter: 'drop-shadow(0 0 8px var(--primary-glow))' }}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

const UploadIcon = () => (
  <svg className="upload-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

const MemoryIcon = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
    <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
    <line x1="6" y1="6" x2="6" y2="6" />
    <line x1="6" y1="18" x2="6" y2="18" />
  </svg>
);

function App() {
  const [file, setFile] = useState(null);
  const [keyword, setKeyword] = useState('');
  const [jobId, setJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [health, setHealth] = useState(null);
  const [dumpPath, setDumpPath] = useState('');
  const [usePathMode, setUsePathMode] = useState(false);
  
  const pollIntervalRef = useRef(null);

  useEffect(() => {
    // Restore jobId from localStorage on startup
    const savedJobId = localStorage.getItem('seedtrace_current_job');
    if (savedJobId) {
      setJobId(savedJobId);
      setUsePathMode(true); // Default to path mode for restored jobs
    }

    apiService.health()
      .then(response => setHealth(response.data))
      .catch(() => setHealth({ status: 'error' }));
    
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (!jobId) {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      return;
    }

    // Persist jobId
    localStorage.setItem('seedtrace_current_job', jobId);

    const pollStatus = async () => {
      try {
        const response = await apiService.getJobStatus(jobId);
        setJobStatus(response.data);

        if (response.data.status === 'done' || response.data.status === 'error') {
          clearInterval(pollIntervalRef.current);
          
          if (response.data.status === 'done' && response.data.result?.type === 'acquisition') {
            const path = response.data.result.filepath;
            setDumpPath(path);
            setUsePathMode(true);
            setFile(null);
          }
          // Note: We keep the jobId in storage until "New Analysis" is clicked
        }
      } catch (error) {
        // Silently retry on network/starvation errors
        console.warn('Status polling heartbeat missed (server busy):', error.message);
      }
    };

    pollStatus();
    pollIntervalRef.current = setInterval(pollStatus, 1500);

    return () => clearInterval(pollIntervalRef.current);
  }, [jobId]);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const resetInternalState = () => {
    setJobId(null);
    setJobStatus(null);
    localStorage.removeItem('seedtrace_current_job');
  };

  const startAnalysis = async () => {
    try {
      if (usePathMode) {
        if (!dumpPath) return alert('Please enter a file path');
        const response = await apiService.analyzeByPath(dumpPath, keyword);
        setJobId(response.data.job_id);
      } else {
        if (!file) return alert('Please select a file');
        setUploading(true);
        const response = await apiService.uploadFile(file, keyword);
        setJobId(response.data.job_id);
        setUploading(false);
      }
      setJobStatus(null);
    } catch (error) {
      console.error('Analysis failed:', error);
      const errorData = error.response?.data;
      
      if (error.response?.status === 507) {
        alert(`🚨 DISK SPACE ERROR: ${errorData.message}\n\nTip: Use "Server Analysis" mode to scan the file directly from your disk without uploading it again.`);
      } else {
        alert(errorData?.error || errorData?.message || 'Analysis failed. Please try again.');
      }
      
      setUploading(false);
    }
  };



  const takeLiveMemoryDump = async () => {
    try {
      const response = await apiService.acquireMemory();
      setJobId(response.data.job_id);
      setJobStatus(null);
    } catch (error) {
      console.error('Memory dump failed:', error);
      const msg = error.response?.data?.message || 'Memory dump failed. Ensure you have administrator privileges.';
      alert(msg);
    }
  };

  const downloadReport = async () => {
    try {
      const response = await apiService.downloadLatestReport();
      const filename = jobStatus?.result?.pdf_report || jobStatus?.result?.report_file || 'report.pdf';
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'queued': return '#e2e8f0';
      case 'running': return '#fef3c7';
      case 'done': return '#d1fae5';
      case 'error': return '#fee2e2';
      default: return '#f1f5f9';
    }
  };

  const getStatusTextColor = (status) => {
    switch (status) {
      case 'queued': return '#64748b';
      case 'running': return '#92400e';
      case 'done': return '#065f46';
      case 'error': return '#991b1b';
      default: return '#64748b';
    }
  };

  const getRiskColor = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'critical': return 'var(--danger)';
      case 'high': return '#f97316';
      case 'medium': return 'var(--warning)';
      case 'low': return 'var(--success)';
      default: return 'var(--text-muted)';
    }
  };

  const getStepProgress = () => {
    if (!jobStatus || jobStatus.type === 'acquisition') return 0;
    const progress = jobStatus.progress || '';
    if (progress.includes('Step 1')) return 1;
    if (progress.includes('Step 2')) return 2;
    if (progress.includes('Step 3')) return 3;
    if (progress.includes('Step 4')) return 4;
    if (progress.includes('Step 5')) return 5;
    if (progress.includes('Step 6')) return 6;
    if (progress === 'Completed') return 7;
    return 0;
  };

  return (
    <div className="app">
      <header className="header">
        <div className="logo-section">
          <h1><ShieldIcon /> SeedTrace</h1>
          <p>Forensic Memory Analysis Engine</p>
        </div>
        <div className="header-status">
          {health && (
            <div className={`health-badge ${health.status === 'ok' ? '' : 'error'}`}>
              <span className="status-dot"></span>
              {health.status === 'ok' ? 'System Ready' : 'System Offline'}
            </div>
          )}
        </div>
      </header>

      <main>
        {jobId && (
          <div className="status-section" style={{ border: '2px solid var(--primary)', marginBottom: '30px' }}>
            {!jobStatus ? (
              <div className="progress-text-display">
                <div className="spinner"></div>
                Establishing Secure Connection...
              </div>
            ) : (
              <>
                <div className="status-card-header">
                  <div className="job-meta">
                    <div className="job-id-pill">ID: {jobId.slice(0, 13)}</div>
                    <h3>{jobStatus.type === 'acquisition' ? 'System Memory Dump' : 'Forensic Investigation'}</h3>
                  </div>
                  <div 
                    className="status-badge" 
                    style={{ 
                      backgroundColor: getStatusColor(jobStatus.status), 
                      color: getStatusTextColor(jobStatus.status) 
                    }}
                  >
                    {jobStatus.status}
                  </div>
                </div>

                {jobStatus.type !== 'acquisition' && (
                  <div className="progress-stepper">
                    {[1, 2, 3, 4, 5, 6].map(i => {
                      const current = getStepProgress();
                      const icons = ['🔍', '📝', '🔑', '₿', '📊', '📄'];
                      return (
                        <div key={i} className={`step ${current >= i ? 'completed' : current === i-1 ? 'active' : ''}`}>
                          {current >= i ? '✓' : icons[i-1]}
                        </div>
                      );
                    })}
                  </div>
                )}

                <div className="progress-text-display">
                  <div className="spinner"></div>
                  {jobStatus.progress || 'Analyzing Data Blocks...'}
                </div>
              </>
            )}

            {jobStatus?.status === 'done' && jobStatus.result && jobStatus.type !== 'acquisition' && (
              <div className="results-container">
                <div className="results-grid">
                  <div className="stat-card" style={{ borderTop: `4px solid ${getRiskColor(jobStatus.result.risk)}` }}>
                    <div className="stat-label">Safety Rating</div>
                    <div className="stat-value" style={{ color: getRiskColor(jobStatus.result.risk) }}>{jobStatus.result.risk}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Total Findings</div>
                    <div className="stat-value">{jobStatus.result.findings_count}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Artifact Count</div>
                    <div className="stat-value">{Object.values(jobStatus.result.artifact_summary || {}).reduce((a, b) => a + b, 0)}</div>
                  </div>
                  <div className="stat-card">
                    <div className="stat-label">Threat Score</div>
                    <div className="stat-value">{jobStatus.result.risk_score}/100</div>
                  </div>
                </div>

                <div className="forensic-summary">
                   <h4>Executive Summary</h4>
                   <p>{jobStatus.result.message}</p>
                </div>

                <div className="findings">
                  <h4 style={{ marginBottom: '16px', color: 'var(--text-main)' }}>Detected Cryptographic Seeds</h4>
                  {jobStatus.result.findings?.length === 0 && <p style={{ color: 'var(--text-muted)' }}>No clear seed phrases identified in this memory region.</p>}
                  {jobStatus.result.findings?.map((f, i) => (
                    <div key={i} className="finding-card">
                      <div className="finding-header">
                        <span className="finding-typebadge">SEED PHRASE DETECTED</span>
                        <div className="finding-meta">
                          <span className="offset-label">Offset: 0x{f.offset.toString(16).toUpperCase()}</span>
                          <div className="confidence-meter">
                            <div className="confidence-fill" style={{ width: `${f.confidence * 100}%` }}></div>
                          </div>
                          <span className="confidence-pct">{Math.round(f.confidence * 100)}% Match</span>
                        </div>
                      </div>
                      <div className="phrase-box">{f.phrase}</div>
                    </div>
                  ))}
                </div>

                <div className="report-actions">
                  <button className="btn-download" onClick={downloadReport}>📄 Download Forensic PDF</button>
                  <button className="btn-new-analysis" onClick={resetInternalState}>Start New Analysis</button>

                </div>
              </div>
            )}

            {jobStatus?.status === 'error' && (
              <div style={{ backgroundColor: '#fef2f2', border: '1px solid #fee2e2', padding: '16px', borderRadius: '8px', color: '#991b1b' }}>
                <p style={{ fontWeight: 600 }}>Error Encountered</p>
                <p style={{ fontSize: '0.9rem' }}>{jobStatus.error}</p>
              </div>
            )}
          </div>
        )}

        <div className="dashboard-grid">
          <section className="card">
            <div className="section-header">
              <h2>Data Intelligence</h2>
              <div className="mode-toggle">
                <button className={`toggle-btn ${!usePathMode ? 'active' : ''}`} onClick={() => setUsePathMode(false)}>Direct Upload</button>
                <button className={`toggle-btn ${usePathMode ? 'active' : ''}`} onClick={() => setUsePathMode(true)}>Server Analysis</button>
              </div>
            </div>

            <div style={{ flex: 1 }}>
              {!usePathMode ? (
                <div className="upload-area">
                  <label className="file-label">
                    <input type="file" onChange={handleFileChange} accept=".raw,.mem,.dmp" style={{ display: 'none' }} />
                    <UploadIcon />
                    <span className="upload-text">{file ? file.name : 'Select RAM Dump'}</span>
                    <span className="upload-hint">Supports full memory dumps</span>
                  </label>
                </div>
              ) : (
                <div className="input-group">
                  <label className="input-label">Forensic File Path</label>
                  <input 
                    type="text" 
                    className="modern-input" 
                    value={dumpPath} 
                    onChange={(e) => setDumpPath(e.target.value)}
                    placeholder="E.g. C:\Forensics\ram.raw"
                  />
                </div>
              )}

              <div className="input-group" style={{ marginTop: '24px' }}>
                <label className="input-label">Target Keyword (Optional)</label>
                <input 
                  type="text" 
                  className="modern-input" 
                  value={keyword} 
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="Scan for specific strings"
                />
              </div>
            </div>

            <button 
              className="btn-primary" 
              onClick={startAnalysis} 
              disabled={(!file && !dumpPath) || uploading || (jobStatus && jobStatus.status === 'running')}
              style={{ marginTop: '24px' }}
            >
              {uploading ? 'Processing Data...' : jobStatus?.status === 'running' ? 'Scanning Memory...' : 'Initiate Intelligence Scan'}
            </button>
          </section>

          <section className="card">
            <h2>Live Acquisition</h2>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginBottom: '24px', flex: 1 }}>
              <p>Execute live physical memory capture from the host system using elevated forensic tools.</p>
              <div style={{ marginTop: '20px', background: 'rgba(15, 23, 42, 0.4)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
                <div style={{ display: 'flex', gap: '12px', marginBottom: '12px', alignItems: 'center' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)' }}></div>
                  <span style={{ fontSize: '0.85rem' }}>Administrator privileges required</span>
                </div>
                <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)' }}></div>
                  <span style={{ fontSize: '0.85rem' }}>Dumping via Windows PMEM driver</span>
                </div>
              </div>
            </div>
            <button 
              className="btn-acquisition" 
              onClick={takeLiveMemoryDump}
              disabled={jobStatus && jobStatus.status === 'running'}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
                <MemoryIcon />
                {jobStatus?.type === 'acquisition' && jobStatus.status === 'running' ? 'Capturing RAM...' : 'Acquire System Memory'}
              </div>
            </button>
          </section>
        </div>
      </main>

      <footer className="footer">
        <p>© 2026 SeedTrace Forensics Engine • Authorized Use Only</p>
      </footer>
    </div>
  );
}

export default App;


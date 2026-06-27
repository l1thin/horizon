import React from 'react';

export default function TerminalOutput({ stdout, stderr, status, isLoading }) {
  return (
    <div style={{ backgroundColor: '#ffffff', color: '#111827', fontFamily: 'monospace', padding: '1rem', height: '200px', overflowY: 'auto', borderTop: '1px solid #e5e7eb' }}>
      {isLoading ? (
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="spinner" style={{ width: '16px', height: '16px', border: '2px solid #e5e7eb', borderTopColor: '#111827', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
          <span>Running…</span>
        </div>
      ) : (
        <>
          {status && (
            <div style={{ fontWeight: 'bold', marginBottom: '10px', color: status.includes('Accepted') ? '#3fb950' : '#f85149' }}>
              {status.includes('Accepted') ? '✓ ' : '✗ '} {status}
            </div>
          )}
          {stdout && <pre style={{ margin: '0 0 10px 0', whiteSpace: 'pre-wrap', color: '#3fb950' }}>{stdout}</pre>}
          {stderr && <pre style={{ margin: '0', whiteSpace: 'pre-wrap', color: '#f85149' }}>{stderr}</pre>}
          {!status && !stdout && !stderr && <div style={{ color: '#6b7280' }}>Ready</div>}
        </>
      )}
      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

import React from 'react';

export default function IntegrityPanel({ integrity }) {
  if (!integrity) return null;

  const isFlagged = integrity.verdict === 'flagged';

  return (
    <div style={{ backgroundColor: '#1e1e2f', borderRadius: '12px', padding: '20px', marginTop: '1.5rem' }}>
      <h3 style={{ margin: '0 0 15px 0', color: '#fff', fontSize: '18px' }}>Session Integrity</h3>
      
      {isFlagged ? (
        <div style={{ backgroundColor: 'rgba(245, 158, 11, 0.1)', borderLeft: '4px solid #f59e0b', padding: '10px 15px', color: '#f59e0b', marginBottom: '15px', borderRadius: '4px' }}>
          A few signals were detected during your session.
        </div>
      ) : (
        <div style={{ backgroundColor: 'rgba(16, 185, 129, 0.1)', borderLeft: '4px solid #10b981', padding: '10px 15px', color: '#10b981', marginBottom: '15px', borderRadius: '4px' }}>
          No integrity issues detected.
        </div>
      )}

      <div style={{ display: 'flex', gap: '20px', color: '#a1a1aa', fontSize: '14px' }}>
        <div style={{ backgroundColor: '#27273a', padding: '10px 15px', borderRadius: '8px', flex: 1 }}>
          <div style={{ fontSize: '20px', color: '#fff', fontWeight: 'bold', marginBottom: '5px' }}>{integrity.tab_switches}</div>
          <div>Tab Switches</div>
        </div>
        <div style={{ backgroundColor: '#27273a', padding: '10px 15px', borderRadius: '8px', flex: 1 }}>
          <div style={{ fontSize: '20px', color: '#fff', fontWeight: 'bold', marginBottom: '5px' }}>{integrity.fast_answer_questions.length}</div>
          <div>Fast Answers</div>
          {integrity.fast_answer_questions.length > 0 && (
             <div style={{ fontSize: '12px', marginTop: '5px', color: '#8b949e' }}>Questions: {integrity.fast_answer_questions.join(', ')}</div>
          )}
        </div>
      </div>
      <div style={{ marginTop: '15px', fontSize: '12px', color: '#8b949e', fontStyle: 'italic' }}>
        This is provided for context. It is not an accusation of cheating.
      </div>
    </div>
  );
}

import React from 'react';

export default function IntegrityPanel({ integrity }) {
  if (!integrity) return null;

  const isFlagged = integrity.verdict === 'flagged';

  return (
    <div style={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '20px', marginTop: '1.5rem', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}>
      <h3 style={{ margin: '0 0 15px 0', color: '#111827', fontSize: '18px' }}>Session Integrity</h3>
      
      {isFlagged ? (
        <div style={{ backgroundColor: '#fffbeb', borderLeft: '4px solid #f59e0b', padding: '10px 15px', color: '#92400e', marginBottom: '15px', borderRadius: '4px' }}>
          A few signals were detected during your session.
        </div>
      ) : (
        <div style={{ backgroundColor: '#f0fdf4', borderLeft: '4px solid #10b981', padding: '10px 15px', color: '#166534', marginBottom: '15px', borderRadius: '4px' }}>
          No integrity issues detected.
        </div>
      )}

      <div style={{ display: 'flex', gap: '20px', color: '#6b7280', fontSize: '14px' }}>
        <div style={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', padding: '10px 15px', borderRadius: '8px', flex: 1 }}>
          <div style={{ fontSize: '20px', color: '#111827', fontWeight: 'bold', marginBottom: '5px' }}>{integrity.tab_switches}</div>
          <div>Tab Switches</div>
        </div>
        <div style={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', padding: '10px 15px', borderRadius: '8px', flex: 1 }}>
          <div style={{ fontSize: '20px', color: '#111827', fontWeight: 'bold', marginBottom: '5px' }}>{integrity.fast_answer_questions.length}</div>
          <div>Fast Answers</div>
          {integrity.fast_answer_questions.length > 0 && (
             <div style={{ fontSize: '12px', marginTop: '5px', color: '#6b7280' }}>Questions: {integrity.fast_answer_questions.join(', ')}</div>
          )}
        </div>
      </div>
      <div style={{ marginTop: '15px', fontSize: '12px', color: '#9ca3af', fontStyle: 'italic' }}>
        This is provided for context. It is not an accusation of cheating.
      </div>
    </div>
  );
}

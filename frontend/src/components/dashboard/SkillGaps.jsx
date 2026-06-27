import React from 'react';

export default function SkillGaps({ skillGaps }) {
  if (!skillGaps || skillGaps.length === 0) return null;

  const topGaps = [...skillGaps].sort((a, b) => b.gap_score - a.gap_score).slice(0, 3);

  return (
    <div style={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '20px', marginTop: '1.5rem', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}>
      <h3 style={{ margin: '0 0 15px 0', color: '#111827', fontSize: '18px' }}>Areas to focus on</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {topGaps.map((gap, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
              <span style={{ color: '#111827' }}>{gap.skill}</span>
              <span style={{ color: '#6b7280' }}>Gap: {gap.gap_score}/10</span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: '#e5e7eb', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${(gap.gap_score / 10) * 100}%`, height: '100%', backgroundColor: '#111827', borderRadius: '4px' }}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

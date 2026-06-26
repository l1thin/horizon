import React from 'react';

export default function SkillGaps({ skillGaps }) {
  if (!skillGaps || skillGaps.length === 0) return null;

  const topGaps = [...skillGaps].sort((a, b) => b.gap_score - a.gap_score).slice(0, 3);

  return (
    <div style={{ backgroundColor: '#1e1e2f', borderRadius: '12px', padding: '20px', marginTop: '1.5rem' }}>
      <h3 style={{ margin: '0 0 15px 0', color: '#fff', fontSize: '18px' }}>Areas to focus on</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
        {topGaps.map((gap, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '14px' }}>
              <span style={{ color: '#c9d1d9' }}>{gap.skill}</span>
              <span style={{ color: '#8b949e' }}>Gap: {gap.gap_score}/10</span>
            </div>
            <div style={{ width: '100%', height: '8px', backgroundColor: '#303046', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ width: `${(gap.gap_score / 10) * 100}%`, height: '100%', backgroundColor: '#ef4444', borderRadius: '4px' }}></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

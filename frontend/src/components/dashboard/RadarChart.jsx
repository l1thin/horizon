import React, { useMemo } from 'react';
import { RadarChart as RechartsRadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from 'recharts';

export default function RadarChart({ questions }) {
  const data = useMemo(() => {
    if (!questions || questions.length === 0) return [];

    let techSum = 0, techCount = 0;
    let commSum = 0, commCount = 0;
    let probSum = 0, probCount = 0;
    let behSum = 0, behCount = 0;
    let codeSum = 0, codeCount = 0;

    questions.forEach(q => {
      if (q.question_type === 'technical') {
        techSum += q.score; techCount++;
      } else if (q.question_type === 'behavioral') {
        behSum += q.score; behCount++;
        commSum += q.score; commCount++; // proxy
      } else if (q.question_type === 'coding') {
        probSum += q.score; probCount++;
        codeSum += q.score; codeCount++; // proxy
      }
    });

    return [
      { subject: 'Technical', A: techCount ? techSum / techCount : 0, fullMark: 10 },
      { subject: 'Communication', A: commCount ? commSum / commCount : 0, fullMark: 10 },
      { subject: 'Problem Solving', A: probCount ? probSum / probCount : 0, fullMark: 10 },
      { subject: 'Behavioural', A: behCount ? behSum / behCount : 0, fullMark: 10 },
      { subject: 'Code Quality', A: codeCount ? codeSum / codeCount : 0, fullMark: 10 },
    ];
  }, [questions]);

  return (
    <div style={{ width: '100%', height: 300, backgroundColor: '#1e1e2f', borderRadius: '12px', padding: '1rem', marginTop: '1rem' }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="#3f3f5a" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#a1a1aa', fontSize: 12 }} />
          <Radar name="Score" dataKey="A" stroke="#818cf8" fill="#6366f1" fillOpacity={0.35} />
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}

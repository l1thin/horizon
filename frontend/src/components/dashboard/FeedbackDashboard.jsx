import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getReport } from '../../services/api';
import RadarChart from './RadarChart';
import QuestionCard from './QuestionCard';
import SkillGaps from './SkillGaps';
import IntegrityPanel from './IntegrityPanel';
import './FeedbackDashboard.css';

export default function FeedbackDashboard({ sessionId }) {
  const { data: report, isLoading, error } = useQuery({
    queryKey: ['report', sessionId],
    queryFn: () => getReport(sessionId),
    retry: 10,
    retryDelay: (attempt) => Math.min(2000 * (attempt + 1), 10000),
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', backgroundColor: 'transparent', color: '#ffffff' }}>
        <div style={{ width: '40px', height: '40px', border: '3px solid rgba(255, 255, 255, 0.2)', borderTopColor: '#ffffff', borderRadius: '50%', animation: 'spin 1s linear infinite', marginBottom: '1rem' }}></div>
        <h2>Evaluating your answers…</h2>
        <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  if (error) {
    return <div style={{ color: '#ef4444', textAlign: 'center', marginTop: '50px' }}>Error loading report: {error.message}</div>;
  }

  if (!report) return null;

  const scoreColor = '#111827';

  return (
    <div className="feedback-dashboard" style={{ backgroundColor: 'transparent', minHeight: '100vh', padding: '40px 20px', color: '#111827', textAlign: 'left' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        
        <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem' }}>
          <div>
            <h1 style={{ margin: '0 0 10px 0', fontSize: '28px', color: '#ffffff' }}>Interview Report</h1>
            <p style={{ color: '#6b7280', margin: 0 }}>Session: {sessionId}</p>
          </div>
          <div className="print-btn-container">
            <button 
              onClick={() => window.print()}
              style={{ background: '#f9fafb', color: '#111827', border: '1px solid #e5e7eb', padding: '8px 16px', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
            >
              Export PDF
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '20px', backgroundColor: '#ffffff', border: '1px solid #e5e7eb', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)', padding: '20px', borderRadius: '12px' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', border: `4px solid ${scoreColor}`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '28px', fontWeight: 'bold', color: scoreColor }}>
            {report.overall_score}
          </div>
          <div>
            <h2 style={{ margin: '0 0 5px 0', fontSize: '20px' }}>Overall Score</h2>
            <p style={{ color: '#6b7280', margin: 0 }}>Based on technical accuracy, communication, and problem-solving skills.</p>
          </div>
        </div>

        <RadarChart questions={report.questions} />
        
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{ margin: '0 0 15px 0', fontSize: '20px', color: '#ffffff' }}>Question Breakdown</h3>
          {report.questions.map((q, i) => (
            <QuestionCard key={q.question_id} question={q} index={i} />
          ))}
        </div>

        <SkillGaps skillGaps={report.skill_gaps} />
        
        <IntegrityPanel integrity={report.integrity} />

      </div>
    </div>
  );
}

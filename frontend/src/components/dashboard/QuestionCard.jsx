import React, { useState, useRef } from 'react';

export default function QuestionCard({ question, index }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef(null);

  const scoreColor = question.score >= 8 ? '#10b981' : question.score >= 5 ? '#f59e0b' : '#ef4444';
  
  return (
    <div className="question-card" style={{ backgroundColor: '#27273a', borderRadius: '10px', marginBottom: '1rem', overflow: 'hidden' }}>
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ padding: '15px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: isExpanded ? '#303046' : '#27273a', transition: 'background-color 0.2s' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, overflow: 'hidden' }}>
          <span style={{ color: '#8b949e', fontWeight: 'bold' }}>Q{index + 1}</span>
          <span style={{ backgroundColor: '#3f3f5a', padding: '3px 8px', borderRadius: '12px', fontSize: '12px', color: '#c9d1d9', textTransform: 'capitalize' }}>{question.question_type}</span>
          <span style={{ color: '#fff', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{question.question_text}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginLeft: '10px' }}>
          <span style={{ border: `1px solid ${scoreColor}`, color: scoreColor, padding: '2px 8px', borderRadius: '10px', fontSize: '12px', fontWeight: 'bold' }}>Score: {question.score}/10</span>
          <span style={{ backgroundColor: '#1e1e2f', color: '#a1a1aa', padding: '2px 8px', borderRadius: '10px', fontSize: '12px', textTransform: 'capitalize' }}>{question.depth_rating}</span>
          <span style={{ color: '#8b949e', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }}>▼</span>
        </div>
      </div>
      
      <div 
        ref={contentRef}
        style={{ 
          height: isExpanded ? `${contentRef.current?.scrollHeight}px` : '0px', 
          transition: 'height 0.3s ease-in-out', 
          overflow: 'hidden',
          backgroundColor: '#1e1e2f'
        }}
      >
        <div style={{ padding: '15px' }}>
          <div style={{ marginBottom: '15px' }}>
            <h4 style={{ margin: '0 0 5px 0', color: '#10b981', fontSize: '14px' }}>What was good</h4>
            <p style={{ margin: 0, color: '#c9d1d9', fontSize: '14px', backgroundColor: 'rgba(16, 185, 129, 0.1)', padding: '10px', borderRadius: '6px' }}>{question.feedback.what_was_good}</p>
          </div>
          <div style={{ marginBottom: '15px' }}>
            <h4 style={{ margin: '0 0 5px 0', color: '#f59e0b', fontSize: '14px' }}>What was missing</h4>
            <p style={{ margin: 0, color: '#c9d1d9', fontSize: '14px', backgroundColor: 'rgba(245, 158, 11, 0.1)', padding: '10px', borderRadius: '6px' }}>{question.feedback.what_was_missing}</p>
          </div>
          {question.feedback.suggestions && question.feedback.suggestions.length > 0 && (
            <div>
              <h4 style={{ margin: '0 0 5px 0', color: '#6366f1', fontSize: '14px' }}>Suggestions</h4>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#a1a1aa', fontSize: '14px' }}>
                {question.feedback.suggestions.map((s, i) => <li key={i} style={{ marginBottom: '4px' }}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

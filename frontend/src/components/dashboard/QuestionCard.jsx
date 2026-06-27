import React, { useState, useRef } from 'react';

export default function QuestionCard({ question, index }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const contentRef = useRef(null);

  const scoreColor = question.score >= 8 ? '#10b981' : question.score >= 5 ? '#f59e0b' : '#ef4444';
  
  return (
    <div className="question-card" style={{ backgroundColor: '#ffffff', border: '1px solid #e5e7eb', borderRadius: '10px', marginBottom: '1rem', overflow: 'hidden', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}>
      <div 
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ padding: '15px', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: isExpanded ? '#f9fafb' : '#ffffff', transition: 'background-color 0.2s' }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flex: 1, overflow: 'hidden' }}>
          <span style={{ color: '#6b7280', fontWeight: 'bold' }}>Q{index + 1}</span>
          <span style={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', padding: '3px 8px', borderRadius: '12px', fontSize: '12px', color: '#111827', textTransform: 'capitalize' }}>{question.question_type}</span>
          <span style={{ color: '#111827', fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{question.question_text}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginLeft: '10px' }}>
          <span style={{ border: `1px solid ${scoreColor}`, color: scoreColor, padding: '2px 8px', borderRadius: '10px', fontSize: '12px', fontWeight: 'bold' }}>Score: {question.score}/10</span>
          <span style={{ backgroundColor: '#f9fafb', border: '1px solid #e5e7eb', color: '#6b7280', padding: '2px 8px', borderRadius: '10px', fontSize: '12px', textTransform: 'capitalize' }}>{question.depth_rating}</span>
          <span style={{ color: '#6b7280', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }}>▼</span>
        </div>
      </div>
      
      <div 
        ref={contentRef}
        style={{ 
          height: isExpanded ? `${contentRef.current?.scrollHeight}px` : '0px', 
          transition: 'height 0.3s ease-in-out', 
          overflow: 'hidden',
          backgroundColor: '#ffffff',
          borderTop: isExpanded ? '1px solid #e5e7eb' : 'none'
        }}
      >
        <div style={{ padding: '15px' }}>
          <div style={{ marginBottom: '15px' }}>
            <h4 style={{ margin: '0 0 5px 0', color: '#10b981', fontSize: '14px' }}>What was good</h4>
            <p style={{ margin: 0, color: '#111827', fontSize: '14px', backgroundColor: '#f0fdf4', border: '1px solid #bbf7d0', padding: '10px', borderRadius: '6px' }}>{question.feedback.what_was_good}</p>
          </div>
          <div style={{ marginBottom: '15px' }}>
            <h4 style={{ margin: '0 0 5px 0', color: '#f59e0b', fontSize: '14px' }}>What was missing</h4>
            <p style={{ margin: 0, color: '#111827', fontSize: '14px', backgroundColor: '#fffbeb', border: '1px solid #fde68a', padding: '10px', borderRadius: '6px' }}>{question.feedback.what_was_missing}</p>
          </div>
          {question.feedback.suggestions && question.feedback.suggestions.length > 0 && (
            <div>
              <h4 style={{ margin: '0 0 5px 0', color: '#6366f1', fontSize: '14px' }}>Suggestions</h4>
              <ul style={{ margin: 0, paddingLeft: '20px', color: '#6b7280', fontSize: '14px' }}>
                {question.feedback.suggestions.map((s, i) => <li key={i} style={{ marginBottom: '4px' }}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

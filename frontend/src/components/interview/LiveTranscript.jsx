import React from 'react';

export default function LiveTranscript({ transcript, interim }) {
  if (!transcript && !interim) return null;
  return (
    <div style={{ marginTop: '2rem', maxWidth: '600px', textAlign: 'center', minHeight: '60px' }}>
      <p style={{ color: '#111827', fontSize: '18px', margin: 0, lineHeight: '1.5' }}>{transcript}</p>
      <p style={{ color: '#6b7280', fontSize: '18px', fontStyle: 'italic', margin: 0, lineHeight: '1.5' }}>{interim}</p>
    </div>
  );
}

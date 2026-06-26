import React from 'react';
import FeedbackDashboard from '../components/dashboard/FeedbackDashboard';

export default function ReportPage({ sessionId }) {
  return <FeedbackDashboard sessionId={sessionId} />;
}

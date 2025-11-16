import React from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';

const TrainingPage: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Training Jobs</h1>
          <button className="btn-primary">+ New Training Job</button>
        </div>

        <div className="card text-center py-12">
          <p className="text-gray-600">Configure and monitor fine-tuning jobs (Phase 3)</p>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default TrainingPage;

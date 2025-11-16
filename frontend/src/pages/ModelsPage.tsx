import React from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';

const ModelsPage: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Model Hub</h1>
          <button className="btn-primary">Browse Models</button>
        </div>

        <div className="card text-center py-12">
          <p className="text-gray-600">Browse and select models for fine-tuning (Phase 2)</p>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ModelsPage;

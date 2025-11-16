import React from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';

const DeploymentPage: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Deployments</h1>
          <button className="btn-primary">+ Deploy Model</button>
        </div>

        <div className="card text-center py-12">
          <p className="text-gray-600">Deploy and manage your fine-tuned models (Phase 4)</p>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DeploymentPage;

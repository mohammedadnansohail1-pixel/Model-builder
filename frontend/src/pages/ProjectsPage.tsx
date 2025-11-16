import React from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';

const ProjectsPage: React.FC = () => {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Projects</h1>
          <button className="btn-primary">+ Create Project</button>
        </div>

        <div className="card text-center py-12">
          <p className="text-gray-600">No projects yet. Create your first project to get started!</p>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default ProjectsPage;

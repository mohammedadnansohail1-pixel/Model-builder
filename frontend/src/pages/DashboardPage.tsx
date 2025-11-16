import React from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import { useAuth } from '../contexts/AuthContext';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.full_name || user?.username}!
          </h1>
          <p className="mt-2 text-gray-600">
            Start fine-tuning your AI models with ease
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900">Projects</h3>
            <p className="mt-2 text-3xl font-bold text-primary-600">0</p>
            <p className="mt-1 text-sm text-gray-600">Active projects</p>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900">Models</h3>
            <p className="mt-2 text-3xl font-bold text-primary-600">0</p>
            <p className="mt-1 text-sm text-gray-600">Fine-tuned models</p>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900">Training Jobs</h3>
            <p className="mt-2 text-3xl font-bold text-primary-600">0</p>
            <p className="mt-1 text-sm text-gray-600">In progress</p>
          </div>

          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900">Deployments</h3>
            <p className="mt-2 text-3xl font-bold text-primary-600">0</p>
            <p className="mt-1 text-sm text-gray-600">Active deployments</p>
          </div>
        </div>

        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Quick Start Guide
          </h2>
          <div className="space-y-4">
            <div className="flex items-start">
              <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-primary-100 text-primary-600 font-semibold">
                1
              </span>
              <div className="ml-4">
                <h3 className="font-medium text-gray-900">Create a Project</h3>
                <p className="text-sm text-gray-600">
                  Organize your models and datasets in projects
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-primary-100 text-primary-600 font-semibold">
                2
              </span>
              <div className="ml-4">
                <h3 className="font-medium text-gray-900">Upload Your Dataset</h3>
                <p className="text-sm text-gray-600">
                  Prepare and validate your training data
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-primary-100 text-primary-600 font-semibold">
                3
              </span>
              <div className="ml-4">
                <h3 className="font-medium text-gray-900">Select a Model</h3>
                <p className="text-sm text-gray-600">
                  Choose from our library of pre-trained models
                </p>
              </div>
            </div>

            <div className="flex items-start">
              <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-primary-100 text-primary-600 font-semibold">
                4
              </span>
              <div className="ml-4">
                <h3 className="font-medium text-gray-900">Start Training</h3>
                <p className="text-sm text-gray-600">
                  Configure and launch your fine-tuning job
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DashboardPage;

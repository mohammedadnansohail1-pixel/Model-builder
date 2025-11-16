import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import { deploymentsAPI, modelsAPI, projectsAPI } from '../services/api';
import { Deployment, DeploymentStatus, InferenceBackend } from '../types/deployment';
import toast from 'react-hot-toast';

const DeploymentPage: React.FC = () => {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDeployment, setSelectedDeployment] = useState<Deployment | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Load deployments
  useEffect(() => {
    loadDeployments();
    const interval = setInterval(loadDeployments, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [statusFilter]);

  const loadDeployments = async () => {
    try {
      const params = statusFilter !== 'all' ? { status_filter: statusFilter } : {};
      const response = await deploymentsAPI.list(params);
      setDeployments(response.data);
    } catch (error) {
      console.error('Failed to load deployments:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStartDeployment = async (deploymentId: string) => {
    try {
      await deploymentsAPI.start(deploymentId);
      toast.success('Deployment started');
      loadDeployments();
    } catch (error) {
      toast.error('Failed to start deployment');
    }
  };

  const handleStopDeployment = async (deploymentId: string) => {
    if (!confirm('Are you sure you want to stop this deployment?')) return;

    try {
      await deploymentsAPI.stop(deploymentId);
      toast.success('Deployment stopped');
      loadDeployments();
    } catch (error) {
      toast.error('Failed to stop deployment');
    }
  };

  const handleDeleteDeployment = async (deploymentId: string) => {
    if (!confirm('Are you sure you want to delete this deployment?')) return;

    try {
      await deploymentsAPI.delete(deploymentId);
      toast.success('Deployment deleted');
      loadDeployments();
    } catch (error) {
      toast.error('Failed to delete deployment');
    }
  };

  const getStatusColor = (status: DeploymentStatus) => {
    switch (status) {
      case DeploymentStatus.RUNNING:
        return 'bg-green-100 text-green-800';
      case DeploymentStatus.DEPLOYING:
      case DeploymentStatus.SCALING:
        return 'bg-blue-100 text-blue-800';
      case DeploymentStatus.FAILED:
        return 'bg-red-100 text-red-800';
      case DeploymentStatus.STOPPED:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const formatNumber = (num?: number) => {
    if (num === undefined || num === null) return 'N/A';
    return new Intl.NumberFormat().format(num);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Deployments</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            + Deploy Model
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input"
          >
            <option value="all">All Status</option>
            <option value="deploying">Deploying</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="failed">Failed</option>
          </select>
        </div>

        {/* Deployments List */}
        {loading ? (
          <div className="card text-center py-12">
            <p className="text-gray-600">Loading deployments...</p>
          </div>
        ) : deployments.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-600">No deployments found. Deploy your first model to get started!</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {deployments.map((deployment) => (
              <div key={deployment.id} className="card hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{deployment.name}</h3>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(deployment.status)}`}>
                        {deployment.status}
                      </span>
                      <span className="px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded-full">
                        {deployment.backend.toUpperCase()}
                      </span>
                      <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                        {deployment.replicas} replica{deployment.replicas > 1 ? 's' : ''}
                      </span>
                    </div>

                    {deployment.description && (
                      <p className="text-gray-600 text-sm mb-3">{deployment.description}</p>
                    )}

                    {/* Endpoint URL */}
                    {deployment.endpoint_url && deployment.status === DeploymentStatus.RUNNING && (
                      <div className="mb-3 bg-gray-50 p-2 rounded">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-600">Endpoint:</span>
                          <code className="text-xs bg-white px-2 py-1 rounded">{deployment.endpoint_url}</code>
                          <button
                            onClick={() => {
                              navigator.clipboard.writeText(deployment.endpoint_url!);
                              toast.success('Endpoint copied!');
                            }}
                            className="text-xs text-blue-600 hover:text-blue-700"
                          >
                            Copy
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Requests:</span>
                        <span className="ml-2 font-semibold">{formatNumber(deployment.total_requests)}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Errors:</span>
                        <span className="ml-2 font-semibold">{formatNumber(deployment.total_errors)}</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Avg Latency:</span>
                        <span className="ml-2 font-semibold">
                          {deployment.average_latency_ms ? `${deployment.average_latency_ms.toFixed(0)}ms` : 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Req/min:</span>
                        <span className="ml-2 font-semibold">
                          {deployment.requests_per_minute ? deployment.requests_per_minute.toFixed(1) : 'N/A'}
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-600">Health:</span>
                        <span className={`ml-2 font-semibold ${
                          deployment.health_status === 'healthy' ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {deployment.health_status}
                        </span>
                      </div>
                    </div>

                    {/* Error Message */}
                    {deployment.error_message && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                        <p className="text-sm text-red-800">{deployment.error_message}</p>
                      </div>
                    )}

                    {/* Timestamps */}
                    <div className="mt-3 text-xs text-gray-500">
                      <span>Created: {new Date(deployment.created_at).toLocaleString()}</span>
                      {deployment.deployed_at && (
                        <span className="ml-4">Deployed: {new Date(deployment.deployed_at).toLocaleString()}</span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => setSelectedDeployment(deployment)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                    >
                      View
                    </button>
                    {deployment.status === DeploymentStatus.STOPPED && (
                      <button
                        onClick={() => handleStartDeployment(deployment.id)}
                        className="px-3 py-1 text-sm text-green-600 hover:bg-green-50 rounded"
                      >
                        Start
                      </button>
                    )}
                    {deployment.status === DeploymentStatus.RUNNING && (
                      <button
                        onClick={() => handleStopDeployment(deployment.id)}
                        className="px-3 py-1 text-sm text-yellow-600 hover:bg-yellow-50 rounded"
                      >
                        Stop
                      </button>
                    )}
                    {(deployment.status === DeploymentStatus.STOPPED || deployment.status === DeploymentStatus.FAILED) && (
                      <button
                        onClick={() => handleDeleteDeployment(deployment.id)}
                        className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                      >
                        Delete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Create Deployment Modal */}
        {showCreateModal && (
          <CreateDeploymentModal
            onClose={() => setShowCreateModal(false)}
            onSuccess={() => {
              setShowCreateModal(false);
              loadDeployments();
            }}
          />
        )}

        {/* Deployment Details Modal */}
        {selectedDeployment && (
          <DeploymentDetailsModal
            deployment={selectedDeployment}
            onClose={() => setSelectedDeployment(null)}
          />
        )}
      </div>
    </DashboardLayout>
  );
};

// Create Deployment Modal Component
const CreateDeploymentModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_id: '',
    model_id: '',
    backend: InferenceBackend.TGI,
    replicas: 1,
    auto_scaling_enabled: false,
  });

  const [projects, setProjects] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [projectsRes, modelsRes] = await Promise.all([
        projectsAPI.list(),
        modelsAPI.list(),
      ]);
      setProjects(projectsRes.data);
      setModels(modelsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await deploymentsAPI.create({
        name: formData.name,
        description: formData.description || undefined,
        project_id: formData.project_id,
        model_id: formData.model_id,
        backend: formData.backend,
        replicas: formData.replicas,
        auto_scaling_enabled: formData.auto_scaling_enabled,
      });
      toast.success('Deployment created successfully!');
      onSuccess();
    } catch (error) {
      toast.error('Failed to create deployment');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4">Deploy Model</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Deployment Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input"
                placeholder="My Production Deployment"
              />
            </div>

            <div>
              <label className="label">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="input"
                rows={3}
                placeholder="Optional description..."
              />
            </div>

            <div>
              <label className="label">Project *</label>
              <select
                required
                value={formData.project_id}
                onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                className="input"
              >
                <option value="">Select a project</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Model *</label>
              <select
                required
                value={formData.model_id}
                onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                className="input"
              >
                <option value="">Select a model</option>
                {models.map((model) => (
                  <option key={model.id} value={model.id}>
                    {model.name} ({model.model_id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Backend</label>
              <select
                value={formData.backend}
                onChange={(e) => setFormData({ ...formData, backend: e.target.value as InferenceBackend })}
                className="input"
              >
                <option value={InferenceBackend.TGI}>TGI (Text Generation Inference)</option>
                <option value={InferenceBackend.VLLM}>vLLM</option>
                <option value={InferenceBackend.TRITON}>NVIDIA Triton</option>
                <option value={InferenceBackend.CUSTOM}>Custom</option>
              </select>
            </div>

            <div>
              <label className="label">Number of Replicas</label>
              <input
                type="number"
                min="1"
                max="100"
                value={formData.replicas}
                onChange={(e) => setFormData({ ...formData, replicas: parseInt(e.target.value) })}
                className="input"
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.auto_scaling_enabled}
                onChange={(e) => setFormData({ ...formData, auto_scaling_enabled: e.target.checked })}
                className="rounded"
              />
              <label className="text-sm">Enable Auto-scaling</label>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
              >
                {loading ? 'Deploying...' : 'Deploy'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Deployment Details Modal Component
const DeploymentDetailsModal: React.FC<{
  deployment: Deployment;
  onClose: () => void;
}> = ({ deployment, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-2xl font-bold">{deployment.name}</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              ✕
            </button>
          </div>

          <div className="space-y-6">
            {/* Status */}
            <div>
              <h3 className="font-semibold mb-2">Status</h3>
              <div className="flex gap-2 items-center">
                <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                  deployment.status === DeploymentStatus.RUNNING ? 'bg-green-100 text-green-800' :
                  deployment.status === DeploymentStatus.FAILED ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {deployment.status}
                </span>
                <span className="text-sm text-gray-600">
                  Health: {deployment.health_status}
                </span>
              </div>
            </div>

            {/* Configuration */}
            <div>
              <h3 className="font-semibold mb-2">Configuration</h3>
              <div className="bg-gray-50 p-4 rounded">
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(deployment.configuration, null, 2)}
                </pre>
              </div>
            </div>

            {/* Resource Allocation */}
            <div>
              <h3 className="font-semibold mb-2">Resources</h3>
              <div className="bg-gray-50 p-4 rounded">
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(deployment.resource_allocation, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeploymentPage;

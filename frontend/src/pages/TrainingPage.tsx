import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/Dashboard/DashboardLayout';
import { trainingAPI, modelsAPI, datasetsAPI, projectsAPI } from '../services/api';
import { TrainingJob, TrainingStatus, FineTuningMethod } from '../types/training';
import toast from 'react-hot-toast';

const TrainingPage: React.FC = () => {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState<TrainingJob | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Load training jobs
  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, [statusFilter]);

  const loadJobs = async () => {
    try {
      const params = statusFilter !== 'all' ? { status: statusFilter } : {};
      const response = await trainingAPI.list(params);
      setJobs(response.data);
    } catch (error) {
      console.error('Failed to load training jobs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to cancel this training job?')) return;

    try {
      await trainingAPI.cancel(jobId);
      toast.success('Training job cancelled');
      loadJobs();
    } catch (error) {
      toast.error('Failed to cancel job');
    }
  };

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('Are you sure you want to delete this training job?')) return;

    try {
      await trainingAPI.delete(jobId);
      toast.success('Training job deleted');
      loadJobs();
    } catch (error) {
      toast.error('Failed to delete job');
    }
  };

  const getStatusColor = (status: TrainingStatus) => {
    switch (status) {
      case TrainingStatus.COMPLETED:
        return 'bg-green-100 text-green-800';
      case TrainingStatus.RUNNING:
        return 'bg-blue-100 text-blue-800';
      case TrainingStatus.FAILED:
        return 'bg-red-100 text-red-800';
      case TrainingStatus.CANCELLED:
        return 'bg-gray-100 text-gray-800';
      case TrainingStatus.QUEUED:
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <h1 className="text-3xl font-bold text-gray-900">Training Jobs</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            + New Training Job
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
            <option value="queued">Queued</option>
            <option value="running">Running</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>

        {/* Jobs List */}
        {loading ? (
          <div className="card text-center py-12">
            <p className="text-gray-600">Loading training jobs...</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-600">No training jobs found. Create your first job to get started!</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <div key={job.id} className="card hover:shadow-lg transition-shadow">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900">{job.name}</h3>
                      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(job.status)}`}>
                        {job.status}
                      </span>
                      <span className="px-2 py-1 text-xs bg-purple-100 text-purple-800 rounded-full">
                        {job.fine_tuning_method.toUpperCase()}
                      </span>
                    </div>

                    {job.description && (
                      <p className="text-gray-600 text-sm mb-3">{job.description}</p>
                    )}

                    {/* Progress Bar */}
                    {(job.status === TrainingStatus.RUNNING || job.status === TrainingStatus.INITIALIZING) && (
                      <div className="mb-3">
                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                          <span>Progress: {job.progress.toFixed(1)}%</span>
                          <span>Epoch {job.current_epoch}/{job.total_epochs}</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      {job.latest_train_loss && (
                        <div>
                          <span className="text-gray-600">Train Loss:</span>
                          <span className="ml-2 font-semibold">{job.latest_train_loss.toFixed(4)}</span>
                        </div>
                      )}
                      {job.latest_eval_loss && (
                        <div>
                          <span className="text-gray-600">Eval Loss:</span>
                          <span className="ml-2 font-semibold">{job.latest_eval_loss.toFixed(4)}</span>
                        </div>
                      )}
                      {job.best_eval_loss && (
                        <div>
                          <span className="text-gray-600">Best Loss:</span>
                          <span className="ml-2 font-semibold">{job.best_eval_loss.toFixed(4)}</span>
                        </div>
                      )}
                      <div>
                        <span className="text-gray-600">Step:</span>
                        <span className="ml-2 font-semibold">
                          {job.current_step}{job.total_steps ? `/${job.total_steps}` : ''}
                        </span>
                      </div>
                    </div>

                    {/* Error Message */}
                    {job.error_message && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                        <p className="text-sm text-red-800">{job.error_message}</p>
                      </div>
                    )}

                    {/* Timestamps */}
                    <div className="mt-3 text-xs text-gray-500">
                      <span>Created: {new Date(job.created_at).toLocaleString()}</span>
                      {job.started_at && (
                        <span className="ml-4">Started: {new Date(job.started_at).toLocaleString()}</span>
                      )}
                      {job.completed_at && (
                        <span className="ml-4">Completed: {new Date(job.completed_at).toLocaleString()}</span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => setSelectedJob(job)}
                      className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                    >
                      View
                    </button>
                    {(job.status === TrainingStatus.RUNNING || job.status === TrainingStatus.QUEUED) && (
                      <button
                        onClick={() => handleCancelJob(job.id)}
                        className="px-3 py-1 text-sm text-yellow-600 hover:bg-yellow-50 rounded"
                      >
                        Cancel
                      </button>
                    )}
                    {(job.status === TrainingStatus.COMPLETED ||
                      job.status === TrainingStatus.FAILED ||
                      job.status === TrainingStatus.CANCELLED) && (
                      <button
                        onClick={() => handleDeleteJob(job.id)}
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

        {/* Create Job Modal */}
        {showCreateModal && (
          <CreateTrainingJobModal
            onClose={() => setShowCreateModal(false)}
            onSuccess={() => {
              setShowCreateModal(false);
              loadJobs();
            }}
          />
        )}

        {/* Job Details Modal */}
        {selectedJob && (
          <JobDetailsModal
            job={selectedJob}
            onClose={() => setSelectedJob(null)}
          />
        )}
      </div>
    </DashboardLayout>
  );
};

// Create Training Job Modal Component
const CreateTrainingJobModal: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    project_id: '',
    base_model_id: '',
    dataset_id: '',
    fine_tuning_method: FineTuningMethod.LORA,
    num_epochs: 3,
    batch_size: 4,
    learning_rate: 0.0002,
    lora_r: 16,
    lora_alpha: 32,
    lora_dropout: 0.1,
  });

  const [projects, setProjects] = useState<any[]>([]);
  const [models, setModels] = useState<any[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [projectsRes, modelsRes, datasetsRes] = await Promise.all([
        projectsAPI.list(),
        modelsAPI.list(),
        datasetsAPI.list(),
      ]);
      setProjects(projectsRes.data);
      setModels(modelsRes.data);
      setDatasets(datasetsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await trainingAPI.create({
        name: formData.name,
        description: formData.description || undefined,
        project_id: formData.project_id,
        base_model_id: formData.base_model_id,
        dataset_id: formData.dataset_id,
        fine_tuning_method: formData.fine_tuning_method,
        hyperparameters: {
          num_epochs: formData.num_epochs,
          batch_size: formData.batch_size,
          learning_rate: formData.learning_rate,
          lora_r: formData.lora_r,
          lora_alpha: formData.lora_alpha,
          lora_dropout: formData.lora_dropout,
        },
      });
      toast.success('Training job created successfully!');
      onSuccess();
    } catch (error) {
      toast.error('Failed to create training job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-2xl font-bold mb-4">Create Training Job</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Job Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input"
                placeholder="My Fine-tuning Job"
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
              <label className="label">Base Model *</label>
              <select
                required
                value={formData.base_model_id}
                onChange={(e) => setFormData({ ...formData, base_model_id: e.target.value })}
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
              <label className="label">Dataset *</label>
              <select
                required
                value={formData.dataset_id}
                onChange={(e) => setFormData({ ...formData, dataset_id: e.target.value })}
                className="input"
              >
                <option value="">Select a dataset</option>
                {datasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.name} ({dataset.size_rows} rows)
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Fine-tuning Method *</label>
              <select
                required
                value={formData.fine_tuning_method}
                onChange={(e) => setFormData({ ...formData, fine_tuning_method: e.target.value as FineTuningMethod })}
                className="input"
              >
                <option value={FineTuningMethod.LORA}>LoRA</option>
                <option value={FineTuningMethod.QLORA}>QLoRA (4-bit)</option>
                <option value={FineTuningMethod.FULL}>Full Fine-tuning</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Number of Epochs</label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={formData.num_epochs}
                  onChange={(e) => setFormData({ ...formData, num_epochs: parseInt(e.target.value) })}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Batch Size</label>
                <input
                  type="number"
                  min="1"
                  max="128"
                  value={formData.batch_size}
                  onChange={(e) => setFormData({ ...formData, batch_size: parseInt(e.target.value) })}
                  className="input"
                />
              </div>
            </div>

            <div>
              <label className="label">Learning Rate</label>
              <input
                type="number"
                step="0.00001"
                min="0.00001"
                max="0.1"
                value={formData.learning_rate}
                onChange={(e) => setFormData({ ...formData, learning_rate: parseFloat(e.target.value) })}
                className="input"
              />
            </div>

            {(formData.fine_tuning_method === FineTuningMethod.LORA ||
              formData.fine_tuning_method === FineTuningMethod.QLORA) && (
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="label">LoRA Rank (r)</label>
                  <input
                    type="number"
                    min="1"
                    max="256"
                    value={formData.lora_r}
                    onChange={(e) => setFormData({ ...formData, lora_r: parseInt(e.target.value) })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">LoRA Alpha</label>
                  <input
                    type="number"
                    min="1"
                    max="256"
                    value={formData.lora_alpha}
                    onChange={(e) => setFormData({ ...formData, lora_alpha: parseInt(e.target.value) })}
                    className="input"
                  />
                </div>
                <div>
                  <label className="label">LoRA Dropout</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="1"
                    value={formData.lora_dropout}
                    onChange={(e) => setFormData({ ...formData, lora_dropout: parseFloat(e.target.value) })}
                    className="input"
                  />
                </div>
              </div>
            )}

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
                {loading ? 'Creating...' : 'Create Job'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Job Details Modal Component
const JobDetailsModal: React.FC<{
  job: TrainingJob;
  onClose: () => void;
}> = ({ job, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-2xl font-bold">{job.name}</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              ✕
            </button>
          </div>

          <div className="space-y-6">
            {/* Status and Progress */}
            <div>
              <h3 className="font-semibold mb-2">Status</h3>
              <div className="flex gap-2 items-center">
                <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                  job.status === TrainingStatus.COMPLETED ? 'bg-green-100 text-green-800' :
                  job.status === TrainingStatus.RUNNING ? 'bg-blue-100 text-blue-800' :
                  job.status === TrainingStatus.FAILED ? 'bg-red-100 text-red-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {job.status}
                </span>
                <span className="text-sm text-gray-600">
                  {job.progress.toFixed(1)}% - Epoch {job.current_epoch}/{job.total_epochs}
                </span>
              </div>
            </div>

            {/* Hyperparameters */}
            <div>
              <h3 className="font-semibold mb-2">Configuration</h3>
              <div className="bg-gray-50 p-4 rounded">
                <pre className="text-sm overflow-x-auto">
                  {JSON.stringify(job.hyperparameters, null, 2)}
                </pre>
              </div>
            </div>

            {/* Metrics */}
            {Object.keys(job.metrics).length > 0 && (
              <div>
                <h3 className="font-semibold mb-2">Metrics</h3>
                <div className="bg-gray-50 p-4 rounded">
                  <pre className="text-sm overflow-x-auto">
                    {JSON.stringify(job.metrics, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Logs */}
            {job.logs && (
              <div>
                <h3 className="font-semibold mb-2">Training Logs</h3>
                <div className="bg-gray-900 text-green-400 p-4 rounded font-mono text-sm max-h-96 overflow-y-auto">
                  {job.logs}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrainingPage;

export enum TrainingStatus {
  QUEUED = 'queued',
  INITIALIZING = 'initializing',
  RUNNING = 'running',
  PAUSED = 'paused',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum FineTuningMethod {
  LORA = 'lora',
  QLORA = 'qlora',
  FULL = 'full',
  PEFT = 'peft',
}

export interface TrainingJob {
  id: string;
  name: string;
  description?: string;
  project_id: string;
  base_model_id: string;
  dataset_id: string;
  fine_tuning_method: FineTuningMethod;
  hyperparameters: Record<string, any>;
  status: TrainingStatus;
  progress: number;
  current_epoch: number;
  total_epochs: number;
  current_step: number;
  total_steps?: number;
  metrics: Record<string, any>;
  latest_train_loss?: number;
  latest_eval_loss?: number;
  best_eval_loss?: number;
  logs: string;
  error_message?: string;
  output_model_path?: string;
  output_model_id?: string;
  compute_used: Record<string, any>;
  checkpoint_dir?: string;
  best_checkpoint_path?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface TrainingConfig {
  id: string;
  name: string;
  description?: string;
  model_type: string;
  method: FineTuningMethod;
  default_hyperparameters: Record<string, any>;
  is_public: boolean;
  organization_id?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTrainingJobData {
  name: string;
  description?: string;
  project_id: string;
  base_model_id: string;
  dataset_id: string;
  fine_tuning_method: FineTuningMethod;
  hyperparameters?: Record<string, any>;
}

/**
 * Dhruva.AI Domain 12 — Production Operations & Notification Types
 */

export interface SystemHealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  version: string;
  environment: string;
  timestamp: string;
  database: {
    status: string;
    database: string;
    connected: boolean;
    error?: string;
  };
  redis: {
    status: string;
    connected: boolean;
    error?: string;
    mode?: string;
  };
  workers: {
    is_running: boolean;
    total_jobs: number;
    completed: number;
    failed: number;
    running: number;
    queue_depth: number;
  };
  ai_provider: {
    provider: string;
    model: string;
    configured: boolean;
    status: string;
  };
}

export interface AdminOperationsOverview {
  environment: string;
  feature_flags: Record<string, boolean>;
  worker_metrics: {
    is_running: boolean;
    total_jobs: number;
    completed: number;
    failed: number;
    running: number;
    queue_depth: number;
  };
  scheduler_status: {
    is_running: boolean;
    timezone: string;
    scheduled_tasks: Array<{
      name: string;
      interval: string;
      last_run: string | null;
    }>;
  };
  redis_status: Record<string, unknown>;
  ai_status: Record<string, unknown>;
}

export interface BackgroundJobRecord {
  id: string;
  name: string;
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  attempts: number;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface NotificationItem {
  id: string;
  notification_type: string;
  title: string;
  message: string;
  link_url: string | null;
  is_read: boolean;
  created_at: string;
}

export interface NotificationPreferences {
  email_enabled: boolean;
  in_app_enabled: boolean;
  learning_reminders: boolean;
  assessment_alerts: boolean;
  remediation_updates: boolean;
  placement_alerts: boolean;
}

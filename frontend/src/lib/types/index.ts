/**
 * Unified TypeScript type definitions for Dhruva.AI platform foundation.
 */

export type UserRole =
  | "student"
  | "teacher"
  | "mentor"
  | "hod"
  | "placement_officer"
  | "institution_admin"
  | "super_admin";

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  display_name: string;
  role: UserRole;
  institution_id?: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login_at?: string | null;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  role: UserRole;
  refresh_token?: string;
}

export interface SystemHealth {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  environment: string;
  timestamp: string;
  database: {
    status: string;
    database: string;
    connected: boolean;
    error?: string;
  };
}

export interface DomainStatus {
  domain: string;
  is_deterministic: boolean;
  status: "active" | "planned" | "in_development";
  description: string;
}

export interface SystemArchitecture {
  product: string;
  architecture_model: string;
  deterministic_engines: DomainStatus[];
  ai_orchestration: {
    gateway: string;
    model: string;
    privacy_sanitization: string;
    pii_leak_prevention: string;
    api_configured: boolean;
  };
  supported_roles: UserRole[];
}

export interface SM2CalculationResult {
  intervalDays: number;
  repetitions: number;
  easinessFactor: number;
  nextReviewAt: string;
}

export * from "./academic";
export * from "./catalog";
export * from "./profile";
export * from "./content";
export * from "./assessment";
export * from "./mastery";
export * from "./career";
export * from "./project";
export * from "./institutional";
export * from "./remediation";
export * from "./ai";
export * from "./operations";

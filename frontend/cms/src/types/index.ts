export type UserRole = "admin" | "editor";

export interface User {
  id: string;
  username: string;
  email?: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ShowListItem {
  id: string;
  title: string;
  slug: string;
  section: string | null;
  categories: string[];
  synopsis: string | null;
  status: "draft" | "published";
  episode_count: number;
  languages: string[];
  created_at: string;
  updated_at: string;
}

export interface ShowDetail {
  id: string;
  title: string;
  slug: string;
  section: string | null;
  categories: string[];
  synopsis: string | null;
  status: "draft" | "published";
  seasons: SeasonDetail[];
  created_at: string;
  updated_at: string;
}

export interface SeasonDetail {
  id: string;
  show_id: string;
  season_number: number;
  title: string | null;
  episodes: EpisodeDetail[];
  created_at: string;
  updated_at: string;
}

export interface EpisodeDetail {
  id: string;
  custom_id: string | null;
  show_id: string;
  season_id: string;
  episode_number: number;
  episode_title: string;
  duration_seconds: number | null;
  language: "en" | "hi";
  content_group: string;
  status: "draft" | "published";
  artwork_available: string[];
  created_at: string;
  updated_at: string;
}

export interface ArtworkRecord {
  id: string;
  entity_type: "show" | "episode";
  entity_id: string;
  artwork_type: "poster" | "banner" | "thumbnail";
  url: string;
  file_path: string;
  width: number;
  height: number;
  file_size_bytes: number;
  mime_type: string;
}

export interface ValidationIssue {
  code: string;
  severity: "blocking" | "warning";
  entity_type: "show" | "season" | "episode" | "artwork" | "other";
  entity_id: string;
  title?: string;
  problem: string;
  action: string;
  show_id?: string;
  show_title?: string;
  season_number?: number;
  episode_number?: number;
}

export interface GroupedValidationIssues {
  shows: ValidationIssue[];
  seasons: ValidationIssue[];
  episodes: ValidationIssue[];
  artwork: ValidationIssue[];
  other: ValidationIssue[];
}

export interface ValidationReport {
  can_publish: boolean;
  total_issues: number;
  blocking_count: number;
  warning_count: number;
  grouped_by_entity: GroupedValidationIssues;
  all_issues: ValidationIssue[];
}

export interface PublishRun {
  id: string;
  version: number;
  catalogue_version?: number;
  triggered_by: string;
  status: "success" | "failed";
  started_at: string;
  completed_at: string | null;
  published_at: string | null;
  show_count: number;
  episode_count: number;
  file_path: string | null;
  file_size_bytes: number | null;
  error_message: string | null;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const ALLOWED_SECTIONS = ["featured", "series", "minisodes", "songs"] as const;
export const ALLOWED_CATEGORIES = [
  "adventure", "folk", "friendship", "india", "language",
  "learning", "maths", "music", "nature", "reading",
  "science", "singalong", "stories", "travel", "values"
] as const;
export const ALLOWED_LANGUAGES = [
  { code: "en", label: "English (en)" },
  { code: "hi", label: "Hindi (hi)" }
] as const;

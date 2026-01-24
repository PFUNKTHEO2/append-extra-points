import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    'Supabase credentials not found. Comments feature will be disabled. ' +
    'Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file.'
  );
}

export const supabase = supabaseUrl && supabaseAnonKey
  ? createClient(supabaseUrl, supabaseAnonKey)
  : null;

export const isSupabaseConfigured = !!supabase;

// Types for our database
export interface Profile {
  id: string;
  display_name: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface GameComment {
  id: string;
  game_id: string;
  author_id: string;
  content: string;
  likes_count: number;
  reports_count: number;
  is_hidden: boolean;
  is_edited: boolean;
  created_at: string;
  updated_at: string;
  // Joined data
  author?: Profile;
  user_has_liked?: boolean;
}

export interface CommentLike {
  id: string;
  comment_id: string;
  user_id: string;
  created_at: string;
}

export type ReportReason = 'spam' | 'harassment' | 'inappropriate' | 'other';

export interface CommentReport {
  id: string;
  comment_id: string;
  reporter_id: string;
  reason: ReportReason;
  details: string | null;
  created_at: string;
}

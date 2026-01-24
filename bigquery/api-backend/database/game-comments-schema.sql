-- NEPSAC GameDay Comments Schema
-- Deploy this to Supabase SQL Editor

-- ============================================================================
-- User Profiles Extension (for display names)
-- ============================================================================

-- Add display_name column to existing profiles table if not exists
-- If you don't have a profiles table, create one:
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add display_name column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
    AND table_name = 'profiles'
    AND column_name = 'display_name'
  ) THEN
    ALTER TABLE public.profiles ADD COLUMN display_name TEXT;
  END IF;
END $$;

-- Create trigger to auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id)
  VALUES (NEW.id)
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================================================
-- Game Comments Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.game_comments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id TEXT NOT NULL,
  author_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  content TEXT NOT NULL CHECK (char_length(content) <= 500),
  likes_count INTEGER DEFAULT 0,
  reports_count INTEGER DEFAULT 0,
  is_hidden BOOLEAN DEFAULT FALSE,
  is_edited BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_game_comments_game_id ON public.game_comments(game_id);
CREATE INDEX IF NOT EXISTS idx_game_comments_author_id ON public.game_comments(author_id);
CREATE INDEX IF NOT EXISTS idx_game_comments_created_at ON public.game_comments(created_at DESC);

-- ============================================================================
-- Comment Likes Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.comment_likes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comment_id UUID NOT NULL REFERENCES public.game_comments(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(comment_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_comment_likes_comment_id ON public.comment_likes(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_likes_user_id ON public.comment_likes(user_id);

-- ============================================================================
-- Comment Reports Table
-- ============================================================================

CREATE TYPE report_reason AS ENUM ('spam', 'harassment', 'inappropriate', 'other');

CREATE TABLE IF NOT EXISTS public.comment_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  comment_id UUID NOT NULL REFERENCES public.game_comments(id) ON DELETE CASCADE,
  reporter_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  reason report_reason NOT NULL,
  details TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(comment_id, reporter_id)
);

CREATE INDEX IF NOT EXISTS idx_comment_reports_comment_id ON public.comment_reports(comment_id);

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to update likes_count on game_comments
CREATE OR REPLACE FUNCTION update_comment_likes_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE public.game_comments
    SET likes_count = likes_count + 1
    WHERE id = NEW.comment_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE public.game_comments
    SET likes_count = likes_count - 1
    WHERE id = OLD.comment_id;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_comment_like_change ON public.comment_likes;
CREATE TRIGGER on_comment_like_change
  AFTER INSERT OR DELETE ON public.comment_likes
  FOR EACH ROW EXECUTE FUNCTION update_comment_likes_count();

-- Function to update reports_count and auto-hide after 3 reports
CREATE OR REPLACE FUNCTION update_comment_reports_count()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.game_comments
  SET
    reports_count = reports_count + 1,
    is_hidden = CASE WHEN reports_count + 1 >= 3 THEN TRUE ELSE is_hidden END
  WHERE id = NEW.comment_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_comment_report ON public.comment_reports;
CREATE TRIGGER on_comment_report
  AFTER INSERT ON public.comment_reports
  FOR EACH ROW EXECUTE FUNCTION update_comment_reports_count();

-- Function to check if edit is within 15-minute window
CREATE OR REPLACE FUNCTION can_edit_comment(comment_created_at TIMESTAMPTZ)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN (NOW() - comment_created_at) < INTERVAL '15 minutes';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Row Level Security (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_comments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comment_likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.comment_reports ENABLE ROW LEVEL SECURITY;

-- Profiles policies
DROP POLICY IF EXISTS "Users can view all profiles" ON public.profiles;
CREATE POLICY "Users can view all profiles"
  ON public.profiles FOR SELECT
  TO authenticated
  USING (true);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
  ON public.profiles FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Game Comments policies
DROP POLICY IF EXISTS "Authenticated users can view non-hidden comments" ON public.game_comments;
CREATE POLICY "Authenticated users can view non-hidden comments"
  ON public.game_comments FOR SELECT
  TO authenticated
  USING (is_hidden = FALSE OR author_id = auth.uid());

DROP POLICY IF EXISTS "Authenticated users with display name can insert comments" ON public.game_comments;
CREATE POLICY "Authenticated users with display name can insert comments"
  ON public.game_comments FOR INSERT
  TO authenticated
  WITH CHECK (
    author_id = auth.uid() AND
    EXISTS (
      SELECT 1 FROM public.profiles
      WHERE id = auth.uid()
      AND display_name IS NOT NULL
      AND display_name != ''
    )
  );

DROP POLICY IF EXISTS "Users can update own comments within edit window" ON public.game_comments;
CREATE POLICY "Users can update own comments within edit window"
  ON public.game_comments FOR UPDATE
  TO authenticated
  USING (
    author_id = auth.uid() AND
    can_edit_comment(created_at)
  )
  WITH CHECK (author_id = auth.uid());

DROP POLICY IF EXISTS "Users can delete own comments" ON public.game_comments;
CREATE POLICY "Users can delete own comments"
  ON public.game_comments FOR DELETE
  TO authenticated
  USING (author_id = auth.uid());

-- Comment Likes policies
DROP POLICY IF EXISTS "Authenticated users can view likes" ON public.comment_likes;
CREATE POLICY "Authenticated users can view likes"
  ON public.comment_likes FOR SELECT
  TO authenticated
  USING (true);

DROP POLICY IF EXISTS "Authenticated users can like comments" ON public.comment_likes;
CREATE POLICY "Authenticated users can like comments"
  ON public.comment_likes FOR INSERT
  TO authenticated
  WITH CHECK (user_id = auth.uid());

DROP POLICY IF EXISTS "Users can remove own likes" ON public.comment_likes;
CREATE POLICY "Users can remove own likes"
  ON public.comment_likes FOR DELETE
  TO authenticated
  USING (user_id = auth.uid());

-- Comment Reports policies
DROP POLICY IF EXISTS "Authenticated users can report comments" ON public.comment_reports;
CREATE POLICY "Authenticated users can report comments"
  ON public.comment_reports FOR INSERT
  TO authenticated
  WITH CHECK (reporter_id = auth.uid());

-- Users cannot see reports (admin only via service role)
DROP POLICY IF EXISTS "Users can view own reports" ON public.comment_reports;
CREATE POLICY "Users can view own reports"
  ON public.comment_reports FOR SELECT
  TO authenticated
  USING (reporter_id = auth.uid());

-- ============================================================================
-- Realtime Configuration
-- ============================================================================

-- Enable realtime for game_comments
ALTER PUBLICATION supabase_realtime ADD TABLE public.game_comments;

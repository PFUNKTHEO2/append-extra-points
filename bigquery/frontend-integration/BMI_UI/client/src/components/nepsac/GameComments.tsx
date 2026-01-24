import { useState, useEffect, useCallback } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Flag, Send, MessageCircle, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useAuth } from '@/contexts/AuthContext';
import { AuthModal } from './AuthModal';
import { DisplayNameModal } from './DisplayNameModal';
import { supabase, isSupabaseConfigured, type GameComment, type ReportReason } from '@/lib/supabase';

interface GameCommentsProps {
  gameId: string;
}

const MAX_COMMENT_LENGTH = 500;

export function GameComments({ gameId }: GameCommentsProps) {
  const { isAuthenticated, hasDisplayName, user, profile, isSupabaseEnabled } = useAuth();
  const [comments, setComments] = useState<GameComment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [showDisplayNameModal, setShowDisplayNameModal] = useState(false);

  // Don't render if Supabase is not configured
  if (!isSupabaseEnabled || !supabase) {
    return null;
  }

  const fetchComments = useCallback(async () => {
    if (!isAuthenticated) {
      setIsLoading(false);
      return;
    }

    const { data, error } = await supabase
      .from('game_comments')
      .select(`
        *,
        author:profiles!author_id(id, display_name, avatar_url)
      `)
      .eq('game_id', gameId)
      .order('created_at', { ascending: false });

    if (error) {
      console.error('Error fetching comments:', error);
    } else if (data) {
      // Check which comments the current user has liked
      const { data: likes } = await supabase
        .from('comment_likes')
        .select('comment_id')
        .eq('user_id', user!.id);

      const likedCommentIds = new Set(likes?.map(l => l.comment_id) || []);

      const commentsWithLikeStatus = data.map(comment => ({
        ...comment,
        user_has_liked: likedCommentIds.has(comment.id),
      }));

      setComments(commentsWithLikeStatus);
    }

    setIsLoading(false);
  }, [gameId, isAuthenticated, user]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  // Real-time subscription
  useEffect(() => {
    if (!isAuthenticated) return;

    const channel = supabase
      .channel(`game_comments:${gameId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'game_comments',
          filter: `game_id=eq.${gameId}`,
        },
        () => {
          fetchComments();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [gameId, isAuthenticated, fetchComments]);

  if (!isAuthenticated) {
    return (
      <>
        <LoginGate onLoginClick={() => setShowAuthModal(true)} />
        <AuthModal open={showAuthModal} onOpenChange={setShowAuthModal} />
      </>
    );
  }

  if (!hasDisplayName) {
    return (
      <>
        <DisplayNamePrompt onSetupClick={() => setShowDisplayNameModal(true)} />
        <DisplayNameModal open={showDisplayNameModal} onOpenChange={setShowDisplayNameModal} />
      </>
    );
  }

  return (
    <div className="glass-panel">
      <h3 className="comments-title" style={{
        fontFamily: 'Orbitron, sans-serif',
        fontSize: '1.2rem',
        textAlign: 'center',
        marginBottom: '20px',
        color: '#22c55e',
        textTransform: 'uppercase',
        letterSpacing: '3px',
      }}>
        <MessageCircle className="inline-block w-5 h-5 mr-2 -mt-1" />
        Fan Comments
      </h3>

      <GuidelinesReminder />

      <CommentInput
        gameId={gameId}
        onCommentPosted={fetchComments}
        displayName={profile?.display_name || 'Anonymous'}
      />

      {isLoading ? (
        <div className="text-center text-gray-400 py-8">Loading comments...</div>
      ) : comments.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <MessageCircle className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No comments yet. Be the first!</p>
        </div>
      ) : (
        <div className="space-y-4 mt-6">
          <AnimatePresence>
            {comments.map((comment) => (
              <CommentCard
                key={comment.id}
                comment={comment}
                currentUserId={user!.id}
                onUpdate={fetchComments}
              />
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

function LoginGate({ onLoginClick }: { onLoginClick: () => void }) {
  return (
    <div className="glass-panel text-center py-12">
      <LogIn className="w-12 h-12 mx-auto mb-4 text-purple-400" />
      <h3 style={{
        fontFamily: 'Orbitron, sans-serif',
        fontSize: '1.2rem',
        marginBottom: '10px',
        color: '#8b5cf6',
      }}>
        Join the Conversation
      </h3>
      <p className="text-gray-400 mb-6 max-w-md mx-auto">
        Sign in to view and post comments. Share your thoughts and support your team!
      </p>
      <Button
        onClick={onLoginClick}
        className="bg-gradient-to-r from-purple-600 to-fuchsia-600 hover:from-purple-700 hover:to-fuchsia-700"
      >
        <LogIn className="w-4 h-4 mr-2" />
        Sign In to Comment
      </Button>
    </div>
  );
}

function DisplayNamePrompt({ onSetupClick }: { onSetupClick: () => void }) {
  return (
    <div className="glass-panel text-center py-12">
      <MessageCircle className="w-12 h-12 mx-auto mb-4 text-cyan-400" />
      <h3 style={{
        fontFamily: 'Orbitron, sans-serif',
        fontSize: '1.2rem',
        marginBottom: '10px',
        color: '#06b6d4',
      }}>
        Almost There!
      </h3>
      <p className="text-gray-400 mb-6 max-w-md mx-auto">
        Set your display name to start commenting. This is how other fans will see you.
      </p>
      <Button
        onClick={onSetupClick}
        className="bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700"
      >
        Set Display Name
      </Button>
    </div>
  );
}

function GuidelinesReminder() {
  return (
    <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-3 mb-4 text-center">
      <p className="text-sm text-green-300">
        Have fun, support your team, but keep it classy!
      </p>
    </div>
  );
}

interface CommentInputProps {
  gameId: string;
  onCommentPosted: () => void;
  displayName: string;
}

function CommentInput({ gameId, onCommentPosted, displayName }: CommentInputProps) {
  const [content, setContent] = useState('');
  const [isPosting, setIsPosting] = useState(false);
  const { user } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const trimmedContent = content.trim();
    if (!trimmedContent || !supabase || !user) return;

    setIsPosting(true);

    const { error } = await supabase.from('game_comments').insert({
      game_id: gameId,
      author_id: user.id,
      content: trimmedContent,
    });

    if (error) {
      console.error('Error posting comment:', error);
    } else {
      setContent('');
      onCommentPosted();
    }

    setIsPosting(false);
  };

  const charsRemaining = MAX_COMMENT_LENGTH - content.length;
  const isOverLimit = charsRemaining < 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-fuchsia-500 flex items-center justify-center text-white font-bold shrink-0">
          {displayName.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Share your thoughts..."
            rows={2}
            maxLength={MAX_COMMENT_LENGTH + 50}
            className="w-full bg-[#1e1e2e] border border-[#3a3a4e] rounded-lg px-4 py-3 text-white placeholder:text-gray-500 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/30 resize-none"
          />
          <div className="flex items-center justify-between mt-2">
            <span className={`text-xs ${isOverLimit ? 'text-red-400' : charsRemaining < 50 ? 'text-yellow-400' : 'text-gray-500'}`}>
              {charsRemaining} characters remaining
            </span>
            <Button
              type="submit"
              disabled={isPosting || isOverLimit || content.trim().length === 0}
              size="sm"
              className="bg-gradient-to-r from-purple-600 to-fuchsia-600 hover:from-purple-700 hover:to-fuchsia-700"
            >
              {isPosting ? 'Posting...' : (
                <>
                  <Send className="w-4 h-4 mr-1" />
                  Post
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
}

interface CommentCardProps {
  comment: GameComment;
  currentUserId: string;
  onUpdate: () => void;
}

function CommentCard({ comment, currentUserId, onUpdate }: CommentCardProps) {
  const [isLiking, setIsLiking] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const isOwnComment = comment.author_id === currentUserId;
  const authorName = comment.author?.display_name || 'Anonymous';
  const timeAgo = formatDistanceToNow(new Date(comment.created_at), { addSuffix: true });

  const handleLike = async () => {
    if (!supabase || isLiking) return;

    setIsLiking(true);

    if (comment.user_has_liked) {
      await supabase
        .from('comment_likes')
        .delete()
        .eq('comment_id', comment.id)
        .eq('user_id', currentUserId);
    } else {
      await supabase.from('comment_likes').insert({
        comment_id: comment.id,
        user_id: currentUserId,
      });
    }

    onUpdate();
    setIsLiking(false);
  };

  const handleDelete = async () => {
    if (!supabase || isDeleting || !window.confirm('Are you sure you want to delete this comment?')) return;

    setIsDeleting(true);
    await supabase.from('game_comments').delete().eq('id', comment.id);
    onUpdate();
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="bg-[#1a1a2a] border border-[#2a2a3e] rounded-lg p-4"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold shrink-0">
            {authorName.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-white">{authorName}</span>
              <span className="text-xs text-gray-500">{timeAgo}</span>
              {comment.is_edited && (
                <span className="text-xs text-gray-600">(edited)</span>
              )}
            </div>
            <p className="text-gray-300 mt-1 break-words">{comment.content}</p>
            <div className="flex items-center gap-4 mt-3">
              <button
                onClick={handleLike}
                disabled={isLiking}
                className={`flex items-center gap-1 text-sm transition-colors ${
                  comment.user_has_liked
                    ? 'text-red-400 hover:text-red-300'
                    : 'text-gray-500 hover:text-red-400'
                }`}
              >
                <Heart className={`w-4 h-4 ${comment.user_has_liked ? 'fill-current' : ''}`} />
                <span>{comment.likes_count}</span>
              </button>

              {!isOwnComment && (
                <button
                  onClick={() => setShowReportModal(true)}
                  className="flex items-center gap-1 text-sm text-gray-500 hover:text-yellow-400 transition-colors"
                >
                  <Flag className="w-4 h-4" />
                  <span>Report</span>
                </button>
              )}

              {isOwnComment && (
                <button
                  onClick={handleDelete}
                  disabled={isDeleting}
                  className="flex items-center gap-1 text-sm text-gray-500 hover:text-red-400 transition-colors"
                >
                  {isDeleting ? 'Deleting...' : 'Delete'}
                </button>
              )}
            </div>
          </div>
        </div>
      </motion.div>

      <ReportModal
        open={showReportModal}
        onOpenChange={setShowReportModal}
        commentId={comment.id}
        onReported={onUpdate}
      />
    </>
  );
}

interface ReportModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  commentId: string;
  onReported: () => void;
}

function ReportModal({ open, onOpenChange, commentId, onReported }: ReportModalProps) {
  const [reason, setReason] = useState<ReportReason | null>(null);
  const [details, setDetails] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  const reasons: { value: ReportReason; label: string; description: string }[] = [
    { value: 'spam', label: 'Spam', description: 'Promotional content or repetitive messages' },
    { value: 'harassment', label: 'Harassment', description: 'Bullying or targeting someone' },
    { value: 'inappropriate', label: 'Inappropriate', description: 'Offensive or harmful content' },
    { value: 'other', label: 'Other', description: 'Something else not listed above' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason || !supabase || !user) return;

    setIsSubmitting(true);
    setError(null);

    const { error: submitError } = await supabase.from('comment_reports').insert({
      comment_id: commentId,
      reporter_id: user.id,
      reason,
      details: details.trim() || null,
    });

    if (submitError) {
      if (submitError.code === '23505') {
        setError('You have already reported this comment');
      } else {
        setError(submitError.message);
      }
    } else {
      onOpenChange(false);
      setReason(null);
      setDetails('');
      onReported();
    }

    setIsSubmitting(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-[#14141e] border-[#2a2a3e] text-white">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold" style={{ fontFamily: 'Orbitron, sans-serif' }}>
            Report Comment
          </DialogTitle>
          <DialogDescription className="text-gray-400">
            Help us keep the community safe. Reports are anonymous.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <label className="text-sm text-gray-300">Reason for report</label>
            <div className="space-y-2">
              {reasons.map((r) => (
                <label
                  key={r.value}
                  className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                    reason === r.value
                      ? 'border-purple-500 bg-purple-500/10'
                      : 'border-[#3a3a4e] hover:border-[#4a4a5e]'
                  }`}
                >
                  <input
                    type="radio"
                    name="reason"
                    value={r.value}
                    checked={reason === r.value}
                    onChange={() => setReason(r.value)}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium text-white">{r.label}</div>
                    <div className="text-xs text-gray-500">{r.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm text-gray-300">Additional details (optional)</label>
            <textarea
              value={details}
              onChange={(e) => setDetails(e.target.value)}
              placeholder="Provide more context..."
              rows={3}
              maxLength={500}
              className="w-full bg-[#1e1e2e] border border-[#3a3a4e] rounded-lg px-4 py-3 text-white placeholder:text-gray-500 focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/30 resize-none"
            />
          </div>

          {error && (
            <div className="text-red-400 text-sm text-center p-2 bg-red-500/10 rounded-md">
              {error}
            </div>
          )}

          <div className="flex gap-3 justify-end">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              className="bg-transparent border-[#3a3a4e] text-gray-300 hover:bg-[#2a2a3e] hover:text-white"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={!reason || isSubmitting}
              className="bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Report'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

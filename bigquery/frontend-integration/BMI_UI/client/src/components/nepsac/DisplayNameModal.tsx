import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useAuth } from '@/contexts/AuthContext';

interface DisplayNameModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function DisplayNameModal({ open, onOpenChange }: DisplayNameModalProps) {
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const { updateDisplayName } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedName = displayName.trim();

    if (trimmedName.length < 3) {
      setError('Display name must be at least 3 characters');
      return;
    }

    if (trimmedName.length > 20) {
      setError('Display name must be 20 characters or less');
      return;
    }

    if (!/^[a-zA-Z0-9_\-\s]+$/.test(trimmedName)) {
      setError('Display name can only contain letters, numbers, spaces, underscores, and hyphens');
      return;
    }

    setIsLoading(true);

    try {
      const { error } = await updateDisplayName(trimmedName);

      if (error) {
        setError(error.message);
      } else {
        onOpenChange(false);
        setDisplayName('');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-[#14141e] border-[#2a2a3e] text-white">
        <DialogHeader>
          <DialogTitle className="text-xl font-bold text-center" style={{ fontFamily: 'Orbitron, sans-serif' }}>
            Set Your Display Name
          </DialogTitle>
          <DialogDescription className="text-center text-gray-400">
            Choose a name that will appear with your comments
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Input
              type="text"
              placeholder="Your display name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              maxLength={20}
              required
              className="bg-[#1e1e2e] border-[#3a3a4e] text-white placeholder:text-gray-500 focus-visible:border-purple-500 focus-visible:ring-purple-500/30"
            />
            <p className="text-xs text-gray-500 text-right">
              {displayName.length}/20 characters
            </p>
          </div>

          {error && (
            <div className="text-red-400 text-sm text-center p-2 bg-red-500/10 rounded-md">
              {error}
            </div>
          )}

          <div className="bg-gradient-to-r from-purple-500/10 to-fuchsia-500/10 border border-purple-500/30 rounded-lg p-4">
            <h4 className="font-semibold text-sm text-purple-300 mb-2">
              Community Guidelines
            </h4>
            <p className="text-sm text-gray-300 leading-relaxed">
              Have fun, support your team, but keep it classy!
            </p>
            <ul className="text-xs text-gray-400 mt-2 space-y-1 list-disc list-inside">
              <li>Be respectful to other fans and players</li>
              <li>No hate speech, harassment, or spam</li>
              <li>Comments with 3+ reports will be hidden</li>
            </ul>
          </div>

          <Button
            type="submit"
            disabled={isLoading || displayName.trim().length < 3}
            className="w-full bg-gradient-to-r from-purple-600 to-fuchsia-600 hover:from-purple-700 hover:to-fuchsia-700 text-white"
          >
            {isLoading ? 'Saving...' : 'Save Display Name'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

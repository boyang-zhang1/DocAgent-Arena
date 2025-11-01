/**
 * Loading overlay component for long-running operations
 * Shows a translucent overlay with spinner and message
 */

import { Loader2 } from 'lucide-react';

interface LoadingOverlayProps {
  isOpen: boolean;
  message?: string;
  submessage?: string;
}

export function LoadingOverlay({
  isOpen,
  message = 'Loading...',
  submessage,
}: LoadingOverlayProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="bg-card text-card-foreground rounded-lg border p-8 shadow-lg">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <div className="text-center">
            <p className="text-lg font-semibold">{message}</p>
            {submessage && (
              <p className="mt-2 text-sm text-muted-foreground">{submessage}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

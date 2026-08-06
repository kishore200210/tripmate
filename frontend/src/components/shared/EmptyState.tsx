/**
 * src/components/shared/EmptyState.tsx
 *
 * Generic empty-state UI for use across all list pages.
 */

import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  message: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed bg-neutral-50 py-16 px-8 text-center">
      <div className="mb-4 rounded-full bg-neutral-100 p-4">
        <Icon className="h-8 w-8 text-neutral-400" />
      </div>
      <h3 className="text-lg font-semibold text-neutral-800">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-neutral-500">{message}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
}

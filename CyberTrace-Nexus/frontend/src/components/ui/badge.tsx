/**
 * badge.tsx - Reusable badge component.
 */

import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-[var(--accent)] text-[var(--background)]",
        secondary:
          "border-transparent bg-[var(--background-tertiary)] text-[var(--foreground)]",
        success:
          "border-transparent bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/30",
        warning:
          "border-transparent bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/30",
        danger:
          "border-transparent bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/30",
        info: "border-transparent bg-[var(--info)]/10 text-[var(--info)] border-[var(--info)]/30",
        outline: "border-[var(--border)] text-[var(--foreground)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  );
}

export { Badge, badgeVariants };

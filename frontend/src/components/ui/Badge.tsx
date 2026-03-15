import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "./Button"

const badgeVariants = cva(
    "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
    {
        variants: {
            variant: {
                default:
                    "border-transparent bg-indigo-600 text-white hover:bg-indigo-800",
                secondary:
                    "border-transparent bg-indigo-100 text-indigo-900 hover:bg-indigo-200",
                destructive:
                    "border-transparent bg-red-100 text-red-900 hover:bg-red-200",
                success:
                    "border-transparent bg-emerald-100 text-emerald-900 hover:bg-emerald-200",
                outline: "text-gray-900 border-gray-200",
            },
        },
        defaultVariants: {
            variant: "default",
        },
    }
)

export interface BadgeProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> { }

function Badge({ className, variant, ...props }: BadgeProps) {
    return (
        <div className={cn(badgeVariants({ variant }), className)} {...props} />
    )
}

export { Badge, badgeVariants }

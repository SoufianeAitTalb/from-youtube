import * as React from "react"

import { cva, type VariantProps } from "class-variance-authority"
import clsx from "clsx"
import { twMerge } from "tailwind-merge"

// Utility for merging tailwind classes
export function cn(...inputs: (string | undefined | null | false)[]) {
    return twMerge(clsx(inputs))
}

const buttonVariants = cva(
    "inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:pointer-events-none disabled:opacity-50 active:scale-95 shadow-sm",
    {
        variants: {
            variant: {
                default:
                    "bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-200 shadow-md",
                destructive:
                    "bg-red-500 text-white hover:bg-red-600 shadow-red-200",
                outline:
                    "border border-gray-200 bg-white hover:bg-gray-100 hover:text-gray-900",
                secondary:
                    "bg-gray-100 text-gray-900 hover:bg-gray-200",
                ghost: "hover:bg-gray-100 hover:text-gray-900 shadow-none",
                link: "text-indigo-600 underline-offset-4 hover:underline shadow-none",
                success: "bg-emerald-500 text-white hover:bg-emerald-600 shadow-emerald-200",
            },
            size: {
                default: "h-10 px-4 py-2",
                sm: "h-9 rounded-md px-3",
                lg: "h-11 rounded-md px-8 text-base",
                icon: "h-10 w-10",
            },
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    }
)

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
    asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant, size, asChild = false, ...props }, ref) => {
        return (
            <button
                className={cn(buttonVariants({ variant, size, className }))}
                ref={ref}
                {...props}
            />
        )
    }
)
Button.displayName = "Button"

export { Button, buttonVariants }

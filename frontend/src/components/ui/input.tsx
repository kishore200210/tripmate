import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-12 w-full min-w-0 rounded-xl border border-neutral-200 bg-white px-4 py-2 text-base text-[#111827] transition-colors outline-none file:inline-flex file:h-6 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-[#111827] placeholder:text-[#9CA3AF] focus-visible:border-blue-500 focus-visible:ring-3 focus-visible:ring-blue-500/20 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-neutral-50 disabled:opacity-50 aria-invalid:border-red-500 aria-invalid:ring-3 aria-invalid:ring-red-500/20 md:text-sm",
        className
      )}
      {...props}
    />
  )
}

export { Input }

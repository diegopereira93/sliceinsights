import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface PerformanceBarProps {
    label: string;
    value: number; // 1 to 5
    icon: LucideIcon;
    activeColorClass?: string;
}

export function PerformanceBar({
    label,
    value,
    icon: Icon,
    activeColorClass = "bg-primary"
}: PerformanceBarProps) {
    // Ensure value is between 1 and 5
    const normalizedValue = Math.min(Math.max(Math.round(value), 0), 5);

    return (
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                <Icon className={cn("w-5 h-5 flex-shrink-0", activeColorClass.replace('bg-', 'text-'))} />
                <span className="text-sm font-bold uppercase tracking-wider">{label}</span>
            </div>
            <div className="flex gap-1">
                {[1, 2, 3, 4, 5].map((i) => (
                    <div
                        key={i}
                        className={cn(
                            "w-6 h-1.5 rounded-full",
                            i <= normalizedValue ? activeColorClass : "bg-muted"
                        )}
                    />
                ))}
            </div>
        </div>
    );
}

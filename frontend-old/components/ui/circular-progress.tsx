import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";

interface CircularProgressProps {
    value: number;
    label: string;
    icon: LucideIcon;
    colorClass?: string;
    strokeColor?: string;
    size?: number;
}

export function CircularProgress({
    value,
    label,
    icon: Icon,
    colorClass = "text-primary",
    strokeColor = "currentColor",
    size = 70
}: CircularProgressProps) {
    const radius = 30;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (value / 100) * circumference;

    return (
        <div className="flex flex-col items-center gap-2">
            <div className="relative" style={{ width: size, height: size }}>
                <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
                    {/* Background Circle */}
                    <circle
                        cx="40"
                        cy="40"
                        r={radius}
                        fill="transparent"
                        stroke="currentColor"
                        strokeWidth="6"
                        className="text-white/5"
                    />
                    {/* Progress Circle */}
                    <circle
                        cx="40"
                        cy="40"
                        r={radius}
                        fill="transparent"
                        stroke={strokeColor}
                        strokeWidth="6"
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        strokeLinecap="round"
                        className={cn("transition-all duration-1000 ease-out")}
                    />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-black text-foreground">
                        {Math.round(value)}%
                    </span>
                </div>
            </div>
            <div className="flex items-center justify-center gap-1.5 mt-1">
                <Icon className={cn("w-4 h-4 flex-shrink-0", colorClass)} />
                <span className="text-[10px] font-black uppercase tracking-wider text-muted-foreground whitespace-nowrap">
                    {label}
                </span>
            </div>
        </div>
    );
}

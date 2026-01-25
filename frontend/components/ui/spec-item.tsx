import { LucideIcon } from "lucide-react";

interface SpecItemProps {
    icon: LucideIcon;
    label: string;
    value: string | number;
}

export function SpecItem({ icon: Icon, label, value }: SpecItemProps) {
    return (
        <div className="bg-muted/30 p-4 rounded-2xl flex flex-col gap-1">
            <Icon className="w-5 h-5 text-primary-text mb-1" />
            <span className="text-[10px] text-muted-foreground uppercase font-bold">{label}</span>
            <span className="font-bold line-clamp-1">{value}</span>
        </div>
    );
}

import { cn } from "@/lib/utils";
import { Feather, Scale, Hammer, HelpCircle } from "lucide-react";

interface WeightSensationScaleProps {
    swingWeight: number | null | undefined;
    className?: string;
}

export function WeightSensationScale({ swingWeight, className }: WeightSensationScaleProps) {
    if (swingWeight === null || swingWeight === undefined) {
        return (
            <div className={cn("flex flex-col gap-1", className)}>
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-tighter">Sensação de Peso</span>
                <div className="flex items-center gap-2 text-muted-foreground/50">
                    <HelpCircle className="w-4 h-4" />
                    <span className="text-xs font-semibold italic">Dados indisponíveis</span>
                </div>
            </div>
        );
    }

    let label = "Equilibrada";
    let description = "Ideal para o dia-a-dia";
    let Icon = Scale;
    let colorClass = "text-blue-400";
    let bgClass = "bg-blue-400/10";
    let percentage = 50;

    if (swingWeight < 110) {
        label = "Parece uma Pena";
        description = "Mão extremamente leve";
        Icon = Feather;
        colorClass = "text-emerald-400";
        bgClass = "bg-emerald-400/10";
        percentage = 20;
    } else if (swingWeight > 120) {
        label = "Cabeça Pesada";
        description = "Poder de martelo (Power)";
        Icon = Hammer;
        colorClass = "text-rose-500";
        bgClass = "bg-rose-500/10";
        percentage = 90;
    } else if (swingWeight >= 115) {
        label = "Manuseio Firme";
        description = "Foco em estabilidade";
        Icon = Scale;
        colorClass = "text-amber-400";
        bgClass = "bg-amber-400/10";
        percentage = 70;
    }

    return (
        <div className={cn("flex flex-col gap-1.5", className)}>
            <div className="flex justify-between items-end">
                <span className="text-[10px] text-muted-foreground uppercase font-bold tracking-tighter">Sensação de Peso</span>
                <span className={cn("text-[10px] font-bold px-1.5 py-0.5 rounded-full", bgClass, colorClass)}>
                    SW {swingWeight}
                </span>
            </div>

            <div className="bg-white/5 border border-white/10 rounded-lg p-2 flex items-center gap-3">
                <div className={cn("p-1.5 rounded-md", bgClass)}>
                    <Icon className={cn("w-4 h-4", colorClass)} />
                </div>
                <div className="flex flex-col">
                    <span className="text-sm font-bold leading-none">{label}</span>
                    <span className="text-[10px] text-muted-foreground leading-tight mt-0.5">{description}</span>
                </div>
            </div>

            <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                <div
                    className={cn("h-full transition-all duration-500 ease-out",
                        swingWeight < 110 ? "bg-emerald-400" :
                            swingWeight > 120 ? "bg-rose-500" :
                                swingWeight >= 115 ? "bg-amber-400" : "bg-blue-400"
                    )}
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}

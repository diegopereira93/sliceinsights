import { Paddle } from "@/components/paddle/paddle-card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Trophy, Medal, Crown, ArrowRight, ExternalLink, ChevronRight } from "lucide-react";
import Link from "next/link";

export interface LeaderboardItem {
    rank: number;
    paddle: Paddle;
    value: number | string;
    unit?: string;
}

interface LeaderboardCardProps {
    title: string;
    subtitle?: string;
    icon: React.ElementType;
    data: LeaderboardItem[];
    colorClass?: string; // e.g., "text-yellow-600", "bg-yellow-500"
    onPaddleClick?: (paddle: Paddle) => void;
}

export function LeaderboardCard({ title, subtitle, icon: Icon, data, colorClass = "text-primary", onPaddleClick }: LeaderboardCardProps) {
    const top3 = data.slice(0, 3);
    const rest = data.slice(3, 10);

    return (
        <div className="bg-card border border-border/50 rounded-3xl overflow-hidden shadow-sm flex flex-col h-full">
            <div className="p-5 border-b border-border/50 flex items-center gap-3 bg-muted/20">
                <div className={cn("p-2 rounded-xl bg-background shadow-sm", colorClass)}>
                    <Icon className="w-6 h-6" />
                </div>
                <div>
                    <h3 className="font-bold text-lg tracking-tight leading-none">{title}</h3>
                    {subtitle && <p className="text-xs text-muted-foreground mt-1 font-medium">{subtitle}</p>}
                </div>
            </div>

            <div className="p-0 flex-1">
                {/* Top 3 */}
                <div className="divide-y divide-border/30">
                    {top3.map((item) => (
                        <div
                            key={item.paddle.id}
                            onClick={() => onPaddleClick?.(item.paddle)}
                            className="flex items-center gap-4 p-4 hover:bg-muted/50 transition-colors cursor-pointer group relative"
                            title={`${item.paddle.brand} ${item.paddle.name}`}
                        >
                            <div className="flex-shrink-0 w-8 flex justify-center">
                                {item.rank === 1 && <Trophy className="w-6 h-6 text-yellow-500 fill-yellow-500/20" />}
                                {item.rank === 2 && <Medal className="w-6 h-6 text-slate-400 fill-slate-400/20" />}
                                {item.rank === 3 && <Medal className="w-6 h-6 text-amber-700 fill-amber-700/20" />}
                            </div>

                            <div className="flex-1 min-w-0 pr-2">
                                <p className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider mb-0.5">
                                    {item.paddle.brand}
                                </p>
                                <p className="font-bold text-sm truncate group-hover:text-primary transition-colors">
                                    {item.paddle.name}
                                </p>
                            </div>

                            <div className="text-right flex items-center gap-3">
                                <div className="flex flex-col items-end">
                                    <span className={cn("text-lg font-black font-mono leading-none", colorClass)}>
                                        {item.value}
                                    </span>
                                    {item.unit && <span className="text-[10px] text-muted-foreground font-medium">{item.unit}</span>}
                                </div>
                                <ChevronRight className="w-4 h-4 text-muted-foreground/30 group-hover:text-primary transition-all opacity-0 group-hover:opacity-100 -ml-2 group-hover:ml-0" />
                            </div>
                        </div>
                    ))}
                </div>

                {/* Rest list (Accordion style or just list) */}
                {rest.length > 0 && (
                    <div className="bg-muted/10 border-t border-border/50">
                        {rest.map((item) => (
                            <div
                                key={item.paddle.id}
                                onClick={() => onPaddleClick?.(item.paddle)}
                                className="flex items-center gap-4 px-4 py-3 hover:bg-muted/50 transition-colors cursor-pointer border-b border-border/30 last:border-0 group"
                                title={`${item.paddle.brand} ${item.paddle.name}`}
                            >
                                <div className="flex-shrink-0 w-8 flex justify-center text-xs font-bold text-muted-foreground/70 font-mono">
                                    {item.rank}
                                </div>
                                <div className="flex-1 min-w-0 flex items-baseline gap-2">
                                    <span className="text-xs font-medium truncate group-hover:text-primary transition-colors">{item.paddle.name}</span>
                                </div>
                                <div className="text-right whitespace-nowrap flex items-center gap-2">
                                    <span className="text-xs font-bold font-mono">{item.value}</span>
                                    {/* Chevron only on hover for compact list too? Maybe just for top 3 to keep it clean, or consistent. Let's do consistent but smaller. */}
                                    <ChevronRight className="w-3 h-3 text-muted-foreground/30 group-hover:text-primary transition-all opacity-0 group-hover:opacity-100" />
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

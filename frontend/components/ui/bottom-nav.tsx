"use client";

import Link from 'next/link';
import { Home, Heart, BarChart2 } from 'lucide-react';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';

export function BottomNav() {
    const pathname = usePathname();

    return (
        <nav className="fixed bottom-0 left-0 right-0 z-50 border-t bg-background/80 backdrop-blur-md pb-[env(safe-area-inset-bottom)]">
            <div className="flex items-center justify-around h-16">
                <NavItem href="/" icon={Home} label="Home" active={pathname === '/'} />
                <NavItem href="/statistics" icon={BarChart2} label="Análise" active={pathname === '/statistics'} />
                <NavItem href="/favorites" icon={Heart} label="Favoritos" active={pathname === '/favorites'} />
            </div>
        </nav>
    );
}

function NavItem({ href, icon: Icon, label, active }: { href: string; icon: any; label: string; active: boolean }) {
    return (
        <Link href={href} className={cn("flex flex-col items-center justify-center w-full h-full space-y-1 transition-colors", active ? "text-primary-text" : "text-muted-foreground hover:text-primary-text/80")}>
            <Icon className="w-6 h-6" />
            <span className="text-xs font-medium">{label}</span>
        </Link>
    );
}

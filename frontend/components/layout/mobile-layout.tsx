import React from 'react';
import { BottomNav } from '@/components/ui/bottom-nav';

interface MobileLayoutProps {
    children: React.ReactNode;
}

export function MobileLayout({ children }: MobileLayoutProps) {
    return (
        <div className="flex flex-col min-h-screen bg-background font-sans antialiased">
            <main className="flex-1 pb-32 px-4 pt-4 ios-safe-padding"> {/* Increased padding for BottomNav + Safe Area */}
                {children}
            </main>
            <BottomNav />
        </div>
    );
}

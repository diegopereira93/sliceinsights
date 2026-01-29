'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle, RefreshCcw } from 'lucide-react';

interface Props {
    children?: ReactNode;
    fallback?: ReactNode;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error('Uncaught error:', error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="flex min-h-[400px] flex-col items-center justify-center p-8 text-center bg-background rounded-3xl border-2 border-dashed border-muted">
                    <div className="p-4 bg-destructive/10 rounded-full mb-6">
                        <AlertCircle className="w-12 h-12 text-destructive" />
                    </div>
                    <h2 className="text-2xl font-black mb-2 uppercase italic tracking-tighter">
                        Oops! Algo deu errado
                    </h2>
                    <p className="text-muted-foreground max-w-md mb-8">
                        Tivemos um problema técnico ao carregar esta seção. Nosso time de robôs já foi notificado.
                    </p>
                    <Button
                        onClick={() => window.location.reload()}
                        className="bg-primary text-primary-foreground font-black px-8 py-6 rounded-full shadow-lg hover:scale-105 transition-transform"
                    >
                        <RefreshCcw className="w-5 h-5 mr-2" />
                        TENTAR NOVAMENTE
                    </Button>
                    {process.env.NODE_ENV === 'development' && (
                        <pre className="mt-8 p-4 bg-muted rounded-xl text-left text-[10px] overflow-auto max-w-full">
                            {this.state.error?.toString()}
                        </pre>
                    )}
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;

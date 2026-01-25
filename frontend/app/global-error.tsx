'use client'

import { AlertTriangle, RefreshCw } from 'lucide-react'

export default function GlobalError({
    error,
    reset,
}: {
    error: Error & { digest?: string }
    reset: () => void
}) {
    return (
        <html>
            <body>
                <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
                    <div className="text-center p-8 max-w-md">
                        <div className="mb-6 flex justify-center">
                            <div className="p-4 bg-red-500/20 rounded-full">
                                <AlertTriangle className="w-12 h-12 text-red-400" />
                            </div>
                        </div>

                        <h2 className="text-2xl font-bold text-white mb-4">
                            Erro Crítico
                        </h2>

                        <p className="text-slate-400 mb-6">
                            Ocorreu um erro grave na aplicação. Por favor, tente recarregar a página.
                        </p>

                        {error.digest && (
                            <p className="text-xs text-slate-500 mb-6 font-mono">
                                Código: {error.digest}
                            </p>
                        )}

                        <button
                            onClick={() => reset()}
                            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold rounded-xl hover:from-emerald-600 hover:to-teal-600 transition-all duration-200"
                        >
                            <RefreshCw className="w-4 h-4" />
                            Recarregar página
                        </button>
                    </div>
                </div>
            </body>
        </html>
    )
}

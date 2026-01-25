import Link from 'next/link'
import { FileQuestion, Home, Search } from 'lucide-react'

export default function NotFound() {
    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
            <div className="text-center p-8 max-w-md">
                <div className="mb-6 flex justify-center">
                    <div className="p-4 bg-amber-500/20 rounded-full">
                        <FileQuestion className="w-12 h-12 text-amber-400" />
                    </div>
                </div>

                <h1 className="text-6xl font-bold text-white mb-4">404</h1>

                <h2 className="text-xl font-semibold text-slate-300 mb-4">
                    Página não encontrada
                </h2>

                <p className="text-slate-400 mb-8">
                    A página que você está procurando não existe ou foi movida.
                </p>

                <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <Link
                        href="/"
                        className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold rounded-xl hover:from-emerald-600 hover:to-teal-600 transition-all duration-200 shadow-lg shadow-emerald-500/25"
                    >
                        <Home className="w-4 h-4" />
                        Ir para o início
                    </Link>

                    <Link
                        href="/statistics"
                        className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-slate-600 text-slate-300 font-semibold rounded-xl hover:bg-slate-800 transition-all duration-200"
                    >
                        <Search className="w-4 h-4" />
                        Ver estatísticas
                    </Link>
                </div>
            </div>
        </div>
    )
}

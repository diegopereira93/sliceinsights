import { WifiOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function OfflinePage() {
    return (
        <div className="flex flex-col items-center justify-center min-h-[80vh] p-4 text-center">
            <div className="bg-muted/30 p-6 rounded-full mb-6">
                <WifiOff className="w-12 h-12 text-muted-foreground" />
            </div>
            <h1 className="text-2xl font-bold mb-2">Você está offline</h1>
            <p className="text-muted-foreground mb-8 max-w-sm">
                Verifique sua conexão com a internet para acessar todo o conteúdo do SliceInsights.
            </p>
            <Button asChild>
                <Link href="/">Tentar Novamente</Link>
            </Button>
        </div>
    );
}

"use client";

import { useState } from "react";
import { Bell, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { subscribeToAlert } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";

interface PriceAlertDialogProps {
    paddleId: string;
    currentPrice: number;
}

export function PriceAlertDialog({ paddleId, currentPrice }: PriceAlertDialogProps) {
    const [open, setOpen] = useState(false);
    const [email, setEmail] = useState("");
    const [loading, setLoading] = useState(false);
    const { toast } = useToast();

    const handleSubscribe = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!email) return;

        setLoading(true);
        try {
            // Set target price to 5% below current price by default logic, or just current price to catch any drop
            // For MVP we just pass current price as the reference
            await subscribeToAlert(paddleId, email, currentPrice);

            toast({
                title: "Alerta criado!",
                description: "Você será avisado quando o preço baixar.",
                variant: "default", // Success
            });
            setOpen(false);
            setEmail("");
        } catch (error) {
            toast({
                title: "Erro ao criar alerta",
                description: "Tente novamente mais tarde.",
                variant: "destructive",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline" size="sm" className="gap-2 w-full sm:w-auto">
                    <Bell className="w-4 h-4" />
                    Avise-me quando baixar
                </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Monitorar Preço</DialogTitle>
                    <DialogDescription>
                        Receba um email quando o preço deste produto cair.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubscribe} className="grid gap-4 py-4">
                    <div className="grid gap-2">
                        <Label htmlFor="email">Seu email</Label>
                        <Input
                            id="email"
                            type="email"
                            placeholder="exemplo@email.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>
                    <DialogFooter>
                        <Button type="submit" disabled={loading}>
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Criar Alerta
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}

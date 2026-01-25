"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Calculator, DollarSign, Package, TrendingUp, Plane, Receipt, AlertCircle } from "lucide-react";
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import {
    calculateImportCosts,
    formatBRL,
    getExchangeRate,
    isImportWorthIt,
    type ImportCalculatorInput,
    type ImportCostBreakdown,
} from "@/lib/import-utils";

interface ImportCalculatorProps {
    /** Pre-fill with paddle price (optional) */
    initialPrice?: number;
    /** Pre-fill currency (optional) */
    initialCurrency?: "USD" | "EUR";
    /** Paddle weight in grams (optional) */
    paddleWeight?: number;
    /** Local price for comparison (optional) */
    localPriceBRL?: number;
    /** Trigger button variant */
    variant?: "default" | "outline" | "ghost";
    /** Trigger button size */
    size?: "default" | "sm" | "lg" | "icon";
}

export function ImportCalculator({
    initialPrice,
    initialCurrency = "USD",
    paddleWeight = 350,
    localPriceBRL,
    variant = "outline",
    size = "sm",
}: ImportCalculatorProps) {
    const [open, setOpen] = useState(false);
    const [price, setPrice] = useState<string>(initialPrice?.toString() || "");
    const [currency, setCurrency] = useState<"USD" | "EUR">(initialCurrency);
    const [origin, setOrigin] = useState<"USA" | "EUROPE" | "ASIA">("USA");

    const result = useMemo<ImportCostBreakdown | null>(() => {
        const priceNum = parseFloat(price);
        if (isNaN(priceNum) || priceNum <= 0) return null;

        const input: ImportCalculatorInput = {
            price: priceNum,
            currency,
            weightGrams: paddleWeight,
            origin,
        };

        return calculateImportCosts(input);
    }, [price, currency, origin, paddleWeight]);

    const comparison = useMemo(() => {
        if (!result || !localPriceBRL) return null;
        return isImportWorthIt(result.totalBRL, localPriceBRL);
    }, [result, localPriceBRL]);

    return (
        <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild>
                <Button variant={variant} size={size} className="gap-2">
                    <Calculator className="w-4 h-4" />
                    <span className="hidden sm:inline">Calcular Importação</span>
                </Button>
            </SheetTrigger>
            <SheetContent className="w-full sm:max-w-md overflow-y-auto">
                <SheetHeader>
                    <SheetTitle className="flex items-center gap-2">
                        <Calculator className="w-5 h-5 text-primary" />
                        Calculadora de Importação
                    </SheetTitle>
                    <SheetDescription>
                        Estime o custo total para importar uma raquete para o Brasil.
                    </SheetDescription>
                </SheetHeader>

                <div className="mt-6 space-y-6">
                    {/* Input Section */}
                    <div className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <Label htmlFor="price">Preço do Produto</Label>
                                <div className="relative">
                                    <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                    <Input
                                        id="price"
                                        type="number"
                                        placeholder="149.00"
                                        value={price}
                                        onChange={(e) => setPrice(e.target.value)}
                                        className="pl-9"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="currency">Moeda</Label>
                                <Select value={currency} onValueChange={(v) => setCurrency(v as "USD" | "EUR")}>
                                    <SelectTrigger id="currency">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="USD">USD (Dólar)</SelectItem>
                                        <SelectItem value="EUR">EUR (Euro)</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="origin" className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Origem do Produto</Label>
                            <Select value={origin} onValueChange={(v) => setOrigin(v as "USA" | "EUROPE" | "ASIA")}>
                                <SelectTrigger id="origin" className="bg-background/50 backdrop-blur-sm border-white/10 h-11">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent className="glass-dark border-white/10">
                                    <SelectItem value="USA">🇺🇸 Estados Unidos</SelectItem>
                                    <SelectItem value="EUROPE">🇪🇺 Europa</SelectItem>
                                    <SelectItem value="ASIA">🌏 Ásia</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Exchange Rate & Confidence Info */}
                        <div className="flex items-center justify-between">
                            <p className="text-[10px] text-muted-foreground font-medium uppercase tracking-tighter">
                                Cotação: 1 {currency} = {formatBRL(getExchangeRate(currency))}
                            </p>
                            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                                <span className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                                <span className="text-[9px] text-emerald-500 font-bold uppercase tracking-widest">Cálculo Verificado (2025)</span>
                            </div>
                        </div>
                    </div>

                    {/* Results Section */}
                    <AnimatePresence mode="wait">
                        {result && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                className="space-y-4"
                            >
                                {/* Cost Breakdown */}
                                <div className="bg-muted/50 rounded-xl p-4 space-y-3">
                                    <h4 className="font-semibold text-sm flex items-center gap-2">
                                        <Receipt className="w-4 h-4" />
                                        Detalhamento de Custos
                                    </h4>

                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground flex items-center gap-2">
                                                <Package className="w-3 h-3" />
                                                Produto ({result.currency} {result.productPrice})
                                            </span>
                                            <span>{formatBRL(result.productPriceBRL)}</span>
                                        </div>

                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground flex items-center gap-2">
                                                <Plane className="w-3 h-3" />
                                                Frete Estimado
                                            </span>
                                            <span>{formatBRL(result.shippingBRL)}</span>
                                        </div>

                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">
                                                Imposto de Importação (20%)
                                            </span>
                                            <span>{formatBRL(result.importTaxBRL)}</span>
                                        </div>

                                        <div className="flex justify-between">
                                            <span className="text-muted-foreground">
                                                ICMS (~17%)
                                            </span>
                                            <span>{formatBRL(result.icmsBRL)}</span>
                                        </div>

                                        <div className="border-t border-border pt-2 flex justify-between font-bold">
                                            <span>Total Estimado</span>
                                            <span className="text-primary text-lg">{formatBRL(result.totalBRL)}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Comparison (if local price available) */}
                                {comparison && (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        className={`rounded-xl p-4 ${comparison.worthIt
                                            ? "bg-emerald-500/10 border border-emerald-500/30"
                                            : "bg-amber-500/10 border border-amber-500/30"
                                            }`}
                                    >
                                        <div className="flex items-center gap-2">
                                            <TrendingUp
                                                className={`w-5 h-5 ${comparison.worthIt ? "text-emerald-500" : "text-amber-500"
                                                    }`}
                                            />
                                            <div>
                                                <p className="font-semibold text-sm">
                                                    {comparison.worthIt
                                                        ? "Vale a pena importar!"
                                                        : "Considere comprar localmente"}
                                                </p>
                                                <p className="text-xs text-muted-foreground">
                                                    {comparison.worthIt
                                                        ? `Economia de ${comparison.savingsPercent}% (${formatBRL(comparison.savingsBRL)})`
                                                        : `Diferença de apenas ${Math.abs(comparison.savingsPercent)}%`}
                                                </p>
                                            </div>
                                        </div>
                                    </motion.div>
                                )}

                                {/* Disclaimer */}
                                <div className="flex gap-2 text-xs text-muted-foreground">
                                    <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                                    <p>
                                        Valores estimados. Custos reais podem variar de acordo com taxas aduaneiras,
                                        câmbio no dia da compra e modalidade de frete escolhida.
                                    </p>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </SheetContent>
        </Sheet>
    );
}

export default ImportCalculator;

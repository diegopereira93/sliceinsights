import * as React from "react";
import { Filter, Search, Check, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Drawer,
    DrawerClose,
    DrawerContent,
    DrawerDescription,
    DrawerFooter,
    DrawerHeader,
    DrawerTitle,
    DrawerTrigger,
} from "@/components/ui/drawer";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";

interface FilterDrawerProps {
    brands: string[];
    selectedBrands: string[];
    onToggleBrand: (brand: string) => void;
    priceRange: [number, number];
    onPriceRangeChange: (range: [number, number]) => void;
    weightFilter?: "all" | "light" | "standard" | "heavy";
    onWeightChange?: (weight: "all" | "light" | "standard" | "heavy") => void;
    thicknessFilter: "all" | "14mm" | "16mm";
    onThicknessChange: (thickness: "all" | "14mm" | "16mm") => void;
    onClear: () => void;
    surfaceMaterialFilter?: "all" | "Carbon" | "Fiberglass";
    onSurfaceMaterialChange?: (v: "all" | "Carbon" | "Fiberglass") => void;
}

export function FilterDrawer({
    brands, selectedBrands, onToggleBrand,
    priceRange, onPriceRangeChange,
    weightFilter = "all", onWeightChange,
    thicknessFilter, onThicknessChange,
    onClear,
    surfaceMaterialFilter = "all", onSurfaceMaterialChange,
}: FilterDrawerProps) {
    const [brandSearch, setBrandSearch] = React.useState("");

    const filteredBrands = React.useMemo(() => {
        if (!Array.isArray(brands)) return [];
        return brands.filter(b => {
            if (typeof b !== 'string') return false;
            return b.toLowerCase().includes(brandSearch.toLowerCase());
        });
    }, [brands, brandSearch]);

    // Count active filters (price is active if min > 0 or max < 4000)
    const priceActive = priceRange[0] > 0 || priceRange[1] < 4000 ? 1 : 0;
    const weightActive = (weightFilter ?? "all") !== "all" ? 1 : 0;
    const thicknessActive = thicknessFilter !== "all" ? 1 : 0;
    const surfaceMaterialActive = surfaceMaterialFilter !== "all" ? 1 : 0;
    const totalActiveFilters = selectedBrands.length + priceActive + weightActive + thicknessActive + surfaceMaterialActive;

    return (
        <Drawer>
            <DrawerTrigger asChild>
                <Button variant="outline" size="sm" className="rounded-full gap-2 transition-all">
                    <Filter className="w-4 h-4" />
                    Filtros
                    {totalActiveFilters > 0 && (
                        <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 flex items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
                            {totalActiveFilters}
                        </Badge>
                    )}
                </Button>
            </DrawerTrigger>
            <DrawerContent>
                <div className="mx-auto w-full max-w-md max-h-[90vh] flex flex-col">
                    <DrawerHeader className="border-b border-white/5 shrink-0">
                        <DrawerTitle className="text-xl font-black italic uppercase tracking-tighter">Filtros Refinados</DrawerTitle>
                        <DrawerDescription>Ajuste as características para encontrar sua raquete perfeita.</DrawerDescription>
                    </DrawerHeader>

                    <div className="p-4 space-y-6 overflow-y-auto flex-1 custom-scrollbar">
                        {/* BRANDS: COMBOBOX / SEARCHABLE LIST */}
                        <div>
                            <div className="flex justify-between items-center mb-3">
                                <h4 className="text-sm font-bold text-white uppercase tracking-wider">Marcas</h4>
                                {selectedBrands.length > 0 && (
                                    <span className="text-xs text-primary font-bold">{selectedBrands.length} selecionadas</span>
                                )}
                            </div>

                            <div className="relative mb-3">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                                <Input
                                    placeholder="Buscar marca..."
                                    className="pl-9 bg-muted/30 border-white/5 h-9"
                                    value={brandSearch}
                                    onChange={(e) => setBrandSearch(e.target.value)}
                                />
                                {brandSearch && (
                                    <button onClick={() => setBrandSearch("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-white">
                                        <X className="w-3 h-3" />
                                    </button>
                                )}
                            </div>

                            <div className="h-40 border border-white/5 rounded-md bg-muted/10 overflow-hidden flex flex-col">
                                {filteredBrands.length === 0 ? (
                                    <div className="flex-1 flex items-center justify-center text-xs text-muted-foreground p-4 text-center">
                                        Nenhuma marca encontrada
                                    </div>
                                ) : (
                                    <div className="flex-1 overflow-y-auto p-1 custom-scrollbar">
                                        {filteredBrands.map((brand) => {
                                            const isSelected = selectedBrands.includes(brand);
                                            return (
                                                <div
                                                    key={brand}
                                                    onClick={() => onToggleBrand(brand)}
                                                    className={cn(
                                                        "flex items-center justify-between px-3 py-2 cursor-pointer rounded-sm text-sm transition-colors",
                                                        isSelected ? "bg-primary/20 text-white font-bold" : "hover:bg-white/5 text-zinc-400 hover:text-white"
                                                    )}
                                                >
                                                    {brand}
                                                    {isSelected && <Check className="w-4 h-4 text-primary" />}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        </div>

                        <Separator className="bg-white/5" />

                        {/* PREÇO: REAL SLIDER */}
                        <div>
                            <div className="flex justify-between items-center mb-4">
                                <h4 className="text-sm font-bold text-white uppercase tracking-wider">Preço (R$)</h4>
                                <span className="text-xs font-mono text-zinc-400 bg-muted px-2 py-0.5 rounded-sm">
                                    {(priceRange[1] === 4000) ? `Até R$ 4000+` : `R$ ${priceRange[0]} - R$ ${priceRange[1]}`}
                                </span>
                            </div>
                            <div className="px-2">
                                <Slider
                                    defaultValue={[0, 4000]}
                                    value={priceRange}
                                    max={4000}
                                    step={50}
                                    className="w-full"
                                    onValueChange={(vals) => onPriceRangeChange(vals as [number, number])}
                                />
                                <div className="flex justify-between text-[10px] text-muted-foreground mt-2 px-1">
                                    <span>R$ 0</span>
                                    <span>R$ 4.000+</span>
                                </div>
                            </div>
                        </div>

                        <Separator className="bg-white/5" />

                        {/* WEIGHT (PESO) — only shown when onWeightChange is provided */}
                        {onWeightChange && (
                            <div>
                                <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Peso Nominal</h4>
                                <div className="flex gap-2">
                                    {[
                                        { value: "all", label: "Qualquer" },
                                        { value: "light", label: "Leve (<7.8 oz)" },
                                        { value: "standard", label: "Padrão" },
                                        { value: "heavy", label: "Pesada (>8.2 oz)" }
                                    ].map(option => (
                                        <Badge
                                            key={option.value}
                                            variant={weightFilter === option.value ? "default" : "outline"}
                                            className={cn(
                                                "cursor-pointer font-bold px-3 py-1.5",
                                                weightFilter !== option.value && "border-white/10 text-zinc-400 hover:text-white"
                                            )}
                                            onClick={() => onWeightChange(option.value as any)}
                                        >
                                            {option.label}
                                        </Badge>
                                    ))}
                                </div>
                            </div>
                        )}

                        <Separator className="bg-white/5" />

                        {/* Espessura (Thickness) */}
                        <div>
                            <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Espessura (Core)</h4>
                            <div className="flex gap-2">
                                {[
                                    { value: "all", label: "Qualquer" },
                                    { value: "14mm", label: "14mm (Potência)" },
                                    { value: "16mm", label: "16mm (Controle)" }
                                ].map(option => (
                                    <Badge
                                        key={option.value}
                                        variant={thicknessFilter === option.value ? "default" : "outline"}
                                        className={cn(
                                            "cursor-pointer font-bold px-3 py-1.5",
                                            thicknessFilter !== option.value && "border-white/10 text-zinc-400 hover:text-white"
                                        )}
                                        onClick={() => onThicknessChange(option.value as any)}
                                    >
                                        {option.label}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        {/* Surface Material Filter — only shown when onSurfaceMaterialChange is provided */}
                        {onSurfaceMaterialChange && (
                            <>
                                <Separator className="bg-white/5" />
                                <div>
                                    <h4 className="text-sm font-bold text-white uppercase tracking-wider mb-3">Material da Face</h4>
                                    <div className="flex gap-2">
                                        {[
                                            { value: "all", label: "Todos" },
                                            { value: "Carbon", label: "Carbon" },
                                            { value: "Fiberglass", label: "Fiberglass" }
                                        ].map(option => (
                                            <Badge
                                                key={option.value}
                                                variant={surfaceMaterialFilter === option.value ? "default" : "outline"}
                                                className={cn(
                                                    "cursor-pointer font-bold px-3 py-1.5",
                                                    surfaceMaterialFilter !== option.value && "border-white/10 text-zinc-400 hover:text-white"
                                                )}
                                                onClick={() => onSurfaceMaterialChange(option.value as any)}
                                            >
                                                {option.label}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}

                    </div>

                    <DrawerFooter className="border-t border-white/5 shrink-0 bg-background/50 backdrop-blur-md">
                        <DrawerClose asChild>
                            <Button className="w-full h-14 text-base font-black rounded-xl">Aplicar {totalActiveFilters > 0 ? `(${totalActiveFilters})` : ''} Filtros</Button>
                        </DrawerClose>
                        {totalActiveFilters > 0 && (
                            <Button variant="ghost" onClick={onClear} className="text-muted-foreground hover:text-white">
                                <X className="w-4 h-4 mr-2" /> Limpar Filtros
                            </Button>
                        )}
                    </DrawerFooter>
                </div>
            </DrawerContent>
        </Drawer>
    );
}

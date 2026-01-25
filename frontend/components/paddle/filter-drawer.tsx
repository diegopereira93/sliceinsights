import * as React from "react";
import { Filter } from "lucide-react";
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

interface FilterDrawerProps {
    brands: string[];
    selectedBrands: string[];
    onToggleBrand: (brand: string) => void;
    onClear: () => void;
}

export function FilterDrawer({ brands, selectedBrands, onToggleBrand, onClear }: FilterDrawerProps) {

    return (
        <Drawer>
            <DrawerTrigger asChild>
                <Button variant="outline" size="sm" className="rounded-full gap-2">
                    <Filter className="w-4 h-4" />
                    Filtros
                    {selectedBrands.length > 0 && (
                        <Badge variant="secondary" className="ml-1 h-5 w-5 p-0 flex items-center justify-center rounded-full">
                            {selectedBrands.length}
                        </Badge>
                    )}
                </Button>
            </DrawerTrigger>
            <DrawerContent>
                <div className="mx-auto w-full max-w-sm">
                    <DrawerHeader>
                        <DrawerTitle>Filtros</DrawerTitle>
                        <DrawerDescription>Selecione as opções para filtrar as raquetes.</DrawerDescription>
                    </DrawerHeader>

                    <div className="p-4 space-y-6">
                        <div>
                            <h4 className="text-sm font-medium mb-3">Marcas</h4>
                            <div className="flex flex-wrap gap-2">
                                {brands.map((brand) => (
                                    <Badge
                                        key={brand}
                                        variant={selectedBrands.includes(brand) ? "default" : "outline"}
                                        className="cursor-pointer py-1.5 px-3 text-sm transition-colors"
                                        onClick={() => onToggleBrand(brand)}
                                    >
                                        {brand}
                                    </Badge>
                                ))}
                            </div>
                        </div>

                        <Separator />

                        <div>
                            <h4 className="text-sm font-medium mb-3">Preço</h4>
                            <div className="flex items-center justify-between text-sm text-muted-foreground">
                                <span>R$ 500</span>
                                <span>R$ 2500+</span>
                            </div>
                            <div className="h-1.5 w-full bg-secondary rounded-full mt-4 overflow-hidden">
                                <div className="h-full w-2/3 bg-primary-text rounded-full" />
                            </div>
                        </div>
                    </div>

                    <DrawerFooter>
                        <DrawerClose asChild>
                            <Button className="w-full py-6 text-lg font-bold">Ver Resultados</Button>
                        </DrawerClose>
                        <Button variant="ghost" onClick={onClear}>Limpar Tudo</Button>
                    </DrawerFooter>
                </div>
            </DrawerContent>
        </Drawer>
    );
}

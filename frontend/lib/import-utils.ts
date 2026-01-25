/**
 * Import Calculator Utilities
 * 
 * Calculates estimated import costs for international pickleball paddles.
 * Based on Brazilian import regulations and typical shipping costs.
 */

export interface ImportCostBreakdown {
    /** Original product price in source currency */
    productPrice: number;
    /** Product price converted to BRL */
    productPriceBRL: number;
    /** Estimated shipping cost in BRL */
    shippingBRL: number;
    /** Import tax (Imposto de Importação) in BRL */
    importTaxBRL: number;
    /** ICMS tax in BRL */
    icmsBRL: number;
    /** Total estimated cost in BRL */
    totalBRL: number;
    /** Currency used for product price */
    currency: 'USD' | 'EUR' | 'BRL';
}

export interface ImportCalculatorInput {
    /** Product price in original currency */
    price: number;
    /** Currency of the product price */
    currency: 'USD' | 'EUR' | 'BRL';
    /** Product weight in grams (for shipping calculation) */
    weightGrams?: number;
    /** Origin country (affects shipping) */
    origin?: 'USA' | 'EUROPE' | 'ASIA' | 'OTHER';
}

// Exchange rates (should be updated periodically or fetched from API)
const EXCHANGE_RATES: Record<string, number> = {
    USD: 5.05,  // USD to BRL
    EUR: 5.50,  // EUR to BRL
    BRL: 1.0,
};

// Tax rates (Brazilian Federal Regulations)
const TAX_RATES = {
    IMPORT_TAX: 0.20,      // 20% Imposto de Importação (for goods over $50)
    ICMS: 0.17,            // 17% ICMS (varies by state, using SP average)
    DE_MINIMIS_USD: 50,    // Valor mínimo para isenção
};

// Shipping cost estimates by origin (in BRL)
const SHIPPING_COSTS: Record<string, number> = {
    USA: 180,      // USA to Brazil (typical USPS/FedEx)
    EUROPE: 220,   // Europe to Brazil
    ASIA: 150,     // Asia to Brazil (usually longer)
    OTHER: 200,    // Default
};

// Weight-based shipping adjustment (per 100g over 500g base)
const WEIGHT_ADJUSTMENT_PER_100G = 15;
const BASE_WEIGHT_GRAMS = 500;

/**
 * Calculate estimated import costs for a pickleball paddle.
 * 
 * @param input - Calculator input with price, currency, and optional weight/origin
 * @returns Breakdown of all costs in BRL
 */
export function calculateImportCosts(input: ImportCalculatorInput): ImportCostBreakdown {
    const { price, currency, weightGrams = 350, origin = 'USA' } = input;

    // Convert product price to BRL
    const exchangeRate = EXCHANGE_RATES[currency] || EXCHANGE_RATES.USD;
    const productPriceBRL = price * exchangeRate;

    // Calculate shipping based on origin and weight
    let shippingBRL = SHIPPING_COSTS[origin] || SHIPPING_COSTS.OTHER;

    // Adjust shipping for heavier paddles
    if (weightGrams > BASE_WEIGHT_GRAMS) {
        const extraWeight = Math.ceil((weightGrams - BASE_WEIGHT_GRAMS) / 100);
        shippingBRL += extraWeight * WEIGHT_ADJUSTMENT_PER_100G;
    }

    // Calculate taxable value (product + shipping)
    const taxableValue = productPriceBRL + shippingBRL;

    // Import tax (only if over de minimis threshold)
    const priceInUSD = currency === 'USD' ? price : productPriceBRL / EXCHANGE_RATES.USD;
    let importTaxBRL = 0;
    if (priceInUSD > TAX_RATES.DE_MINIMIS_USD) {
        importTaxBRL = taxableValue * TAX_RATES.IMPORT_TAX;
    }

    // ICMS (applied on total including import tax)
    // ICMS is calculated "por dentro", but simplified here
    const icmsBRL = (taxableValue + importTaxBRL) * TAX_RATES.ICMS;

    // Total
    const totalBRL = productPriceBRL + shippingBRL + importTaxBRL + icmsBRL;

    return {
        productPrice: price,
        productPriceBRL: Math.round(productPriceBRL * 100) / 100,
        shippingBRL: Math.round(shippingBRL * 100) / 100,
        importTaxBRL: Math.round(importTaxBRL * 100) / 100,
        icmsBRL: Math.round(icmsBRL * 100) / 100,
        totalBRL: Math.round(totalBRL * 100) / 100,
        currency,
    };
}

/**
 * Format currency value in Brazilian Real.
 */
export function formatBRL(value: number): string {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
    }).format(value);
}

/**
 * Get current exchange rate for display.
 */
export function getExchangeRate(currency: 'USD' | 'EUR'): number {
    return EXCHANGE_RATES[currency];
}

/**
 * Estimate if importing is worth it compared to local price.
 */
export function isImportWorthIt(importTotal: number, localPriceBRL: number): {
    worthIt: boolean;
    savingsPercent: number;
    savingsBRL: number;
} {
    const savingsBRL = localPriceBRL - importTotal;
    const savingsPercent = (savingsBRL / localPriceBRL) * 100;

    return {
        worthIt: savingsPercent > 10, // Worth if savings > 10%
        savingsPercent: Math.round(savingsPercent * 10) / 10,
        savingsBRL: Math.round(savingsBRL * 100) / 100,
    };
}

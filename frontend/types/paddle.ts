export interface Paddle {
    id: string;
    name: string;
    brand: string;
    price: number;
    image: string;
    rating: number; 
    weight: string;
    surfaceMaterial: string;
    powerLevel: 'High' | 'Medium' | 'Low';
    controlLevel: 'High' | 'Medium' | 'Low';
    power: number;      // 0-10
    control: number;    // 0-10
    spin: number;       // 0-10
    sweetSpot: number;  // 0-10
    matchReasons?: string[];
    tags?: string[];
    availableInBrazil?: boolean;
    affiliateUrl?: string;

    // Detailed Specs
    swingWeight?: number;
    twistWeight?: number;
    spinRPM?: number;
    powerOriginal?: number;
    coreThicknessmm?: number;
    handleLength?: string;
    gripCircumference?: string;
    coreMaterial?: string;
    faceMaterial?: string; 

    // Data Transparency
    isSynthetic?: boolean;
    dataQuality?: 'Verified' | 'Estimated';
}

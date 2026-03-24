export interface Paddle {
  id: number;
  name: string;
  brand: string;
  price: number;
  imageUrl?: string;
  coreThickness?: number;
  surface?: string;
  handle?: string;
  swingWeight?: number;
  powerScore: number;
  controlScore: number;
  weightSensation?: string;
  weightSensationDescription?: string;
  shopUrl?: string;
  isHiddenGem?: boolean;
  valueCostBenefit?: string;
}
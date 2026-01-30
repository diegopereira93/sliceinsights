import { HomeClient } from '@/components/home-client';
import { getPaddles, getBrands, mapBackendToFrontendPaddle } from '@/lib/api';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'SliceInsights - Encontre Sua Raquete Ideal',
  description: 'Use nossa análise de dados para descobrir a raquete perfeita para seu estilo de jogo. Insights precisos para sua melhor jogada.',
};

export const dynamic = 'force-dynamic'; // Ensure fresh data on each request

export default async function Home() {
  // Fetch data on the server
  let paddles = [];
  let brands: string[] = [];

  try {
    const [paddlesRes, brandsRes] = await Promise.all([
      getPaddles({ limit: 50, available_in_brazil: true }),
      getBrands()
    ]);

    if (paddlesRes && paddlesRes.data) {
      paddles = paddlesRes.data.map(mapBackendToFrontendPaddle);
    }

    if (brandsRes && brandsRes.data) {
      // Show only brands that actually have products in the catalog
      // or at least available locally
      brands = brandsRes.data.map((b: any) => b.name).sort();
    }
  } catch (error) {
    console.error('Failed to fetch initial data:', error);
  }

  return (
    <HomeClient
      initialPaddles={paddles}
      availableBrands={brands}
    />
  );
}

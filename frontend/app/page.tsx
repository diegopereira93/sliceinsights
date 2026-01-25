import { HomeClient } from '@/components/home-client';
import { getPaddles, mapBackendToFrontendPaddle } from '@/lib/api';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'SliceInsights - Encontre Sua Raquete Ideal',
  description: 'Use nossa análise de dados para descobrir a raquete perfeita para seu estilo de jogo. Insights precisos para sua melhor jogada.',
};

export const dynamic = 'force-dynamic'; // Ensure fresh data on each request

export default async function Home() {
  // Fetch data on the server
  let paddles = [];

  try {
    const paddlesRes = await getPaddles({ limit: 50, available_in_brazil: true });

    if (paddlesRes && paddlesRes.data) {
      paddles = paddlesRes.data.map(mapBackendToFrontendPaddle);
    }
  } catch (error) {
    console.error('Failed to fetch initial data:', error);
  }

  return (
    <HomeClient
      initialPaddles={paddles}
    />
  );
}

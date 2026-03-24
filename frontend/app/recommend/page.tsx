import { RecommendClient } from '@/components/recommend/recommend-client';
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Quiz Tecnico | SliceInsights',
  description: 'Encontre sua raquete ideal de pickleball com nosso assistente de IA personalizado',
};

export default function RecommendPage() {
  return <RecommendClient />;
}

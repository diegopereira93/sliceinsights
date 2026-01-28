
import { StatisticsClient } from '@/components/statistics-client';
import { getPaddles, mapBackendToFrontendPaddle } from '@/lib/api';
import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Análise de Raquetes | SliceInsights',
    description: 'Mergulhe nos dados. Compare preço, performance, controle e potência para encontrar a raquete matematicamente perfeita para você.',
};

export const dynamic = 'force-dynamic';

export default async function StatisticsPage() {
    let paddles = [];

    try {
        // Fetch a larger dataset for meaningful statistics
        // available_in_brazil=null/false to see the whole market for analysis
        const response = await getPaddles({ limit: 150 });
        if (response && response.data) {
            paddles = response.data.map(mapBackendToFrontendPaddle);
        }
    } catch (error) {
        console.error('Failed to fetch data for statistics:', error);
    }

    return (
        <div className="min-h-screen bg-background pb-20">
            <StatisticsClient initialPaddles={paddles} />
        </div>
    );
}

import HomeClient from '@/components/home-client';
import { getPaddles, getBrands, mapBackendToFrontendPaddle } from '@/lib/api';

export const revalidate = 3600; // Revalidate every hour

export default async function Home() {
    let paddles: ReturnType<typeof mapBackendToFrontendPaddle>[] = [];
    let brands: string[] = [];

    try {
        const [paddlesData, brandsData] = await Promise.all([
            getPaddles({ available_in_brazil: true }),
            getBrands({ available_in_brazil: true }),
        ]);

        paddles = paddlesData.data.map(mapBackendToFrontendPaddle);
        brands = (brandsData.data || []).map((b: any) =>
            typeof b === 'string' ? b : b.name
        );
    } catch (err) {
        console.error('[Home] Failed to fetch initial data:', err);
        // Renders with empty state — HomeClient handles the empty case gracefully
    }

    return (
        <HomeClient
            initialPaddles={paddles}
            brands={brands}
        />
    );
}

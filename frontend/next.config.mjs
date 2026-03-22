/** @type {import('next').NextConfig} */
const nextConfig = {
    // Enable standalone output for Docker production builds only
    ...(process.env.NODE_ENV === 'production' && { output: 'standalone' }),

    async redirects() {
        return [
            { source: '/catalog', destination: '/', permanent: true },
            { source: '/catalogo', destination: '/', permanent: true },
        ];
    },

    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: 'placehold.co',
            },
            {
                protocol: 'https',
                hostname: 'cdn.shopify.com',
            },
            {
                protocol: 'https',
                hostname: 'acdn-us.mitiendanube.com',
            },
            {
                protocol: 'https',
                hostname: 'www.joola.com.br',
            },
            {
                protocol: 'https',
                hostname: 'cdn.dooca.store',
            },
            {
                protocol: 'https',
                hostname: 'images.unsplash.com',
            }
        ],
    },
};

export default nextConfig;

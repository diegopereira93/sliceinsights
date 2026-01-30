import withPWA from 'next-pwa';

/** @type {import('next').NextConfig} */
const nextConfig = {
    // Enable standalone output for Docker multi-stage builds
    // output: 'standalone',

    async rewrites() {
        const backendUrl = process.env.BACKEND_URL || 'http://backend_v3:8000';
        return [
            {
                source: '/api/v1/:path*',
                destination: `${backendUrl}/api/v1/:path*`,
            },
        ];
    },

    // Cache headers for static assets
    async headers() {
        return [
            {
                source: '/:all*(svg|jpg|jpeg|png|gif|ico|webp)',
                headers: [
                    {
                        key: 'Cache-Control',
                        value: 'public, max-age=31536000, immutable',
                    },
                ],
            },
            {
                source: '/_next/static/:path*',
                headers: [
                    {
                        key: 'Cache-Control',
                        value: 'public, max-age=31536000, immutable',
                    },
                ],
            },
            // API response caching for CDN
            {
                source: '/api/v1/paddles',
                headers: [
                    {
                        key: 'Cache-Control',
                        value: 's-maxage=60, stale-while-revalidate=300',
                    },
                ],
            },
            {
                source: '/api/v1/brands',
                headers: [
                    {
                        key: 'Cache-Control',
                        value: 's-maxage=300, stale-while-revalidate=600',
                    },
                ],
            },
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
                hostname: 'images.unsplash.com',
                port: '',
                pathname: '/**',
            },
            {
                protocol: 'https',
                hostname: 'acdn-us.mitiendanube.com',  // Brazil Pickleball Store CDN
                port: '',
                pathname: '/stores/002/859/813/products/**',
            },
            {
                protocol: 'https',
                hostname: 'www.joola.com.br',  // Joola Brazil CDN
                port: '',
                pathname: '/cdn/shop/**',
            },
        ],
    },
};

export default withPWA({
    dest: 'public',
    disable: process.env.NODE_ENV === 'development',
    register: true,
    skipWaiting: true,
})(nextConfig);

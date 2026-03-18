/** @type {import('next').NextConfig} */
const nextConfig = {
    // Enable standalone output for Docker production builds only
    ...(process.env.NODE_ENV === 'production' && { output: 'standalone' }),

    images: {
        remotePatterns: [
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
            }
        ],
    },
};

export default nextConfig;

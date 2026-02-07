/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      bodySizeLimit: '5mb',
    },
  },
  // Supabase auth requires strict mode to be off for SSR
  reactStrictMode: false,
};

module.exports = nextConfig;

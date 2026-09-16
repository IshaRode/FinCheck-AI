import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/ask/:path*',
        destination: 'http://localhost:8000/api/ask/:path*',
      },
      {
        source: '/api/health',
        destination: 'http://localhost:8000/api/health',
      },
    ];
  },
};

export default nextConfig;

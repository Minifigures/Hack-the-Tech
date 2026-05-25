/** @type {import('next').NextConfig} */

// On Vercel, all `/api/*` traffic is handled by the Python serverless function
// (see vercel.json). Locally, proxy to the FastAPI dev server on :8000.
const backend = process.env.BACKEND_URL;
const onVercel = !!process.env.VERCEL;

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    if (onVercel) return [];
    const target = backend ?? "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${target}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;

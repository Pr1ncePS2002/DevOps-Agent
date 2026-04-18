/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Workaround: Next.js 14.2.x does not apply the default generateBuildId in all paths
  generateBuildId: async () => null,
  ...(process.env.NEXT_OUTPUT === "standalone" ? { output: "standalone" } : {}),
  experimental: {
    typedRoutes: true
  }
};

export default nextConfig;

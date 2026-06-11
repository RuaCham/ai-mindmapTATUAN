/** @type {import('next').NextConfig} */
const nextConfig = {
  // Cho phép gọi API từ domain khác khi deploy
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/:path*`,
      },
    ];
  },
};
module.exports = nextConfig;

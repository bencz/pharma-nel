import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "pubchem.ncbi.nlm.nih.gov",
        pathname: "/rest/pug/**",
      },
    ],
  },
};

export default nextConfig;

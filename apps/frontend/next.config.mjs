/** @type {import('next').NextConfig} */
const nextConfig = {
  // Allow an isolated build output dir via env (e.g. a dev/QA type-check build) so a one-off
  // `next build` never clobbers the running dev server's shared `.next`. Unset => default `.next`,
  // so normal `npm run dev` / `npm run build` behaviour is unchanged.
  ...(process.env.NEXT_DIST_DIR ? { distDir: process.env.NEXT_DIST_DIR } : {}),
};

export default nextConfig;

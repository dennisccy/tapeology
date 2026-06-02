import type { Config } from "tailwindcss";

const config: Config = {
  // ./lib is scanned so the dynamic color classes returned as literal strings by
  // lib/format.ts (stateColor/stateBarColor/sideColor/impactColor) are emitted as base
  // utilities. Without it Tailwind's content scanner never sees them and the cockpit's
  // load-bearing color semantics (green=buy/+impact, red=sell/-impact, amber=absorption)
  // render colorless. See goal-i_will_be_rich-iter-3.
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: { extend: {} },
  plugins: [],
};

export default config;

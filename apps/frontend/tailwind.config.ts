import type { Config } from "tailwindcss";
import defaultTheme from "tailwindcss/defaultTheme";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", ...defaultTheme.fontFamily.sans],
        sans: ["IBM Plex Sans", ...defaultTheme.fontFamily.sans]
      },
      colors: {
        "surface-900": "#050912",
        "surface-800": "#0A1324",
        "surface-700": "#111d33",
        "accent-500": "#55d6ff",
        "accent-400": "#71f3d6",
        "accent-300": "#c8ff9c"
      },
      backgroundImage: {
        "grid-fade": "radial-gradient(circle at top, rgba(255,255,255,0.2), transparent 60%)"
      },
      boxShadow: {
        card: "0 20px 45px rgba(10, 19, 36, 0.45)"
      }
    }
  },
  plugins: []
};

export default config;

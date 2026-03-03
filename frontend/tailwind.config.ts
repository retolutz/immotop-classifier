import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Immotop Brand Colors (approximiert)
        immotop: {
          primary: "#0066CC",
          secondary: "#004D99",
          accent: "#00A3E0",
          success: "#28A745",
          warning: "#FFC107",
          danger: "#DC3545",
        },
      },
    },
  },
  plugins: [],
};

export default config;

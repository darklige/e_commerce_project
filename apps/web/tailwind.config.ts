import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        commerce: {
          ink: "#15171a",
          red: "#d71920",
          teal: "#007d78",
          gold: "#b7791f"
        }
      }
    }
  },
  plugins: []
};

export default config;


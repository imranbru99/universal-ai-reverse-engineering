import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ink: {
          950: "#12140f",
          900: "#1b1f17",
          700: "#3d4536",
          500: "#6b7460",
        },
        paper: {
          50: "#f7f5ef",
          100: "#efebe1",
          200: "#e2dbc9",
        },
        accent: {
          600: "#2f6f5e",
          700: "#245749",
        },
      },
      fontFamily: {
        display: ["\"Iowan Old Style\"", "Palatino", "Georgia", "serif"],
        sans: ["\"Segoe UI\"", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        mesh: "radial-gradient(circle at 10% 10%, #ffffffaa, transparent 40%), radial-gradient(circle at 90% 0%, #d9ebe4aa, transparent 35%), linear-gradient(160deg, #f7f5ef, #e8eee9)",
      },
    },
  },
  plugins: [],
};

export default config;

import { heroui } from "@heroui/theme";
import tailwindcssAnimate from "tailwindcss-animate";
import typography from "@tailwindcss/typography";

/** @type {import('tailwindcss').Config} */
const config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        inter: "var(--font-inter), sans-serif",
        sans: "var(--font-inter), system-ui, sans-serif", // Make Inter the default sans font
      },
      command: {
        bg: "#1E293B",
        text: "#F8FAFC",
        border: "#334155",
      },
      animation: {
        shine: "shine 5s linear infinite",
        orbit: "orbit calc(var(--duration)*1s) linear infinite",
        grid: "grid 15s linear infinite",
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "shiny-text": "shiny-text 8s infinite",
        "pulse-shadow": "pulseShadow 2s infinite ease-in-out",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
      keyframes: {
        shine: {
          "0%": { "background-position": "100%" },
          "100%": { "background-position": "-100%" },
        },
        pulseShadow: {
          "0%, 100%": {
            boxShadow: "0px 0px 170px #00bbff",
          },
          "50%": {
            boxShadow: "0px 0px 50px #00bbff10",
          },
        },
        orbit: {
          "0%": {
            transform:
              "rotate(0deg) translateY(calc(var(--radius) * 1px)) rotate(0deg)",
          },
          "100%": {
            transform:
              "rotate(360deg) translateY(calc(var(--radius) * 1px)) rotate(-360deg)",
          },
        },
        grid: {
          "0%": {
            transform: "translateY(-50%)",
          },
          "100%": {
            transform: "translateY(0)",
          },
        },
        "accordion-down": {
          from: {
            height: "0",
          },
          to: {
            height: "var(--radix-accordion-content-height)",
          },
        },
        "accordion-up": {
          from: {
            height: "var(--radix-accordion-content-height)",
          },
          to: {
            height: "0",
          },
        },
        "shiny-text": {
          "0%, 90%, 100%": {
            "background-position": "calc(-100% - var(--shiny-width)) 0",
          },
          "30%, 60%": {
            "background-position": "calc(100% + var(--shiny-width)) 0",
          },
        },
        shine: {
          "0%": {
            "background-position": "0% 0%",
          },
          "50%": {
            "background-position": "100% 100%",
          },
          to: {
            "background-position": "0% 0%",
          },
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      colors: {
        sidebar: {
          DEFAULT: "hsl(var(--sidebar-background))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
    },
  },
  darkMode: ["class", "class"],
  mode: "jit",
  plugins: [
    tailwindcssAnimate,
    typography,
    heroui({
      defaultExtendTheme: "dark",
      defaultTheme: "dark",
      prefix: "heroui",
      themes: {
        dark: {
          colors: {
            primary: {
              DEFAULT: "#00bbff",
              foreground: "#000000",
            },
            white: {
              DEFAULT: "#ffffff",
              foreground: "#000000",
            },
          },
        },
        light: {
          colors: {
            primary: {
              DEFAULT: "#00bbff",
              foreground: "#000000",
            },
            white: {
              DEFAULT: "#ffffff",
              foreground: "#000000",
            },
          },
        },
      },
    }),
  ],
};

export default config;

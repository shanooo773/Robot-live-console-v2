import { extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
  config: {
    initialColorMode: "light",
    useSystemColorMode: false,
  },
  fonts: {
    heading: "'Inter', sans-serif",
    body: "'Inter', sans-serif",
    mono: "'JetBrains Mono', monospace",
  },
  colors: {
    brand: {
      50: "#EFF6FF",
      100: "#DBEAFE",
      200: "#BFDBFE",
      300: "#93C5FD",
      400: "#60A5FA",
      500: "#2563EB",
      600: "#1D4ED8",
      700: "#1E40AF",
      800: "#1E3A8A",
      900: "#1E3470",
    },
    blue: {
      50: "#EFF6FF",
      100: "#DBEAFE",
      200: "#BFDBFE",
      300: "#93C5FD",
      400: "#60A5FA",
      500: "#2563EB",
      600: "#1D4ED8",
      700: "#1E40AF",
      800: "#1E3A8A",
      900: "#1E3470",
    },
  },
  styles: {
    global: {
      body: {
        bg: "#F0F4FF",
        color: "#1E293B",
        minHeight: "100vh",
        fontFamily: "'Inter', sans-serif",
        overflowX: "hidden",
        overflowY: "auto",
      },
      "@keyframes pulse": {
        "0%, 100%": { opacity: 1 },
        "50%": { opacity: 0.8 },
      },
      "@keyframes float": {
        "0%, 100%": { transform: "translateY(0px)" },
        "50%": { transform: "translateY(-20px)" },
      },
      "@keyframes fadeSlideUp": {
        from: { opacity: 0, transform: "translateY(16px)" },
        to: { opacity: 1, transform: "translateY(0)" },
      },
    },
  },
  components: {
    Card: {
      baseStyle: {
        container: {
          background: "white",
          border: "1px solid #E2E8F0",
          borderRadius: "16px",
          boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
          transition: "all 0.2s ease",
          _hover: {
            boxShadow: "0 8px 24px rgba(37,99,235,0.12)",
            transform: "translateY(-2px)",
          },
        },
      },
    },
    Button: {
      baseStyle: {
        borderRadius: "10px",
        fontWeight: "600",
        fontFamily: "'Inter', sans-serif",
        transition: "all 0.2s ease",
        _focus: {
          boxShadow: "0 0 0 3px rgba(37,99,235,0.25)",
        },
      },
      variants: {
        solid: {
          bg: "brand.500",
          color: "white",
          _hover: {
            bg: "brand.600",
            transform: "translateY(-1px)",
            boxShadow: "0 4px 12px rgba(37,99,235,0.3)",
          },
          _active: {
            transform: "translateY(0)",
            bg: "brand.700",
          },
        },
        ghost: {
          bg: "transparent",
          color: "gray.600",
          _hover: {
            bg: "gray.100",
            color: "gray.900",
          },
        },
        outline: {
          bg: "white",
          border: "1.5px solid",
          borderColor: "gray.200",
          color: "gray.700",
          _hover: {
            borderColor: "brand.500",
            color: "brand.600",
            bg: "brand.50",
          },
        },
      },
    },
    Text: {
      variants: {
        neonGlow: {
          color: "brand.600",
          fontWeight: "700",
        },
      },
    },
    Box: {
      variants: {
        glassPanel: {
          bg: "rgba(255,255,255,0.85)",
          backdropFilter: "blur(12px)",
          border: "1px solid #E2E8F0",
          borderRadius: "8px",
          boxShadow: "0 4px 16px rgba(0,0,0,0.06)",
        },
        neonBorder: {
          border: "1.5px solid #E2E8F0",
          borderRadius: "8px",
          boxShadow: "0 2px 8px rgba(0,0,0,0.06)",
        },
      },
    },
  },
});

export default theme;

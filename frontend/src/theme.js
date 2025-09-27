import { extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
  config: {
    initialColorMode: "dark",
    useSystemColorMode: false,
  },
  fonts: {
    heading: "'Orbitron', sans-serif",
    body: "'Rajdhani', sans-serif",
    mono: "'Exo 2', monospace",
  },
  colors: {
    brand: {
      50: "#e6f3ff",
      100: "#b3d9ff",
      200: "#80bfff",
      300: "#4da6ff",
      400: "#1a8cff",
      500: "#0066cc",
      600: "#0052a3",
      700: "#003d7a",
      800: "#002952",
      900: "#001429",
    },
    blue: {
      50: "#e6f3ff",
      100: "#b3d9ff",
      200: "#80bfff",
      300: "#4da6ff",
      400: "#1a8cff",
      500: "#0066cc",
      600: "#0052a3",
      700: "#003d7a",
      800: "#002952",
      900: "#001429",
    },
    neon: {
      cyan: "rgba(0,255,200,0.8)",
      blue: "rgba(0,191,255,0.8)",
      purple: "rgba(138,43,226,0.8)",
      pink: "rgba(255,20,147,0.8)",
      green: "rgba(50,205,50,0.8)",
    }
  },
  styles: {
    global: {
      body: {
        bg: "linear-gradient(135deg, #0a0015 0%, #1a0033 25%, #001a33 50%, #003366 75%, #004080 100%)",
        minHeight: "100vh",
        fontFamily: "'Rajdhani', sans-serif",
        overflowX: "hidden",
        overflowY: "auto",
      },
      "@keyframes pulse": {
        "0%, 100%": {
          opacity: 1,
        },
        "50%": {
          opacity: 0.8,
        },
      },
      "@keyframes float": {
        "0%, 100%": {
          transform: "translateY(0px)",
        },
        "50%": {
          transform: "translateY(-20px)",
        },
      },
      "@keyframes neonGlow": {
        "0%, 100%": {
          textShadow: "0 0 5px rgba(0,255,200,0.5), 0 0 10px rgba(0,255,200,0.3), 0 0 15px rgba(0,255,200,0.1)",
        },
        "50%": {
          textShadow: "0 0 10px rgba(0,255,200,0.8), 0 0 20px rgba(0,255,200,0.6), 0 0 30px rgba(0,255,200,0.4)",
        },
      },
      "@keyframes borderGlow": {
        "0%, 100%": {
          boxShadow: "0 0 5px rgba(0,255,200,0.3), inset 0 0 5px rgba(0,255,200,0.1)",
        },
        "50%": {
          boxShadow: "0 0 20px rgba(0,255,200,0.6), inset 0 0 10px rgba(0,255,200,0.2)",
        },
      },
    },
  },
  components: {
    Card: {
      baseStyle: {
        container: {
          background: "rgba(26, 32, 44, 0.3)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(0,255,200,0.2)",
          borderRadius: "12px",
          boxShadow: "0 8px 32px rgba(0,0,0,0.3), 0 0 0 1px rgba(0,255,200,0.1)",
          transition: "all 0.3s ease",
          _hover: {
            border: "1px solid rgba(0,255,200,0.4)",
            boxShadow: "0 12px 48px rgba(0,0,0,0.4), 0 0 20px rgba(0,255,200,0.2)",
            transform: "translateY(-2px)",
          },
        },
      },
    },
    Button: {
      baseStyle: {
        borderRadius: "full",
        fontWeight: "600",
        fontFamily: "'Exo 2', sans-serif",
        transition: "all 0.3s ease",
        _focus: {
          boxShadow: "0 0 0 3px rgba(0,255,200,0.3)",
        },
      },
      variants: {
        solid: {
          bg: "rgba(0,191,255,0.2)",
          color: "white",
          border: "1px solid rgba(0,191,255,0.4)",
          boxShadow: "0 4px 20px rgba(0,191,255,0.2)",
          backdropFilter: "blur(8px)",
          _hover: {
            bg: "rgba(0,191,255,0.3)",
            border: "1px solid rgba(0,191,255,0.6)",
            boxShadow: "0 6px 30px rgba(0,191,255,0.4), 0 0 20px rgba(0,191,255,0.2)",
            transform: "translateY(-2px)",
          },
          _active: {
            transform: "translateY(0)",
          },
        },
        ghost: {
          bg: "transparent",
          color: "gray.300",
          border: "1px solid transparent",
          _hover: {
            bg: "rgba(0,255,200,0.1)",
            color: "white",
            border: "1px solid rgba(0,255,200,0.3)",
            boxShadow: "0 0 15px rgba(0,255,200,0.2)",
          },
        },
        neonPrimary: {
          bg: "rgba(0,255,200,0.1)",
          color: "rgba(0,255,200,1)",
          border: "2px solid rgba(0,255,200,0.5)",
          textShadow: "0 0 10px rgba(0,255,200,0.8)",
          boxShadow: "0 0 20px rgba(0,255,200,0.3), inset 0 0 20px rgba(0,255,200,0.1)",
          _hover: {
            bg: "rgba(0,255,200,0.2)",
            border: "2px solid rgba(0,255,200,0.8)",
            boxShadow: "0 0 30px rgba(0,255,200,0.6), inset 0 0 30px rgba(0,255,200,0.2)",
            transform: "translateY(-2px)",
          },
        },
      },
    },
    Text: {
      variants: {
        neonGlow: {
          color: "rgba(0,255,200,1)",
          textShadow: "0 0 10px rgba(0,255,200,0.8), 0 0 20px rgba(0,255,200,0.4)",
          fontFamily: "'Orbitron', sans-serif",
          fontWeight: "700",
        },
      },
    },
    Box: {
      variants: {
        glassPanel: {
          bg: "rgba(26, 32, 44, 0.2)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(0,255,200,0.2)",
          borderRadius: "8px",
          boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
        },
        neonBorder: {
          border: "1px solid rgba(0,255,200,0.4)",
          borderRadius: "8px",
          boxShadow: "0 0 15px rgba(0,255,200,0.2), inset 0 0 15px rgba(0,255,200,0.1)",
          animation: "borderGlow 2s ease-in-out infinite alternate",
        },
      },
    },
  },
});

export default theme;

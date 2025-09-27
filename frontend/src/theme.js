import { extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
  config: {
    initialColorMode: "dark",
    useSystemColorMode: false,
  },
  fonts: {
    heading: "'Orbitron', 'Exo 2', 'Rajdhani', sans-serif",
    body: "'Orbitron', 'Exo 2', 'Rajdhani', sans-serif",
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
      cyan: "rgba(0, 255, 200, 0.8)",
      blue: "rgba(0, 191, 255, 0.8)",
      purple: "rgba(138, 43, 226, 0.8)",
      pink: "rgba(255, 20, 147, 0.8)",
      green: "rgba(50, 205, 50, 0.8)",
    }
  },
  styles: {
    global: {
      html: {
        height: '100%',
      },
      body: {
        height: '100%',
        bg: "linear-gradient(135deg, #0a0f23 0%, #1a1a2e 50%, #16213e 100%)",
        backgroundAttachment: "fixed",
        minHeight: "100vh",
        fontFamily: "'Orbitron', 'Exo 2', 'Rajdhani', sans-serif",
      },
      "#root": {
        height: '100%',
        minHeight: '100vh',
      },
      "html, body, #root": {
        overflow: "hidden",
      }, 
      "@keyframes neonGlow": {
        "0%, 100%": {
          textShadow: "0 0 5px rgba(0, 255, 200, 0.5), 0 0 10px rgba(0, 255, 200, 0.5), 0 0 15px rgba(0, 255, 200, 0.5)",
        },
        "50%": {
          textShadow: "0 0 10px rgba(0, 255, 200, 0.8), 0 0 20px rgba(0, 255, 200, 0.8), 0 0 30px rgba(0, 255, 200, 0.8)",
        },
      },
      "@keyframes neonWave": {
        "0%": {
          backgroundPosition: "0% 50%",
        },
        "50%": {
          backgroundPosition: "100% 50%",
        },
        "100%": {
          backgroundPosition: "0% 50%",
        },
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
    },
  },
  components: {
    Card: {
      baseStyle: {
        container: {
          background: "rgba(10, 15, 35, 0.6)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(0, 255, 200, 0.3)",
          boxShadow: "0 8px 32px rgba(0, 255, 200, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.1)",
          borderRadius: "16px",
          transition: "all 0.3s ease",
          _hover: {
            border: "1px solid rgba(0, 255, 200, 0.5)",
            boxShadow: "0 12px 48px rgba(0, 255, 200, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.1)",
            transform: "translateY(-2px)",
          },
        },
      },
    },
    Button: {
      baseStyle: {
        borderRadius: "12px",
        fontWeight: "600",
        transition: "all 0.3s ease",
        fontFamily: "'Orbitron', sans-serif",
      },
      variants: {
        solid: {
          bg: "rgba(0, 191, 255, 0.1)",
          color: "rgba(0, 255, 200, 0.9)",
          border: "1px solid rgba(0, 255, 200, 0.4)",
          backdropFilter: "blur(8px)",
          _hover: {
            bg: "rgba(0, 191, 255, 0.2)",
            border: "1px solid rgba(0, 255, 200, 0.7)",
            boxShadow: "0 0 20px rgba(0, 255, 200, 0.4)",
            transform: "translateY(-2px)",
          },
          _active: {
            transform: "translateY(0px)",
          },
        },
        neonPill: {
          bg: "rgba(0, 0, 0, 0.3)",
          color: "rgba(0, 255, 200, 0.9)",
          border: "1px solid rgba(0, 255, 200, 0.4)",
          borderRadius: "full",
          backdropFilter: "blur(8px)",
          px: 6,
          py: 2,
          fontSize: "sm",
          _hover: {
            bg: "rgba(0, 255, 200, 0.1)",
            border: "1px solid rgba(0, 255, 200, 0.7)",
            boxShadow: "0 0 15px rgba(0, 255, 200, 0.4)",
            transform: "scale(1.05)",
          },
        },
        ghost: {
          color: "rgba(255, 255, 255, 0.7)",
          _hover: {
            color: "rgba(0, 255, 200, 0.9)",
            bg: "rgba(0, 255, 200, 0.1)",
          },
        },
      },
    },
    Badge: {
      variants: {
        neonPill: {
          bg: "rgba(0, 255, 200, 0.2)",
          color: "rgba(0, 255, 200, 1)",
          border: "1px solid rgba(0, 255, 200, 0.5)",
          borderRadius: "full",
          px: 3,
          py: 1,
          fontSize: "xs",
          fontWeight: "600",
          textTransform: "uppercase",
          boxShadow: "0 0 10px rgba(0, 255, 200, 0.3)",
        },
      },
    },
  },
});

export default theme;

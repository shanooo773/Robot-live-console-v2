import { extendTheme } from "@chakra-ui/react";

const theme = extendTheme({
  config: {
    initialColorMode: "dark",
    useSystemColorMode: false,
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
    }
  },
  styles: {
    global: {
      body: {
        bg: "linear-gradient(135deg, #001429 0%, #002952 50%, #003d7a 100%)",
        minHeight: "100vh",
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
          boxShadow: "0 8px 32px rgba(255, 255, 255, 0.1)",
          border: "1px solid",
          borderColor: "whiteAlpha.200",
          backdropFilter: "blur(10px)",
          transition: "all 0.3s ease",
          _hover: {
            boxShadow: "0 12px 48px rgba(255, 255, 255, 0.15)",
            transform: "translateY(-4px)",
          },
        },
      },
    },
    Button: {
      baseStyle: {
        borderRadius: "full",
        fontWeight: "bold",
        transition: "all 0.3s ease",
      },
      variants: {
        solid: {
          bg: "linear-gradient(135deg, #1a8cff, #0066cc)",
          color: "white",
          boxShadow: "0 4px 20px rgba(26, 140, 255, 0.4)",
          _hover: {
            bg: "linear-gradient(135deg, #4da6ff, #1a8cff)",
            boxShadow: "0 6px 30px rgba(26, 140, 255, 0.6)",
            transform: "translateY(-2px)",
          },
        },
      },
    },
  },
});

export default theme;

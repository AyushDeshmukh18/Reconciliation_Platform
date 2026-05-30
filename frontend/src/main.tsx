import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Toaster } from "react-hot-toast";
import App from "./App";
import "./styles/tokens.css";
import "./styles/typography.css";
import "./styles/global.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
    <Toaster
      position="bottom-right"
      toastOptions={{
        style: {
          background: "var(--color-surface-elevated)",
          color: "var(--color-foreground)",
          border: "1px solid var(--color-border)",
          fontSize: "14px",
        },
        success: {
          iconTheme: { primary: "var(--color-success)", secondary: "#fff" },
        },
        error: {
          iconTheme: { primary: "var(--color-danger)", secondary: "#fff" },
        },
      }}
    />
  </StrictMode>
);

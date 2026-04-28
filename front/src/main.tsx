import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./app/App";
import { AppProviders } from "./app/providers";
import { RootErrorBoundary } from "./components/ui/root-error-boundary";
import "./styles/index.css";

createRoot(document.getElementById("root") as HTMLElement).render(
  <StrictMode>
    <AppProviders>
      <RootErrorBoundary>
        <App />
      </RootErrorBoundary>
    </AppProviders>
  </StrictMode>,
);

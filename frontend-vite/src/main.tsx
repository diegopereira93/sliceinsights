import { createRoot } from "react-dom/client";
import { setBaseUrl } from "./lib/api-client/custom-fetch";
import App from "./App";
import "./index.css";

// Bootstrap the API base URL from environment
const apiBase = import.meta.env.VITE_API_URL ?? "http://localhost:8002";
setBaseUrl(apiBase);

createRoot(document.getElementById("root")!).render(<App />);
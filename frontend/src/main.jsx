import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import "./index.css";
import App from "./App.jsx";
import LandingPage from "./components/LandingPage";
import Auth from "./components/Auth";
import Dashboard from "./components/Dashboard";
import { MathJaxContext } from "better-react-mathjax";
import Analytics from "./pages/Analytics.jsx";

const mathJaxConfig = {
  loader: { load: ["input/tex", "output/chtml"] },
};

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <MathJaxContext config={mathJaxConfig}>
        <Routes>
          <Route
            path='/'
            element={<LandingPage />}
          />
          <Route
            path='/auth'
            element={<Auth />}
          />
          <Route
            path='/dashboard/*'
            element={<Dashboard />}
          />
          <Route
            path='/analytics'
            element={<Analytics />}
          />
        </Routes>
      </MathJaxContext>
    </BrowserRouter>
  </StrictMode>
);

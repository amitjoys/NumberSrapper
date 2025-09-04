import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// Global error handler for ResizeObserver errors (common with UI libraries)
const suppressResizeObserverErrors = () => {
  const resizeObserverErrorHandler = (e) => {
    if (e.message && (
      e.message.includes('ResizeObserver loop completed with undelivered notifications') ||
      e.message.includes('ResizeObserver loop limit exceeded') ||
      e.message.includes('ResizeObserver')
    )) {
      e.stopImmediatePropagation();
      return true;
    }
    return false;
  };

  // Handle window errors
  window.addEventListener('error', resizeObserverErrorHandler);
  
  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (e) => {
    if (e.reason && e.reason.message && e.reason.message.includes('ResizeObserver')) {
      e.preventDefault();
    }
  });
  
  // Monkey patch console.error to suppress ResizeObserver errors
  const originalConsoleError = console.error;
  console.error = (...args) => {
    if (args.length > 0 && typeof args[0] === 'string' && args[0].includes('ResizeObserver')) {
      return; // Suppress ResizeObserver errors
    }
    originalConsoleError.apply(console, args);
  };
};

// Apply the error suppression
suppressResizeObserverErrors();

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

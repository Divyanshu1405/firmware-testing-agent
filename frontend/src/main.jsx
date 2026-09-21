import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './index.css';
import ErrorBoundary from "./components/ErrorBoundary";
import { PipelineProvider } from './hooks/usePipeline';

ReactDOM.createRoot(document.getElementById('root')).render(
 <React.StrictMode>
  <BrowserRouter>
    <ErrorBoundary>
      <PipelineProvider>
        <App />
      </PipelineProvider>
    </ErrorBoundary>
  </BrowserRouter>
</React.StrictMode>
);

import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import { Toaster } from './components/ui/sonner';
import { toast } from 'sonner';

// Components
import Header from './components/Header';
import ScrapingForm from './components/ScrapingForm';
import BulkUpload from './components/BulkUpload';
import ProgressTracker from './components/ProgressTracker';
import ResultsTable from './components/ResultsTable';
import { useWebSocket } from './hooks/useWebSocket';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Home = () => {
  const [activeTab, setActiveTab] = useState('single');
  const [currentJob, setCurrentJob] = useState(null);
  const [jobResults, setJobResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // WebSocket connection for real-time updates
  const wsUrl = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') + '/ws';
  const { messages, isConnected } = useWebSocket(wsUrl);

  // Handle WebSocket messages
  useEffect(() => {
    if (messages.length > 0) {
      const latestMessage = messages[messages.length - 1];
      
      try {
        const data = JSON.parse(latestMessage);
        
        switch (data.type) {
          case 'progress_update':
            if (currentJob && data.job_id === currentJob.id) {
              setCurrentJob(prev => ({
                ...prev,
                progress: data.progress,
                completed: data.completed,
                failed: data.failed,
                total: data.total || prev.total
              }));
            }
            break;
            
          case 'url_complete':
            if (data.success && data.data) {
              setJobResults(prev => {
                const newResults = [...prev];
                const existingIndex = newResults.findIndex(r => r.url === data.url);
                if (existingIndex >= 0) {
                  newResults[existingIndex] = data.data;
                } else {
                  newResults.push(data.data);
                }
                return newResults;
              });
            }
            break;
            
          case 'job_complete':
            toast.success(`Scraping completed! ${data.completed} successful, ${data.failed} failed`);
            setIsLoading(false);
            if (currentJob && data.job_id === currentJob.id) {
              setCurrentJob(prev => ({
                ...prev,
                status: 'completed',
                progress: 100,
                completed: data.completed,
                failed: data.failed,
                total: data.total || prev.total
              }));
            }
            break;
            
          case 'job_error':
            toast.error(`Scraping failed: ${data.error}`);
            setIsLoading(false);
            break;
            
          default:
            break;
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e);
      }
    }
  }, [messages, currentJob]);

  const handleSingleUrlSubmit = async (url, maxThreads) => {
    setIsLoading(true);
    setJobResults([]);
    
    try {
      const response = await axios.post(`${API}/scrape/single`, {
        url,
        max_threads: maxThreads
      });
      
      if (response.data.status === 'started') {
        const jobData = {
          id: response.data.job_id,
          type: 'single',
          status: 'started',
          progress: 0,
          completed: 0,
          failed: 0,
          total: 1
        };
        setCurrentJob(jobData);
        toast.success('Scraping started! Check progress below.');
        
        // Start polling job status as fallback in case WebSocket messages are missed
        pollJobStatus(response.data.job_id);
      } else {
        toast.error(response.data.message);
        setIsLoading(false);
      }
    } catch (error) {
      toast.error('Failed to start scraping');
      setIsLoading(false);
      console.error('Error:', error);
    }
  };

  const handleBulkUpload = async (file, maxThreads) => {
    setIsLoading(true);
    setJobResults([]);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('max_threads', maxThreads);
    
    try {
      const response = await axios.post(`${API}/scrape/bulk`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      if (response.data.status === 'started') {
        setCurrentJob({
          id: response.data.job_id,
          type: 'bulk',
          status: 'started',
          progress: 0,
          completed: 0,
          failed: 0,
          total: 0 // Will be updated via WebSocket
        });
        toast.success(response.data.message);
        
        // Start polling job status as fallback in case WebSocket messages are missed
        pollJobStatus(response.data.job_id);
      } else {
        toast.error(response.data.message);
        setIsLoading(false);
      }
    } catch (error) {
      toast.error('Failed to start bulk scraping');
      setIsLoading(false);
      console.error('Error:', error);
    }
  };

  const downloadResults = async () => {
    if (!currentJob) return;
    
    try {
      const response = await axios.get(`${API}/scrape/download/${currentJob.id}`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `scraping_results_${currentJob.id}.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Results downloaded successfully!');
    } catch (error) {
      toast.error('Failed to download results');
      console.error('Error:', error);
    }
  };

  const downloadTemplate = async () => {
    try {
      const response = await axios.get(`${API}/scrape/template`, {
        responseType: 'blob',
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'bulk_scraping_template.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast.success('Template downloaded successfully!');
    } catch (error) {
      toast.error('Failed to download template');
      console.error('Error:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <Header />
      
      <main className="container mx-auto px-6 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4 tracking-tight">
            Realtime <span className="text-blue-600">Webscraper</span>
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Extract contact details, social media URLs, and company information with high accuracy. 
            Smart caching and real-time progress tracking included.
          </p>
        </div>

        {/* Connection Status */}
        <div className="flex justify-center mb-8">
          <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
            isConnected 
              ? 'bg-green-100 text-green-800 border border-green-200' 
              : 'bg-red-100 text-red-800 border border-red-200'
          }`}>
            <div className={`w-2 h-2 rounded-full mr-2 ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}></div>
            {isConnected ? 'Connected' : 'Disconnected'}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              <button
                onClick={() => setActiveTab('single')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'single'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Single URL
              </button>
              <button
                onClick={() => setActiveTab('bulk')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'bulk'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Bulk Upload
              </button>
            </nav>
          </div>
        </div>

        {/* Content Area */}
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Forms */}
          {activeTab === 'single' ? (
            <ScrapingForm
              onSubmit={handleSingleUrlSubmit}
              isLoading={isLoading}
            />
          ) : (
            <BulkUpload
              onUpload={handleBulkUpload}
              onDownloadTemplate={downloadTemplate}
              isLoading={isLoading}
            />
          )}

          {/* Progress Tracker */}
          {currentJob && (
            <ProgressTracker
              job={currentJob}
              onDownload={downloadResults}
            />
          )}

          {/* Results Table */}
          {jobResults.length > 0 && (
            <ResultsTable results={jobResults} />
          )}
        </div>
      </main>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-right" />
    </div>
  );
}

export default App;
import React, { useState, useMemo } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Globe, Play, Settings } from 'lucide-react';

const ScrapingForm = ({ onSubmit, isLoading }) => {
  const [url, setUrl] = useState('');
  const [maxThreads, setMaxThreads] = useState('5');

  // Memoize thread options to prevent unnecessary re-renders
  const threadOptions = useMemo(() => 
    Array.from({ length: 25 }, (_, i) => i + 1).map((num) => ({
      value: num.toString(),
      label: `${num} ${num === 1 ? 'thread' : 'threads'}`
    })), []
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    
    onSubmit(url.trim(), parseInt(maxThreads));
  };

  const isValidUrl = (string) => {
    try {
      new URL(string.startsWith('http') ? string : `https://${string}`);
      return true;
    } catch (_) {
      return false;
    }
  };

  return (
    <Card className="animate-fadeIn card-hover">
      <CardHeader className="pb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-gradient-to-br from-blue-500 to-indigo-600 p-2 rounded-lg">
            <Globe className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-xl">Single URL Scraping</CardTitle>
            <CardDescription>
              Extract contact details from a single website
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="url" className="text-sm font-medium text-gray-700">
              Website URL
            </Label>
            <div className="relative">
              <Input
                id="url"
                type="url"
                placeholder="https://example.com or example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="pl-10 h-12 text-base"
                required
              />
              <Globe className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            </div>
            {url && !isValidUrl(url) && (
              <p className="text-sm text-red-600">Please enter a valid URL</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="threads" className="text-sm font-medium text-gray-700 flex items-center space-x-2">
              <Settings className="w-4 h-4" />
              <span>Max Threads</span>
            </Label>
            <Select value={maxThreads} onValueChange={setMaxThreads}>
              <SelectTrigger className="h-12">
                <SelectValue placeholder="Select thread count" />
              </SelectTrigger>
              <SelectContent className="max-h-60 overflow-y-auto">
                {Array.from({ length: 25 }, (_, i) => i + 1).map((num) => (
                  <SelectItem key={num} value={num.toString()}>
                    {num} {num === 1 ? 'thread' : 'threads'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-gray-500">
              Higher thread counts may be faster but could trigger rate limiting
            </p>
          </div>

          <Button
            type="submit"
            disabled={isLoading || !url.trim() || !isValidUrl(url)}
            className="w-full h-12 text-base btn-primary"
          >
            {isLoading ? (
              <div className="flex items-center space-x-2">
                <div className="spinner"></div>
                <span>Scraping...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <Play className="w-4 h-4" />
                <span>Start Scraping</span>
              </div>
            )}
          </Button>
        </form>

        {/* Features List */}
        <div className="mt-6 pt-6 border-t border-gray-100">
          <h4 className="text-sm font-medium text-gray-900 mb-3">What we extract:</h4>
          <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
              <span>Phone numbers (E164)</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
              <span>Email addresses</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
              <span>Social media links</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
              <span>Company addresses</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
              <span>Team member details</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-1.5 h-1.5 bg-blue-500 rounded-full"></div>
              <span>Leadership info</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ScrapingForm;
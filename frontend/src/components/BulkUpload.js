import React, { useState, useCallback, useMemo } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Upload, FileText, Download, Play, Settings, CheckCircle, AlertCircle } from 'lucide-react';
import Papa from 'papaparse';

const BulkUpload = ({ onUpload, onDownloadTemplate, isLoading }) => {
  const [file, setFile] = useState(null);
  const [maxThreads, setMaxThreads] = useState('5');
  const [csvPreview, setCsvPreview] = useState(null);
  const [parseError, setParseError] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const uploadedFile = acceptedFiles[0];
    if (uploadedFile) {
      setFile(uploadedFile);
      setParseError(null);
      
      // Preview CSV content
      Papa.parse(uploadedFile, {
        header: true,
        preview: 5,
        complete: (results) => {
          if (results.errors.length > 0) {
            setParseError('Error parsing CSV file. Please check the format.');
            setCsvPreview(null);
          } else if (!results.data.some(row => row.url)) {
            setParseError('CSV must contain a "url" column.');
            setCsvPreview(null);
          } else {
            setCsvPreview(results.data);
          }
        },
        error: (error) => {
          setParseError('Failed to parse CSV file.');
          setCsvPreview(null);
        }
      });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv']
    },
    maxFiles: 1
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!file || parseError) return;
    
    onUpload(file, parseInt(maxThreads));
  };

  const removeFile = () => {
    setFile(null);
    setCsvPreview(null);
    setParseError(null);
  };

  return (
    <Card className="animate-fadeIn card-hover">
      <CardHeader className="pb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-gradient-to-br from-green-500 to-emerald-600 p-2 rounded-lg">
            <Upload className="w-5 h-5 text-white" />
          </div>
          <div>
            <CardTitle className="text-xl">Bulk CSV Upload</CardTitle>
            <CardDescription>
              Upload a CSV file with URLs for batch processing
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Template Download */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileText className="w-5 h-5 text-blue-600" />
              <div>
                <h4 className="text-sm font-medium text-blue-900">Need a template?</h4>
                <p className="text-sm text-blue-700">Download our CSV template to get started</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onDownloadTemplate}
              className="border-blue-300 text-blue-700 hover:bg-blue-100"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Template
            </Button>
          </div>
        </div>

        {/* File Upload Zone */}
        <div
          {...getRootProps()}
          className={`upload-zone border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
            isDragActive
              ? 'border-blue-400 bg-blue-50 drag-active'
              : file
              ? 'border-green-400 bg-green-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          
          {file ? (
            <div className="space-y-3">
              <CheckCircle className="w-12 h-12 text-green-500 mx-auto" />
              <div>
                <p className="text-lg font-medium text-green-700">{file.name}</p>
                <p className="text-sm text-green-600">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile();
                }}
                className="mt-2"
              >
                Remove File
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-lg font-medium text-gray-700">
                  {isDragActive ? 'Drop your CSV file here' : 'Click to upload or drag and drop'}
                </p>
                <p className="text-sm text-gray-500">CSV files only, up to 10MB</p>
              </div>
            </div>
          )}
        </div>

        {/* Parse Error */}
        {parseError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-sm text-red-700">{parseError}</p>
            </div>
          </div>
        )}

        {/* CSV Preview */}
        {csvPreview && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-900 mb-3">CSV Preview (first 5 rows)</h4>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-300">
                    <th className="text-left py-2 px-3 font-medium text-gray-700">URL</th>
                  </tr>
                </thead>
                <tbody>
                  {csvPreview.map((row, index) => (
                    <tr key={index} className="border-b border-gray-200">
                      <td className="py-2 px-3 text-gray-600">{row.url || '(empty)'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Thread Selection */}
        <div className="space-y-2">
          <Label htmlFor="bulk-threads" className="text-sm font-medium text-gray-700 flex items-center space-x-2">
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
            More threads = faster processing, but may trigger rate limiting
          </p>
        </div>

        {/* Submit Button */}
        <Button
          onClick={handleSubmit}
          disabled={isLoading || !file || parseError}
          className="w-full h-12 text-base btn-primary"
        >
          {isLoading ? (
            <div className="flex items-center space-x-2">
              <div className="spinner"></div>
              <span>Processing...</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2">
              <Play className="w-4 h-4" />
              <span>Start Bulk Scraping</span>
            </div>
          )}
        </Button>

        {/* Requirements */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-2">CSV Requirements:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Must contain a column named "url"</li>
            <li>• URLs can include or exclude http/https protocol</li>
            <li>• Results will be returned in the same order as input</li>
            <li>• Maximum file size: 10MB</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  );
};

export default BulkUpload;
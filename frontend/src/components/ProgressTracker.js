import React from 'react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Download, Clock, CheckCircle, XCircle, BarChart3 } from 'lucide-react';

const ProgressTracker = ({ job, onDownload }) => {
  if (!job) return null;

  const getStatusIcon = () => {
    switch (job.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-blue-500 animate-pulse" />;
    }
  };

  const getStatusText = () => {
    switch (job.status) {
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'in_progress':
        return 'In Progress';
      default:
        return 'Starting...';
    }
  };

  const getStatusColor = () => {
    switch (job.status) {
      case 'completed':
        return 'text-green-700 bg-green-50 border-green-200';
      case 'failed':
        return 'text-red-700 bg-red-50 border-red-200';
      default:
        return 'text-blue-700 bg-blue-50 border-blue-200';
    }
  };

  return (
    <Card className="animate-slideInRight card-hover">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-br from-purple-500 to-indigo-600 p-2 rounded-lg">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <CardTitle className="text-xl">Scraping Progress</CardTitle>
              <CardDescription>
                Job ID: {job.id}
              </CardDescription>
            </div>
          </div>
          
          <div className={`flex items-center space-x-2 px-3 py-1 rounded-full border text-sm font-medium ${getStatusColor()}`}>
            {getStatusIcon()}
            <span>{getStatusText()}</span>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-gray-700">Overall Progress</span>
            <span className="text-gray-600">{job.progress || 0}%</span>
          </div>
          
          <div className="relative">
            <Progress 
              value={job.progress || 0} 
              className="h-3 progress-bar"
            />
          </div>
          
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>0%</span>
            <span>100%</span>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {job.total || job.urls?.length || 0}
            </div>
            <div className="text-sm text-blue-700">Total URLs</div>
          </div>
          
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {job.completed || 0}
            </div>
            <div className="text-sm text-green-700">Completed</div>
          </div>
          
          <div className="text-center p-4 bg-red-50 rounded-lg">
            <div className="text-2xl font-bold text-red-600">
              {job.failed || 0}
            </div>
            <div className="text-sm text-red-700">Failed</div>
          </div>
        </div>

        {/* Success Rate */}
        {(job.completed > 0 || job.failed > 0) && (
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">Success Rate</span>
              <span className="text-sm text-gray-600">
                {job.completed + job.failed > 0 
                  ? Math.round((job.completed / (job.completed + job.failed)) * 100)
                  : 0}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{
                  width: `${job.completed + job.failed > 0 
                    ? (job.completed / (job.completed + job.failed)) * 100
                    : 0}%`
                }}
              ></div>
            </div>
          </div>
        )}

        {/* Download Button */}
        {job.status === 'completed' && job.completed > 0 && (
          <div className="pt-4 border-t border-gray-100">
            <Button
              onClick={onDownload}
              className="w-full h-12 text-base btn-primary"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Results CSV
            </Button>
          </div>
        )}

        {/* Status Messages */}
        {job.status === 'failed' && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <XCircle className="w-5 h-5 text-red-500" />
              <p className="text-sm text-red-700">
                Scraping job failed. Please try again with different settings.
              </p>
            </div>
          </div>
        )}

        {job.status === 'in_progress' && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <p className="text-sm text-blue-700">
                Scraping in progress... You can leave this page and come back later.
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ProgressTracker;
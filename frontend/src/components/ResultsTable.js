import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { 
  Search, 
  ExternalLink, 
  Phone, 
  Mail, 
  Linkedin, 
  Facebook, 
  Instagram, 
  Github,
  MapPin,
  User,
  Filter,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

const ResultsTable = ({ results }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedResult, setSelectedResult] = useState(null);
  const itemsPerPage = 10;

  if (!results || results.length === 0) {
    return null;
  }

  const filteredResults = results.filter(result =>
    result.url?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    result.email_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    result.company_address?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(filteredResults.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedResults = filteredResults.slice(startIndex, startIndex + itemsPerPage);

  const formatPhoneNumbers = (phones) => {
    if (!phones || phones.length === 0) return 'None';
    return phones.slice(0, 2).join(', ') + (phones.length > 2 ? ` (+${phones.length - 2} more)` : '');
  };

  const openUrl = (url) => {
    if (url) {
      window.open(url.startsWith('http') ? url : `https://${url}`, '_blank');
    }
  };

  const DetailModal = ({ result, onClose }) => {
    if (!result) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div className="p-6 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-xl font-semibold text-gray-900">Scraping Results</h3>
              <Button variant="outline" size="sm" onClick={onClose}>
                Close
              </Button>
            </div>
            <p className="text-sm text-gray-500 mt-1">{result.url}</p>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Contact Information */}
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Contact Information</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Mail className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-600">Email:</span>
                  </div>
                  <p className="text-sm font-medium">{result.email_address || 'Not found'}</p>
                </div>
                
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <Phone className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-600">Phone Numbers:</span>
                  </div>
                  <div className="space-y-1">
                    {result.phone_numbers && result.phone_numbers.length > 0 ? (
                      result.phone_numbers.map((phone, index) => (
                        <p key={index} className="text-sm font-medium">{phone}</p>
                      ))
                    ) : (
                      <p className="text-sm font-medium">Not found</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Address */}
            {result.company_address && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Address</h4>
                <div className="flex items-start space-x-2">
                  <MapPin className="w-4 h-4 text-gray-400 mt-0.5" />
                  <p className="text-sm">{result.company_address}</p>
                </div>
              </div>
            )}

            {/* Social Media */}
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-3">Social Media</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { key: 'linkedin_url', icon: Linkedin, label: 'LinkedIn', color: 'text-blue-600' },
                  { key: 'facebook_url', icon: Facebook, label: 'Facebook', color: 'text-blue-700' },
                  { key: 'instagram_url', icon: Instagram, label: 'Instagram', color: 'text-pink-600' },
                  { key: 'github_url', icon: Github, label: 'GitHub', color: 'text-gray-800' }
                ].map(({ key, icon: Icon, label, color }) => (
                  <div key={key} className="flex items-center space-x-2">
                    <Icon className={`w-4 h-4 ${color}`} />
                    <div>
                      <p className="text-xs text-gray-600">{label}</p>
                      {result[key] ? (
                        <Button
                          variant="link"
                          size="sm"
                          className="p-0 h-auto text-xs"
                          onClick={() => openUrl(result[key])}
                        >
                          View Profile
                        </Button>
                      ) : (
                        <p className="text-xs text-gray-400">Not found</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Team Members */}
            {result.persons && result.persons.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-900 mb-3">Team Members</h4>
                <div className="space-y-3">
                  {result.persons.map((person, index) => (
                    <div key={index} className="bg-gray-50 rounded-lg p-4">
                      <div className="flex items-start space-x-3">
                        <User className="w-5 h-5 text-gray-400 mt-0.5" />
                        <div className="flex-1">
                          <h5 className="font-medium text-gray-900">{person.name || 'Unknown'}</h5>
                          {person.title && (
                            <p className="text-sm text-gray-600">{person.title}</p>
                          )}
                          <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                            {person.email && (
                              <div className="flex items-center space-x-2">
                                <Mail className="w-3 h-3 text-gray-400" />
                                <span>{person.email}</span>
                              </div>
                            )}
                            {person.phone && (
                              <div className="flex items-center space-x-2">
                                <Phone className="w-3 h-3 text-gray-400" />
                                <span>{person.phone}</span>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      <Card className="animate-fadeIn">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-xl">Scraping Results</CardTitle>
              <CardDescription>
                {filteredResults.length} of {results.length} results
              </CardDescription>
            </div>
            
            <div className="flex items-center space-x-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search results..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Website</TableHead>
                  <TableHead>Contact Info</TableHead>
                  <TableHead>Social Media</TableHead>
                  <TableHead>Team Members</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {paginatedResults.map((result, index) => (
                  <TableRow key={index} className="table-row">
                    <TableCell>
                      <div className="space-y-1">
                        <Button
                          variant="link"
                          size="sm"
                          className="p-0 h-auto text-blue-600 hover:text-blue-800"
                          onClick={() => openUrl(result.url)}
                        >
                          <ExternalLink className="w-3 h-3 mr-1" />
                          {result.url?.length > 30 
                            ? `${result.url.substring(0, 30)}...` 
                            : result.url}
                        </Button>
                        {result.company_address && (
                          <p className="text-xs text-gray-500 flex items-center">
                            <MapPin className="w-3 h-3 mr-1" />
                            {result.company_address.length > 40 
                              ? `${result.company_address.substring(0, 40)}...` 
                              : result.company_address}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="space-y-1">
                        {result.email_address && (
                          <div className="flex items-center text-sm">
                            <Mail className="w-3 h-3 mr-1 text-gray-400" />
                            <span className="truncate">{result.email_address}</span>
                          </div>
                        )}
                        {result.phone_numbers && result.phone_numbers.length > 0 && (
                          <div className="flex items-center text-sm">
                            <Phone className="w-3 h-3 mr-1 text-gray-400" />
                            <span>{formatPhoneNumbers(result.phone_numbers)}</span>
                          </div>
                        )}
                        {!result.email_address && (!result.phone_numbers || result.phone_numbers.length === 0) && (
                          <span className="text-xs text-gray-400">No contact info</span>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex space-x-1">
                        {[
                          { key: 'linkedin_url', icon: Linkedin, color: 'text-blue-600' },
                          { key: 'facebook_url', icon: Facebook, color: 'text-blue-700' },
                          { key: 'instagram_url', icon: Instagram, color: 'text-pink-600' },
                          { key: 'github_url', icon: Github, color: 'text-gray-800' }
                        ].map(({ key, icon: Icon, color }) => (
                          result[key] ? (
                            <Button
                              key={key}
                              variant="ghost"
                              size="sm"
                              className="p-1 h-auto"
                              onClick={() => openUrl(result[key])}
                            >
                              <Icon className={`w-4 h-4 ${color}`} />
                            </Button>
                          ) : null
                        ))}
                        {!result.linkedin_url && !result.facebook_url && !result.instagram_url && !result.github_url && (
                          <span className="text-xs text-gray-400">None found</span>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      {result.persons && result.persons.length > 0 ? (
                        <Badge variant="secondary">
                          {result.persons.length} member{result.persons.length !== 1 ? 's' : ''}
                        </Badge>
                      ) : (
                        <span className="text-xs text-gray-400">None found</span>
                      )}
                    </TableCell>
                    
                    <TableCell>
                      <Badge variant={result.success ? "default" : "destructive"}>
                        {result.success ? 'Success' : 'Failed'}
                      </Badge>
                    </TableCell>
                    
                    <TableCell>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setSelectedResult(result)}
                      >
                        View Details
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6">
              <p className="text-sm text-gray-600">
                Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredResults.length)} of {filteredResults.length} results
              </p>
              
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </Button>
                
                <span className="text-sm text-gray-600">
                  Page {currentPage} of {totalPages}
                </span>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedResult && (
        <DetailModal 
          result={selectedResult} 
          onClose={() => setSelectedResult(null)} 
        />
      )}
    </>
  );
};

export default ResultsTable;
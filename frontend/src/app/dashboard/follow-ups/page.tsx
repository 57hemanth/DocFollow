'use client';

import { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Clock, CheckCircle, Calendar } from 'lucide-react';

interface FollowUp {
  _id: string;
  patient_id: string;
  patient_name: string;
  patient_phone: string;
  patient_diagnosis: string;
  followup_date: string;
  status: 'upcoming' | 'current' | 'completed' | 'overdue';
  message_sent: boolean;
  response_received: boolean;
  created_at: string;
}

type FilterStatus = 'all' | 'upcoming' | 'current' | 'completed' | 'overdue';

export default function Page() {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [filteredFollowUps, setFilteredFollowUps] = useState<FollowUp[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterStatus>('upcoming');
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchFollowUps = async () => {
    try {
      setIsRefreshing(true);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/followups/with-patients`);
      if (!response.ok) {
        throw new Error('Failed to fetch follow-ups');
      }
      const data = await response.json();
      
      // Categorize follow-ups based on date and status
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      
      const categorizedData = data.map((followup: any) => {
        const followupDate = new Date(followup.followup_date);
        const followupDay = new Date(followupDate.getFullYear(), followupDate.getMonth(), followupDate.getDate());
        
        let status: 'upcoming' | 'current' | 'completed' | 'overdue';
        
        if (followup.final_message_sent && followup.response_received) {
          status = 'completed';
        } else if (followupDay < today) {
          status = 'overdue';
        } else if (followupDay.getTime() === today.getTime()) {
          status = 'current';
        } else {
          status = 'upcoming';
        }
        
        return {
          ...followup,
          status
        };
      });
      
      setFollowUps(categorizedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchFollowUps();
  }, []);

  useEffect(() => {
    if (filter === 'all') {
      setFilteredFollowUps(followUps);
    } else {
      setFilteredFollowUps(followUps.filter(followup => followup.status === filter));
    }
  }, [followUps, filter]);

  const formatTo12Hour = (dateTimeString: string): string => {
    try {
      const date = new Date(dateTimeString);
      return date.toLocaleTimeString('en-US', { 
        hour: 'numeric', 
        minute: '2-digit', 
        hour12: true 
      });
    } catch {
      return 'N/A';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'upcoming':
        return <Badge variant="outline" className="text-blue-600 border-blue-200 bg-blue-50"><Clock className="w-3 h-3 mr-1" />Upcoming</Badge>;
      case 'current':
        return <Badge variant="outline" className="text-orange-600 border-orange-200 bg-orange-50"><Calendar className="w-3 h-3 mr-1" />Today</Badge>;
      case 'completed':
        return <Badge variant="outline" className="text-green-600 border-green-200 bg-green-50"><CheckCircle className="w-3 h-3 mr-1" />Completed</Badge>;
      case 'overdue':
        return <Badge variant="outline" className="text-red-600 border-red-200 bg-red-50"><Clock className="w-3 h-3 mr-1" />Overdue</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getFilterCounts = () => {
    const counts = {
      all: followUps.length,
      upcoming: followUps.filter(f => f.status === 'upcoming').length,
      current: followUps.filter(f => f.status === 'current').length,
      completed: followUps.filter(f => f.status === 'completed').length,
      overdue: followUps.filter(f => f.status === 'overdue').length,
    };
    return counts;
  };

  if (isLoading) {
    return <main className="flex-1 p-6 md:p-8"><div>Loading...</div></main>;
  }

  if (error) {
    return <main className="flex-1 p-6 md:p-8"><div>Error: {error}</div></main>;
  }

  const counts = getFilterCounts();

  return (
    <main className="flex-1 p-6 md:p-8 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200">Patient Follow-ups</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchFollowUps}
          disabled={isRefreshing}
          className="flex items-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Filter Controls */}
      <div className="flex items-center gap-4 mb-6">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter by status:</label>
        <Select value={filter} onValueChange={(value: FilterStatus) => setFilter(value)}>
          <SelectTrigger className="w-48">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All ({counts.all})</SelectItem>
            <SelectItem value="upcoming">Upcoming ({counts.upcoming})</SelectItem>
            <SelectItem value="current">Today ({counts.current})</SelectItem>
            <SelectItem value="completed">Completed ({counts.completed})</SelectItem>
            <SelectItem value="overdue">Overdue ({counts.overdue})</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="border rounded-lg shadow-sm bg-white dark:bg-gray-800">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Patient</TableHead>
              <TableHead>Diagnosis</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Follow-up Date</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Progress</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredFollowUps.length > 0 ? (
              filteredFollowUps.map((followup) => (
                <TableRow key={followup._id}>
                  <TableCell className="font-medium">{followup.patient_name}</TableCell>
                  <TableCell>{followup.patient_diagnosis}</TableCell>
                  <TableCell>{followup.patient_phone}</TableCell>
                  <TableCell>
                    <div>
                      {new Date(followup.followup_date).toLocaleDateString('en-GB')}
                      <br />
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {formatTo12Hour(followup.followup_date)}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    {getStatusBadge(followup.status)}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${followup.message_sent ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          {followup.message_sent ? 'Message sent' : 'Pending'}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${followup.response_received ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          {followup.response_received ? 'Response received' : 'No response'}
                        </span>
                      </div>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} className="text-center text-gray-500 dark:text-gray-400">
                  {filter === 'all' ? 'No follow-ups found.' : `No ${filter} follow-ups.`}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </main>
  );
}

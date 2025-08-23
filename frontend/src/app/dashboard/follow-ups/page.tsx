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

interface Patient {
  _id: string;
  name: string;
  diagnosis: string;
  phone: string;
  followup_date?: string;
}

export default function Page() {
  const [followUps, setFollowUps] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFollowUps = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients`);
        if (!response.ok) {
          throw new Error('Failed to fetch patients with follow-ups');
        }
        const data = await response.json();
        const upcoming = data.filter((patient: Patient) => patient.followup_date && new Date(patient.followup_date) > new Date());
        setFollowUps(upcoming);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchFollowUps();
  }, []);

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

  if (isLoading) {
    return <main className="flex-1 p-6 md:p-8"><div>Loading...</div></main>;
  }

  if (error) {
    return <main className="flex-1 p-6 md:p-8"><div>Error: {error}</div></main>;
  }

  return (
    <main className="flex-1 p-6 md:p-8 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200">Upcoming Follow-ups</h1>
      </div>

      <div className="border rounded-lg shadow-sm">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Diagnosis</TableHead>
              <TableHead>Phone</TableHead>
              <TableHead>Follow-up Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {followUps.length > 0 ? (
              followUps.map((patient) => (
                <TableRow key={patient._id}>
                  <TableCell className="font-medium">{patient.name}</TableCell>
                  <TableCell>{patient.diagnosis}</TableCell>
                  <TableCell>{patient.phone}</TableCell>
                  <TableCell>
                    {patient.followup_date ? (
                      <>
                        {new Date(patient.followup_date).toLocaleDateString('en-GB')}
                        <br />
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {formatTo12Hour(patient.followup_date)}
                        </span>
                      </>
                    ) : (
                      'N/A'
                    )}
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="text-center">
                  No upcoming follow-ups.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </main>
  );
}

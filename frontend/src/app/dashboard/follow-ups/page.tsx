'use client';

import { useState, useEffect, useCallback } from 'react';
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
import { RefreshCw, User, MessageSquare, Send, X, ClipboardList } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogClose,
  DialogDescription,
} from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { useSession } from 'next-auth/react';
import { format } from 'date-fns';

interface Message {
  sender: 'patient' | 'agent' | 'doctor';
  content: string;
  timestamp: string;
}

interface FollowUp {
  _id: string;
  patient_id: string;
  doctor_id: string;
  status: 'waiting_for_patient' | 'waiting_for_doctor' | 'closed';
  history: Message[];
  original_data?: string[];
  extracted_data?: Record<string, any>;
  ai_draft_message?: string;
  note?: string;
  created_at: string;
  updated_at: string;
  // Fields to be populated client-side
  patient_name?: string;
  patient_phone?: string;
}

type FilterStatus = 'all' | 'waiting_for_patient' | 'waiting_for_doctor' | 'closed';

// Main Component
export default function Page() {
  const [followUps, setFollowUps] = useState<FollowUp[]>([]);
  const [filteredFollowUps, setFilteredFollowUps] = useState<FollowUp[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterStatus>('waiting_for_doctor');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedFollowUp, setSelectedFollowUp] = useState<FollowUp | null>(null);
  const [isDetailsDialogOpen, setIsDetailsDialogOpen] = useState(false);
  const { data: session } = useSession();

  const fetchFollowUps = useCallback(async () => {
    if (!session?.user?.id) return;
    try {
      setIsRefreshing(true);
      setError(null);
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/followups?doctor_id=${session.user.id}`);
      if (!response.ok) throw new Error('Failed to fetch follow-ups');
      
      const data: FollowUp[] = await response.json();
      
      // Enrich with patient data
      const enrichedData = await Promise.all(data.map(async (f) => {
        const patientRes = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients/${f.patient_id}?doctor_id=${session.user.id}`);
        if(patientRes.ok) {
          const patientData = await patientRes.json();
          return {...f, patient_name: patientData.name, patient_phone: patientData.phone};
        }
        return {...f, patient_name: 'Unknown', patient_phone: 'N/A'};
      }));
      
      setFollowUps(enrichedData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [session]);

  useEffect(() => {
    fetchFollowUps();
  }, [fetchFollowUps]);

  useEffect(() => {
    const filtered = filter === 'all' ? followUps : followUps.filter(f => f.status === filter);
    setFilteredFollowUps(filtered);
  }, [followUps, filter]);

  const handleSendMessage = async (followupId: string, message: string) => {
    if (!session?.user?.id) return;
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/followups/${followupId}/send-message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ doctor_id: session.user.id, message_content: message }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to send message');
      }
      setIsDetailsDialogOpen(false);
      fetchFollowUps(); // Refresh the list
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
    }
  };

  if (isLoading) return <main className="flex-1 p-6 md:p-8"><div>Loading...</div></main>;
  if (error) return <main className="flex-1 p-6 md:p-8"><div className="text-red-500">Error: {error}</div></main>;

  const counts = {
    all: followUps.length,
    waiting_for_patient: followUps.filter(f => f.status === 'waiting_for_patient').length,
    waiting_for_doctor: followUps.filter(f => f.status === 'waiting_for_doctor').length,
    closed: followUps.filter(f => f.status === 'closed').length,
  };

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

      <div className="flex items-center gap-4 mb-6">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Filter by status:</label>
        <Select value={filter} onValueChange={(value: FilterStatus) => setFilter(value)}>
          <SelectTrigger className="w-48"><SelectValue /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All ({counts.all})</SelectItem>
            <SelectItem value="waiting_for_doctor">Needs Review ({counts.waiting_for_doctor})</SelectItem>
            <SelectItem value="waiting_for_patient">Waiting for Patient ({counts.waiting_for_patient})</SelectItem>
            <SelectItem value="closed">Closed ({counts.closed})</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="border rounded-lg shadow-sm bg-white dark:bg-gray-800">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Patient</TableHead>
              <TableHead>Last Update</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredFollowUps.length > 0 ? (
              filteredFollowUps.map((followup) => (
                <TableRow key={followup._id}>
                  <TableCell className="font-medium">{followup.patient_name || 'Loading...'}</TableCell>
                  <TableCell>{format(new Date(followup.updated_at), "dd MMM yyyy, hh:mm a")}</TableCell>
                  <TableCell><StatusBadge status={followup.status} /></TableCell>
                  <TableCell>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedFollowUp(followup);
                        setIsDetailsDialogOpen(true);
                      }}
                    >
                      View Details
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-gray-500 dark:text-gray-400">
                  No follow-ups match the current filter.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
      
      {selectedFollowUp && (
        <FollowUpDetailsDialog
          followup={selectedFollowUp}
          isOpen={isDetailsDialogOpen}
          onClose={() => setIsDetailsDialogOpen(false)}
          onSendMessage={handleSendMessage}
        />
      )}
    </main>
  );
}

// StatusBadge Component
const StatusBadge = ({ status }: { status: FollowUp['status'] }) => {
  const statusStyles = {
    waiting_for_patient: "text-blue-600 border-blue-200 bg-blue-50",
    waiting_for_doctor: "text-orange-600 border-orange-200 bg-orange-50",
    closed: "text-green-600 border-green-200 bg-green-50",
  };
  const statusText = {
    waiting_for_patient: "Waiting for Patient",
    waiting_for_doctor: "Needs Review",
    closed: "Closed",
  };
  return <Badge variant="outline" className={statusStyles[status]}>{statusText[status]}</Badge>;
};

// FollowUpDetailsDialog Component
interface DialogProps {
  followup: FollowUp;
  isOpen: boolean;
  onClose: () => void;
  onSendMessage: (followupId: string, message: string) => void;
}

const FollowUpDetailsDialog = ({ followup, isOpen, onClose, onSendMessage }: DialogProps) => {
  const [message, setMessage] = useState('');
  
  useEffect(() => {
    if (followup?.ai_draft_message) {
      setMessage(followup.ai_draft_message);
    }
  }, [followup]);
  
  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(followup._id, message);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl w-full h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Follow-up Details: {followup.patient_name}</DialogTitle>
          <DialogDescription>
            Review patient-submitted data, check history, and send a response.
          </DialogDescription>
        </DialogHeader>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 py-4 flex-1 overflow-y-auto">
          {/* Left side: Patient Data */}
          <div className="space-y-4 pr-4 border-r">
            <h3 className="font-semibold text-lg flex items-center"><ClipboardList className="mr-2" /> Patient Submitted Data</h3>
            
            {/* Raw Data Previews */}
            {followup.original_data && followup.original_data.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-semibold">Attachments</h4>
                <div className="grid grid-cols-2 gap-2">
                  {followup.original_data.map((url, index) => (
                    <a key={index} href={url} target="_blank" rel="noopener noreferrer" className="block border rounded-md overflow-hidden hover:opacity-80 transition-opacity">
                      <img src={url} alt={`Patient submission ${index + 1}`} className="w-full h-auto object-cover" />
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Extracted Data */}
            {followup.extracted_data && (
              <div className="space-y-2">
                <h4 className="font-semibold">Extracted Text</h4>
                <div className="text-sm bg-gray-100 dark:bg-gray-800 p-3 rounded-md whitespace-pre-wrap font-sans">
                  <p>{followup.extracted_data?.text || 'No text extracted.'}</p>
                </div>
              </div>
            )}
          </div>

          {/* Right side: Communication */}
          <div className="space-y-4 flex flex-col">
             <h3 className="font-semibold text-lg flex items-center"><MessageSquare className="mr-2" /> Communication Panel</h3>
            
            {/* History */}
            <div className="flex-1 space-y-4 rounded-md border p-4 bg-gray-50 dark:bg-gray-800 overflow-y-auto">
              <h4 className="font-semibold">History</h4>
              {followup.history.map((msg, index) => (
                <div key={index} className={`flex flex-col ${msg.sender === 'patient' ? 'items-start' : 'items-end'}`}>
                  <div className={`rounded-lg p-3 max-w-sm ${msg.sender === 'patient' ? 'bg-white dark:bg-gray-700' : 'bg-blue-100 dark:bg-blue-900'}`}>
                    <p className="text-sm">{msg.content}</p>
                  </div>
                  <span className="text-xs text-gray-500 mt-1">
                    {msg.sender.charAt(0).toUpperCase() + msg.sender.slice(1)} - {format(new Date(msg.timestamp), "hh:mm a")}
                  </span>
                </div>
              ))}
            </div>
            
            {/* AI Draft & Response */}
            {followup.status === 'waiting_for_doctor' && (
              <div className="space-y-2 pt-4 border-t">
                <h4 className="font-semibold">Respond to Patient (AI Draft)</h4>
                <Textarea 
                  placeholder="Review the AI draft or write your own message..."
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  rows={6}
                  className="text-base"
                />
              </div>
            )}
          </div>
        </div>

        <DialogFooter className="mt-auto pt-4 border-t">
          <Button variant="outline" onClick={onClose}>Close</Button>
          {followup.status === 'waiting_for_doctor' && (
            <Button onClick={handleSend}><Send className="mr-2 h-4 w-4" /> Send Message</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

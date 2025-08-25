"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
  
interface AppointmentDetails {
  event_title: string;
  start_time: string;
  end_time: string;
}

interface Appointment {
  _id: string;
  patient_id: string;
  doctor_id: string;
  followup_id: string;
  event_title: string;
  start_time: string;
  end_time: string;
  status: string;
  patient: {
    _id: string;
    name: string;
  };
}

interface FollowUp {
  _id: string;
  patient_id: {
    _id: string;
    name: string;
  };
  doctor_id: string;
  status: string;
  summary: string;
  created_at: string;
  gcal_auth_url?: string;
  appointment_details?: AppointmentDetails;
}

export default function Page() {
  const [completedFollowUps, setCompletedFollowUps] = useState<FollowUp[]>([]);
  const [schedulingFollowUps, setSchedulingFollowUps] = useState<FollowUp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { data: session, status } = useSession();

  useEffect(() => {
    const fetchData = async () => {
      if (status === "loading") return;
      if (!session) {
        setError("You must be logged in to view this page.");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const doctor_id = session.user?.id;

        if (!doctor_id) {
          setError("Doctor ID not found in session.");
          setLoading(false);
          return;
        }

        const [completedRes, schedulingRes] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/followups?doctor_id=${doctor_id}&status=completed`),
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/followups?doctor_id=${doctor_id}&status=appointment_scheduling`),
        ]);

        if (!completedRes.ok || !schedulingRes.ok) {
          throw new Error("Failed to fetch data");
        }

        const completedData = await completedRes.json();
        const schedulingData = await schedulingRes.json();

        setCompletedFollowUps(completedData);
        setSchedulingFollowUps(schedulingData);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [session, status]);

  if (loading) return <p>Loading...</p>;
  if (error) return <p>Error: {error}</p>;

  return (
    <main className="p-4 md:p-8">
      <h1 className="text-2xl font-bold mb-4">Appointments</h1>
      
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Pending Appointments</CardTitle>
          <CardDescription>
            These follow-ups are waiting for the patient to provide their availability.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Patient</TableHead>
                <TableHead>Summary</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Requested On</TableHead>
                <TableHead>Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedulingFollowUps.length > 0 ? (
                schedulingFollowUps.map((followUp) => (
                  <TableRow key={followUp._id}>
                    <TableCell>{followUp.patient_id.name}</TableCell>
                    <TableCell>{followUp.summary}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{followUp.status}</Badge>
                    </TableCell>
                    <TableCell>
                      {new Date(followUp.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      {followUp.gcal_auth_url && (
                        <a
                          href={followUp.gcal_auth_url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <Badge>Authenticate Google Calendar</Badge>
                        </a>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="text-center">
                    No pending appointments.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Confirmed Appointments</CardTitle>
          <CardDescription>
            These appointments have been successfully booked in Google Calendar.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Title</TableHead>
                <TableHead>Patient</TableHead>
                <TableHead>Start Time</TableHead>
                <TableHead>End Time</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {completedFollowUps.length > 0 ? (
                completedFollowUps.map((followUp) => (
                  <TableRow key={followUp._id}>
                    <TableCell>{followUp.appointment_details?.event_title}</TableCell>
                    <TableCell>{followUp.patient_id.name}</TableCell>
                    <TableCell>
                      {followUp.appointment_details?.start_time
                        ? new Date(followUp.appointment_details.start_time).toLocaleString()
                        : "N/A"}
                    </TableCell>
                    <TableCell>
                      {followUp.appointment_details?.end_time
                        ? new Date(followUp.appointment_details.end_time).toLocaleString()
                        : "N/A"}
                    </TableCell>
                    <TableCell>
                      <Badge>{followUp.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={5} className="text-center">
                    No confirmed appointments.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </main>
  );
}

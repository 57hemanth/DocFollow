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
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PlusCircle } from 'lucide-react';

interface Patient {
  _id: string;
  name: string;
  disease: string;
  phone: string;
  address?: string;
  notes?: string;
  image_url?: string;
}

export default function Page() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [newPatient, setNewPatient] = useState({
    name: '',
    disease: '',
    phone: '',
    address: '',
    notes: '',
    image_url: '',
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients`);
        if (!response.ok) {
          throw new Error('Failed to fetch patients');
        }
        const data = await response.json();
        setPatients(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPatients();
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setNewPatient((prev) => ({ ...prev, [id]: value }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleAddPatient = async () => {
    let imageUrl = '';

    if (selectedFile) {
      const formData = new FormData();
      formData.append('file', selectedFile);

      try {
        const uploadResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/upload`, {
          method: 'POST',
          body: formData,
        });

        if (!uploadResponse.ok) {
          throw new Error('Failed to upload image');
        }

        const uploadData = await uploadResponse.json();
        imageUrl = uploadData.url;
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
        return;
      }
    }

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/patients`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ ...newPatient, image_url: imageUrl, doctor_id: '1' }), // Hardcoded doctor_id for now
      });

      if (!response.ok) {
        throw new Error('Failed to add patient');
      }

      const createdPatient = await response.json();
      setPatients((prev) => [...prev, createdPatient]);
      setNewPatient({ name: '', disease: '', phone: '', address: '', notes: '', image_url: '' });
      setSelectedFile(null);
      setIsDialogOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
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
        <h1 className="text-2xl font-bold text-gray-800 dark:text-gray-200">Patients</h1>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button className="flex items-center gap-2">
              <PlusCircle className="h-5 w-5" />
              Add Patient
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px] bg-white dark:bg-gray-800">
            <DialogHeader>
              <DialogTitle className="text-gray-800 dark:text-gray-200">Add New Patient</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="name" className="text-right text-gray-600 dark:text-gray-400">
                  Name
                </Label>
                <Input id="name" value={newPatient.name} onChange={handleInputChange} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="disease" className="text-right text-gray-600 dark:text-gray-400">
                  Disease
                </Label>
                <Input id="disease" value={newPatient.disease} onChange={handleInputChange} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="phone" className="text-right text-gray-600 dark:text-gray-400">
                  Phone
                </Label>
                <Input id="phone" value={newPatient.phone} onChange={handleInputChange} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="address" className="text-right text-gray-600 dark:text-gray-400">
                  Address
                </Label>
                <Input id="address" value={newPatient.address} onChange={handleInputChange} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="notes" className="text-right text-gray-600 dark:text-gray-400">
                  Notes
                </Label>
                <Input id="notes" value={newPatient.notes} onChange={handleInputChange} className="col-span-3" />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="image" className="text-right text-gray-600 dark:text-gray-400">
                  Image
                </Label>
                <Input id="image" type="file" onChange={handleFileChange} className="col-span-3" />
              </div>
            </div>
            <div className="flex justify-end">
              <Button onClick={handleAddPatient}>Add Patient</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="border rounded-lg shadow-sm">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Image</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Disease</TableHead>
              <TableHead>Phone</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {patients.map((patient) => (
              <TableRow key={patient._id}>
                <TableCell>
                  {patient.image_url && (
                    <img
                      src={patient.image_url}
                      alt={patient.name}
                      className="h-10 w-10 rounded-lg object-cover"
                    />
                  )}
                </TableCell>
                <TableCell className="font-medium">{patient.name}</TableCell>
                <TableCell>{patient.disease}</TableCell>
                <TableCell>{patient.phone}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </main>
  );
}

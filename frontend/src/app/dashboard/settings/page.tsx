
"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSession } from "next-auth/react";

interface WhatsAppSandboxInfo {
  sandbox_number: string;
  join_code: string;
  instructions: string[];
  note: string;
}

interface Settings {
  whatsapp_connected: boolean;
  whatsapp_number?: string;
  whatsapp_sandbox_id?: string;
  google_calendar_connected: boolean;
  notifications?: unknown;
}

export default function SettingsPage() {
  const { data: session } = useSession();
  const [settings, setSettings] = useState<Settings>({
    whatsapp_connected: false,
    google_calendar_connected: false,
  });
  const [sandboxInfo, setSandboxInfo] = useState<WhatsAppSandboxInfo | null>(null);
  const [testPhoneNumber, setTestPhoneNumber] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (session?.user?.id) {
      fetchSettings(session.user.id);
    }
    fetchSandboxInfo();
  }, [session]);

  const fetchSettings = async (userId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/settings/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error("Failed to fetch settings:", error);
    }
  };

  const fetchSandboxInfo = async () => {
    try {
      const response = await fetch("http://localhost:8000/settings/whatsapp/sandbox-info");
      if (response.ok) {
        const data = await response.json();
        setSandboxInfo(data);
      }
    } catch (error) {
      console.error("Failed to fetch sandbox info:", error);
    }
  };

  const testWhatsAppConnection = async () => {
    if (!session?.user?.id || !testPhoneNumber) return;
    
    setIsLoading(true);
    setMessage("");
    
    try {
      const response = await fetch(`http://localhost:8000/settings/${session.user.id}/whatsapp/test`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          phone_number: testPhoneNumber,
        }),
      });
      
      const data = await response.json();
      
      if (data.status === "success") {
        setMessage("✅ Test message sent successfully! Check your WhatsApp.");
        if (data.updated_settings) {
          setSettings(data.updated_settings);
        } else {
          setSettings(prev => ({ ...prev, whatsapp_connected: true, whatsapp_number: testPhoneNumber }));
        }
      } else {
        setMessage(`❌ ${data.message}`);
      }
    } catch (error) {
      setMessage(`❌ Failed to send test message: ${error}`);
    } finally {
      setIsLoading(false);
    }
  };

  const updateSettings = async (newSettings: Partial<Settings>) => {
    if (!session?.user?.id) return;
    
    try {
      const response = await fetch(`http://localhost:8000/settings/${session.user.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newSettings),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error("Failed to update settings:", error);
    }
  };

  return (
    <main className="flex-1 p-6 md:p-8">
    <div className="space-y-6">
      {/* WhatsApp Integration Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>📱</span>
            WhatsApp Integration
          </CardTitle>
          <CardDescription>
            Connect WhatsApp to send automated follow-up reminders and receive patient updates
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Connection Status */}
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div>
              <p className="font-medium">Connection Status</p>
              <p className="text-sm text-muted-foreground">
                {settings.whatsapp_connected ? (
                  <span className="text-green-600">✅ Connected ({settings.whatsapp_number})</span>
                ) : (
                  <span className="text-orange-600">⚠️ Not Connected</span>
                )}
              </p>
            </div>
            {settings.whatsapp_connected && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => updateSettings({ whatsapp_connected: false, whatsapp_number: undefined })}
              >
                Disconnect
              </Button>
            )}
          </div>

          {/* Sandbox Setup Instructions */}
          {sandboxInfo && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">📋 Twilio WhatsApp Sandbox Setup</h4>
              <div className="space-y-2 text-sm text-blue-800">
                <p><strong>Sandbox Number:</strong> {sandboxInfo.sandbox_number}</p>
                <p><strong>Join Message:</strong> {sandboxInfo.join_code}</p>
                <div>
                  <p><strong>Setup Steps:</strong></p>
                  <ol className="list-decimal list-inside space-y-1 ml-4">
                    {sandboxInfo.instructions.map((instruction, index) => (
                      <li key={index}>{instruction}</li>
                    ))}
                  </ol>
                </div>
                <p className="text-xs mt-2 text-blue-600">{sandboxInfo.note}</p>
              </div>
            </div>
          )}

          {/* Test Connection */}
          <div className="space-y-4">
            <div>
              <Label htmlFor="testPhone">Test WhatsApp Connection</Label>
              <p className="text-sm text-muted-foreground mb-2">
                Enter your phone number to test the WhatsApp integration
              </p>
              <div className="flex gap-2">
                <Input
                  id="testPhone"
                  type="tel"
                  placeholder="+1234567890"
                  value={testPhoneNumber}
                  onChange={(e) => setTestPhoneNumber(e.target.value)}
                  className="flex-1"
                />
                <Button
                  onClick={testWhatsAppConnection}
                  disabled={!testPhoneNumber || isLoading}
                  className="shrink-0"
                >
                  {isLoading ? "Sending..." : "Send Test"}
                </Button>
              </div>
            </div>
            
            {message && (
              <div className={`p-3 rounded-lg text-sm ${
                message.includes("✅") 
                  ? "bg-green-50 text-green-800 border border-green-200" 
                  : "bg-red-50 text-red-800 border border-red-200"
              }`}>
                {message}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
    </main>
  );
}

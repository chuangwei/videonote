import { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { RefreshCw, ArrowLeft } from 'lucide-react';

interface LogViewerProps {
  onBack: () => void;
}

export function LogViewer({ onBack }: LogViewerProps) {
  const [logs, setLogs] = useState<string>('');
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const content = await invoke<string>('get_log_contents');
      setLogs(content);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
      setLogs(`Error fetching logs: ${error}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="container mx-auto p-4 max-w-4xl h-screen flex flex-col">
      <Card className="flex-1 flex flex-col h-full">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="icon" onClick={onBack}>
              <ArrowLeft className="h-4 w-4" />
            </Button>
            <CardTitle>System Logs</CardTitle>
          </div>
          <Button variant="outline" size="sm" onClick={fetchLogs} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </CardHeader>
        <CardContent className="flex-1 min-h-0 overflow-hidden">
          <div className="bg-slate-950 text-slate-50 p-4 rounded-md h-full overflow-auto font-mono text-xs whitespace-pre-wrap">
            {logs || 'No logs available.'}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

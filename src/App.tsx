import { useState } from 'react';
import { DownloadPage } from "./components/DownloadPage";
import { LogViewer } from "./components/LogViewer";
import { Button } from "./components/ui/button";
import { FileText } from "lucide-react";

function App() {
  const [showLogs, setShowLogs] = useState(false);

  if (showLogs) {
    return <LogViewer onBack={() => setShowLogs(false)} />;
  }

  return (
    <div className="min-h-screen bg-background relative">
      <div className="absolute top-4 right-4 z-10">
        <Button variant="ghost" size="icon" onClick={() => setShowLogs(true)} title="View Logs">
            <FileText className="h-5 w-5" />
        </Button>
      </div>
      <DownloadPage />
    </div>
  );
}

export default App;

import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

/**
 * API Client for communicating with the Python sidecar
 */
class ApiClient {
  private port: number | null = null;
  private baseUrl: string | null = null;
  private portPromise: Promise<number> | null = null;

  constructor() {
    this.initializePort();
  }

  /**
   * Initialize the port by listening to the sidecar-port event and invoking get_sidecar_port
   */
  private initializePort() {
    this.portPromise = new Promise((resolve, reject) => {
      // First, try to get the port via invoke (if already set)
      invoke<number>("get_sidecar_port")
        .then((port) => {
          console.log("Got sidecar port from invoke:", port);
          this.setPort(port);
          resolve(port);
        })
        .catch((error) => {
          console.log("Port not yet available via invoke, listening for event:", error);

          // Listen for the sidecar-port event
          listen<number>("sidecar-port", (event) => {
            console.log("Received sidecar-port event:", event.payload);
            this.setPort(event.payload);
            resolve(event.payload);
          });

          // Also keep polling invoke in case we missed the event
          const pollInterval = setInterval(() => {
            invoke<number>("get_sidecar_port")
              .then((port) => {
                clearInterval(pollInterval);
                console.log("Got sidecar port from polling:", port);
                this.setPort(port);
                resolve(port);
              })
              .catch(() => {
                // Port not ready yet, continue polling
              });
          }, 500);

          // Timeout after 30 seconds
          setTimeout(() => {
            clearInterval(pollInterval);
            reject(new Error("Timeout waiting for sidecar port"));
          }, 30000);
        });
    });
  }

  /**
   * Set the port and update the base URL
   */
  private setPort(port: number) {
    this.port = port;
    this.baseUrl = `http://127.0.0.1:${port}`;
    console.log("API baseUrl set to:", this.baseUrl);
  }

  /**
   * Wait for the port to be available
   */
  async waitForPort(): Promise<number> {
    if (this.port !== null) {
      return this.port;
    }
    return this.portPromise!;
  }

  /**
   * Get the base URL for the API
   */
  async getBaseUrl(): Promise<string> {
    if (this.baseUrl !== null) {
      return this.baseUrl;
    }
    await this.waitForPort();
    return this.baseUrl!;
  }

  /**
   * Make a GET request to the Python API
   */
  async get<T>(path: string): Promise<T> {
    const baseUrl = await this.getBaseUrl();
    const response = await fetch(`${baseUrl}${path}`);

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Make a POST request to the Python API
   */
  async post<T>(path: string, data: any): Promise<T> {
    const baseUrl = await this.getBaseUrl();
    const response = await fetch(`${baseUrl}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API request failed: ${response.statusText} - ${errorText}`);
    }

    return response.json();
  }

  /**
   * Health check
   */
  async healthCheck() {
    return this.get<{ status: string; message: string }>("/health");
  }

  /**
   * Start a video download
   */
  async startDownload(url: string, savePath: string, formatPreference = "best") {
    return this.post<{
      success: boolean;
      message: string;
      task_id: string;
    }>("/api/download", {
      url,
      save_path: savePath,
      format_preference: formatPreference,
    });
  }

  /**
   * Get download status
   */
  async getDownloadStatus(taskId: string) {
    return this.get<{
      success: boolean;
      message: string;
      task_id: string;
      file_path?: string;
      title?: string;
      duration?: number;
      thumbnail?: string;
    }>(`/api/download/${taskId}`);
  }
}

// Export a singleton instance
export const api = new ApiClient();

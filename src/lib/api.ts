import { invoke, listen } from "@tauri-apps/api/core";

/**
 * API Client for communicating with the Python sidecar
 */
class ApiClient {
  // Dynamic port for Python sidecar (obtained from Tauri)
  private port: number | null = null;
  private portPromise: Promise<number>;

  constructor() {
    console.log("API Client initializing with dynamic port...");
    this.portPromise = this.initializePort();
  }

  /**
   * Initialize and get the dynamic port from Tauri
   */
  private async initializePort(): Promise<number> {
    try {
      // Listen for sidecar-port event
      const unlisten = await listen<number>("sidecar-port", (event) => {
        this.port = event.payload;
        console.log("Received sidecar port from event:", this.port);
      });

      // Also try to get port via invoke (in case event was missed)
      const maxAttempts = 30; // 30 seconds timeout
      for (let i = 0; i < maxAttempts; i++) {
        try {
          const port = await invoke<number>("get_sidecar_port");
          this.port = port;
          console.log("Got sidecar port via invoke:", this.port);
          return port;
        } catch (error) {
          // Port not ready yet, wait and retry
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      }

      throw new Error("Failed to get sidecar port after 30 seconds");
    } catch (error) {
      console.error("Failed to initialize port:", error);
      throw error;
    }
  }

  /**
   * Get the base URL for the API
   */
  async getBaseUrl(): Promise<string> {
    const port = await this.portPromise;
    return `http://127.0.0.1:${port}`;
  }

  /**
   * Make a GET request to the Python API
   */
  async get<T>(path: string): Promise<T> {
    const baseUrl = await this.getBaseUrl();
    const url = `${baseUrl}${path}`;

    console.log(`Making GET request to: ${url}`);

    try {
      // Add timeout for fetch request (especially important on Windows)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout per request

      const response = await fetch(url, {
        signal: controller.signal,
        // Explicitly set mode for CORS
        mode: 'cors',
        // Add cache busting to avoid Windows caching issues
        cache: 'no-cache',
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`API request failed: ${response.statusText}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`Request to ${url} timed out after 10 seconds`);
        }
        throw new Error(`Failed to connect to ${url}: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * Make a POST request to the Python API
   */
  async post<T>(path: string, data: any): Promise<T> {
    const baseUrl = await this.getBaseUrl();
    const url = `${baseUrl}${path}`;

    console.log(`Making POST request to: ${url}`);

    try {
      // Add timeout for fetch request
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000);

      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
        signal: controller.signal,
        mode: 'cors',
        cache: 'no-cache',
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`API request failed: ${response.statusText} - ${errorText}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new Error(`Request to ${url} timed out after 10 seconds`);
        }
        throw new Error(`Failed to connect to ${url}: ${error.message}`);
      }
      throw error;
    }
  }

  /**
   * Health check with retry logic
   */
  async healthCheck() {
    try {
      return await this.get<{ status: string; message: string }>("/health");
    } catch (error) {
      // Provide more detailed error information
      if (error instanceof Error) {
        throw new Error(`Health check failed: ${error.message}. Make sure the sidecar is running.`);
      }
      throw error;
    }
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
      progress?: {
        status: string;
        percent: number;
        speed: string;
        eta: string;
        filename: string;
      };
    }>(`/api/download/${taskId}`);
  }
}

// Export a singleton instance
export const api = new ApiClient();

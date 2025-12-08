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
      let resolved = false;

      // Listen for sidecar error events
      listen<string>("sidecar-error", (event) => {
        if (!resolved) {
          console.error("Sidecar error event received:", event.payload);
          resolved = true;
          reject(new Error(`Sidecar failed to start: ${event.payload}`));
        }
      });

      // Listen for sidecar termination events
      listen<number | null>("sidecar-terminated", (event) => {
        if (!resolved) {
          console.error("Sidecar terminated unexpectedly with code:", event.payload);
          resolved = true;
          reject(new Error(`Sidecar terminated with exit code: ${event.payload}`));
        }
      });

      // First, try to get the port via invoke (if already set)
      invoke<number>("get_sidecar_port")
        .then((port) => {
          if (!resolved) {
            console.log("Got sidecar port from invoke:", port);
            resolved = true;
            this.setPort(port);
            resolve(port);
          }
        })
        .catch((error) => {
          console.log("Port not yet available via invoke, listening for event:", error);

          // Listen for the sidecar-port event
          listen<number>("sidecar-port", (event) => {
            if (!resolved) {
              console.log("Received sidecar-port event:", event.payload);
              resolved = true;
              this.setPort(event.payload);
              resolve(event.payload);
            }
          });

          // Also keep polling invoke in case we missed the event
          const pollInterval = setInterval(() => {
            invoke<number>("get_sidecar_port")
              .then((port) => {
                if (!resolved) {
                  clearInterval(pollInterval);
                  console.log("Got sidecar port from polling:", port);
                  resolved = true;
                  this.setPort(port);
                  resolve(port);
                }
              })
              .catch(() => {
                // Port not ready yet, continue polling
              });
          }, 500);

          // Timeout after 60 seconds (Windows needs more time)
          setTimeout(() => {
            clearInterval(pollInterval);
            if (!resolved) {
              resolved = true;
              reject(new Error("应用初始化超时。请尝试重启应用。如果问题持续，请联系技术支持。"));
            }
          }, 60000);
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

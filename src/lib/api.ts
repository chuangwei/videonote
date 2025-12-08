/**
 * API Client for communicating with the Python sidecar
 */
class ApiClient {
  // Fixed port for Python sidecar
  private readonly port: number = 8118;
  private readonly baseUrl: string = `http://127.0.0.1:${this.port}`;

  constructor() {
    console.log("API baseUrl set to:", this.baseUrl);
  }

  /**
   * Get the base URL for the API
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Make a GET request to the Python API
   */
  async get<T>(path: string): Promise<T> {
    const url = `${this.baseUrl}${path}`;

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
    const url = `${this.baseUrl}${path}`;

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

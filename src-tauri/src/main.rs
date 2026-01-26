use std::sync::{Arc, Mutex};
use tauri::{Emitter, Manager, State};
use tauri_plugin_shell::ShellExt;
use log::{info, error};

// State to store the Python sidecar port
#[derive(Default)]
struct SidecarState {
    port: Arc<Mutex<Option<u16>>>,
}

// Command to get the sidecar port
#[tauri::command]
fn get_sidecar_port(state: State<SidecarState>) -> Result<u16, String> {
    let port = state.port.lock().unwrap();
    match *port {
        Some(p) => Ok(p),
        None => Err("Sidecar port not yet available".to_string()),
    }
}

// Command to open DevTools (removed - not available in Tauri 2.x)
// Use the DevTools shortcut: Cmd+Shift+I (macOS)

#[tauri::command]
async fn get_log_contents(app: tauri::AppHandle) -> Result<String, String> {
    let log_dir = app.path().app_log_dir().map_err(|e| e.to_string())?;
    if !log_dir.exists() {
        return Ok("Log directory not found.".to_string());
    }

    let mut files = Vec::new();
    if let Ok(entries) = std::fs::read_dir(&log_dir) {
        for entry in entries {
            if let Ok(entry) = entry {
                let path = entry.path();
                if path.extension().map_or(false, |ext| ext == "log") {
                    if let Ok(metadata) = std::fs::metadata(&path) {
                        if let Ok(modified) = metadata.modified() {
                            files.push((path, modified));
                        }
                    }
                }
            }
        }
    }

    files.sort_by(|a, b| a.1.cmp(&b.1));

    let mut content = String::new();
    for (path, _) in files {
        content.push_str(&format!("=== {} ===\n", path.file_name().unwrap_or_default().to_string_lossy()));
        if let Ok(c) = std::fs::read_to_string(&path) {
            content.push_str(&c);
        }
        content.push_str("\n\n");
    }

    if content.is_empty() {
        Ok("No logs found.".to_string())
    } else {
        Ok(content)
    }
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::default().build())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(SidecarState::default())
        .setup(|app| {
            let handle = app.handle().clone();
            let state: State<SidecarState> = handle.state();
            let port_state = state.port.clone();

            // DevTools can be opened with Cmd+Shift+I in development mode

            // Spawn the Python sidecar
            tauri::async_runtime::spawn(async move {
                info!("Starting Python sidecar...");
                info!("Platform: {}", std::env::consts::OS);

                let shell = handle.shell();

                // Create sidecar command with dynamic port (port 0 = auto-assign)
                // IMPORTANT: Pass only the binary name (without path or extension)
                // Tauri will automatically look in externalBin paths from tauri.conf.json
                info!("Creating sidecar command for 'vn-sidecar' with dynamic port");
                let sidecar_command = shell.sidecar("vn-sidecar")
                    .map(|cmd| cmd.args(["--port", "0"]));

                match sidecar_command {
                    Ok(command) => {
                        info!("Sidecar command created successfully, spawning process...");
                        // Spawn the sidecar process
                        match command.spawn() {
                            Ok((mut rx, _child)) => {
                                info!("Python sidecar process spawned successfully");

                                // Listen to stdout to capture the port
                                while let Some(event) = rx.recv().await {
                                    match event {
                                        tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                                            let line_str = String::from_utf8_lossy(&line);
                                            info!("Sidecar stdout: {}", line_str);

                                            // Extract port from "SERVER_PORT=12345" format
                                            if line_str.contains("SERVER_PORT=") {
                                                if let Some(port_str) = line_str.split('=').nth(1) {
                                                    if let Ok(port) = port_str.trim().parse::<u16>() {
                                                        info!("Extracted sidecar port: {}", port);

                                                        // Store the port in state
                                                        let mut port_lock = port_state.lock().unwrap();
                                                        *port_lock = Some(port);

                                                        // Emit event to frontend
                                                        let _ = handle.emit("sidecar-port", port);

                                                        info!("Sidecar port stored and emitted to frontend");
                                                    } else {
                                                        error!("Failed to parse port from: {}", port_str.trim());
                                                    }
                                                } else {
                                                    error!("Failed to extract port from line: {}", line_str);
                                                }
                                            }
                                        }
                                        tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                                            let line_str = String::from_utf8_lossy(&line);
                                            // Python sidecar uses stderr for normal logging, not errors
                                            // Only log as error if it contains actual error keywords
                                            if line_str.to_lowercase().contains("error") || 
                                               line_str.to_lowercase().contains("failed") ||
                                               line_str.to_lowercase().contains("exception") {
                                                error!("Sidecar stderr: {}", line_str);
                                            } else {
                                                info!("Sidecar: {}", line_str);
                                            }
                                        }
                                        tauri_plugin_shell::process::CommandEvent::Error(err) => {
                                            error!("Sidecar error: {}", err);
                                        }
                                        tauri_plugin_shell::process::CommandEvent::Terminated(payload) => {
                                            error!("Sidecar terminated with code: {:?}", payload.code);
                                            let _ = handle.emit("sidecar-terminated", payload.code);
                                            break;
                                        }
                                        _ => {}
                                    }
                                }
                            }
                            Err(e) => {
                                error!("Failed to spawn Python sidecar: {}", e);
                                let _ = handle.emit("sidecar-error", e.to_string());
                            }
                        }
                    }
                    Err(e) => {
                        error!("Failed to create sidecar command: {}", e);
                        error!("Note: For development, you can run the Python server manually:");
                        error!("  cd src-python && ./run.sh");
                        let _ = handle.emit("sidecar-error", e.to_string());
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_sidecar_port, get_log_contents])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

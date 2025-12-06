// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::{Arc, Mutex};
use tauri::{Emitter, Manager, State};
use tauri_plugin_shell::ShellExt;

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

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .manage(SidecarState::default())
        .setup(|app| {
            let handle = app.handle().clone();
            let state: State<SidecarState> = handle.state();
            let port_state = state.port.clone();

            // Spawn the Python sidecar
            tauri::async_runtime::spawn(async move {
                println!("Starting Python sidecar...");

                let shell = handle.shell();

                // Create sidecar command
                let sidecar_command = shell.sidecar("vn-sidecar");

                match sidecar_command {
                    Ok(command) => {
                        // Spawn the sidecar process
                        let (mut rx, _child) = command
                            .spawn()
                            .expect("Failed to spawn Python sidecar");

                        // Listen to stdout to capture the port
                        while let Some(event) = rx.recv().await {
                            match event {
                                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                                    let line_str = String::from_utf8_lossy(&line);
                                    println!("Sidecar stdout: {}", line_str);

                                    // Extract port from "SERVER_PORT=12345" format
                                    if line_str.contains("SERVER_PORT=") {
                                        if let Some(port_str) = line_str.split('=').nth(1) {
                                            if let Ok(port) = port_str.trim().parse::<u16>() {
                                                println!("Extracted sidecar port: {}", port);

                                                // Store the port in state
                                                let mut port_lock = port_state.lock().unwrap();
                                                *port_lock = Some(port);

                                                // Emit event to frontend
                                                let _ = handle.emit("sidecar-port", port);

                                                println!("Sidecar port stored and emitted to frontend");
                                            }
                                        }
                                    }
                                }
                                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                                    let line_str = String::from_utf8_lossy(&line);
                                    eprintln!("Sidecar stderr: {}", line_str);
                                }
                                tauri_plugin_shell::process::CommandEvent::Error(err) => {
                                    eprintln!("Sidecar error: {}", err);
                                }
                                tauri_plugin_shell::process::CommandEvent::Terminated(payload) => {
                                    eprintln!("Sidecar terminated with code: {:?}", payload.code);
                                    break;
                                }
                                _ => {}
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("Failed to create sidecar command: {}", e);
                        eprintln!("Note: For development, you can run the Python server manually:");
                        eprintln!("  cd src-python && ./run.sh");
                    }
                }
            });

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![get_sidecar_port])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

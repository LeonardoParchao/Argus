#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Setup sidecar to launch Python backend
            #[cfg(target_os = "windows")]
            {
                use tauri::utils::config::SidecarOptions;
                let sidecar_path = app.path_resolver()
                    .resolve("backend/python_backend.exe", SidecarOptions::default())
                    .expect("failed to resolve sidecar");
                
                let _child = tauri::api::process::Command::new(sidecar_path)
                    .spawn()
                    .expect("Failed to spawn sidecar");
            }
            
            #[cfg(not(target_os = "windows"))]
            {
                use tauri::utils::config::SidecarOptions;
                let sidecar_path = app.path_resolver()
                    .resolve("backend/python_backend", SidecarOptions::default())
                    .expect("failed to resolve sidecar");
                
                let _child = tauri::api::process::Command::new(sidecar_path)
                    .spawn()
                    .expect("Failed to spawn sidecar");
            }
            
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
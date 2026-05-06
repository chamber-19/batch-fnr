mod commands;

use commands::fnr::{execute_replacements, preview_replacements, scan_folder_for_dwg};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            preview_replacements,
            execute_replacements,
            scan_folder_for_dwg
        ])
        .run(tauri::generate_context!())
        .expect("error while running batch-fnr");
}

use std::fs;
use std::path::PathBuf;

fn main() {
    // Copy sidecar binaries to target directory for development
    let target_os = std::env::var("CARGO_CFG_TARGET_OS").unwrap_or_else(|_| "unknown".to_string());
    let target_arch = std::env::var("CARGO_CFG_TARGET_ARCH").unwrap_or_else(|_| "unknown".to_string());

    // Determine the target triple for the sidecar binary
    let target_triple = match (target_os.as_str(), target_arch.as_str()) {
        ("macos", "aarch64") => "aarch64-apple-darwin",
        ("macos", "x86_64") => "x86_64-apple-darwin",
        ("windows", "x86_64") => "x86_64-pc-windows-msvc",
        ("linux", "x86_64") => "x86_64-unknown-linux-gnu",
        _ => {
            println!("cargo:warning=Unknown target platform: {} {}", target_os, target_arch);
            return tauri_build::build();
        }
    };

    let binary_name = if target_os == "windows" {
        format!("vn-sidecar-{}.exe", target_triple)
    } else {
        format!("vn-sidecar-{}", target_triple)
    };

    // Source: src-tauri/binaries/vn-sidecar-{triple}
    let source = PathBuf::from("binaries").join(&binary_name);

    // Destination: target/{profile}/binaries/vn-sidecar-{triple}
    let target_dir = PathBuf::from(std::env::var("OUT_DIR").unwrap())
        .ancestors()
        .nth(3)
        .unwrap()
        .join("binaries");

    // Create target binaries directory if it doesn't exist
    if let Err(e) = fs::create_dir_all(&target_dir) {
        println!("cargo:warning=Failed to create binaries directory: {}", e);
        return tauri_build::build();
    }

    let dest = target_dir.join(&binary_name);

    // Copy sidecar binary if source exists
    if source.exists() {
        match fs::copy(&source, &dest) {
            Ok(_) => println!("cargo:warning=Copied sidecar binary to {:?}", dest),
            Err(e) => println!("cargo:warning=Failed to copy sidecar binary: {}", e),
        }

        // On Unix, ensure executable permissions
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            if let Ok(metadata) = fs::metadata(&dest) {
                let mut perms = metadata.permissions();
                perms.set_mode(perms.mode() | 0o111);
                let _ = fs::set_permissions(&dest, perms);
            }
        }
    } else {
        println!("cargo:warning=Sidecar binary not found at {:?}. Run 'python src-python/build_sidecar.py' first.", source);
    }

    // Rebuild if source binary changes
    println!("cargo:rerun-if-changed=binaries/{}", binary_name);

    tauri_build::build()
}

fn main() {
    tauri_build::try_build(
        tauri_build::Attributes::new()
            .sidecar("vn-sidecar"),
    )
    .expect("failed to build");
}

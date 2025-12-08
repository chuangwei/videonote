import { invoke } from '@tauri-apps/api/core';

/**
 * 初始化 DevTools 快捷键监听
 * 在打包后的应用中也可以使用以下快捷键打开开发者工具：
 * - macOS: Cmd + Shift + D
 * - Windows/Linux: Ctrl + Shift + D
 */
export function initDevToolsShortcut() {
  window.addEventListener('keydown', (event) => {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
    const modifier = isMac ? event.metaKey : event.ctrlKey;
    
    // Cmd+Shift+D (Mac) 或 Ctrl+Shift+D (Windows/Linux)
    if (modifier && event.shiftKey && event.key.toLowerCase() === 'd') {
      event.preventDefault();
      openDevTools();
    }
  });
}

/**
 * 打开 DevTools
 */
export async function openDevTools() {
  try {
    await invoke('open_devtools');
    console.log('DevTools opened');
  } catch (error) {
    console.error('Failed to open DevTools:', error);
  }
}

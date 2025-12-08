import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import { initDevToolsShortcut } from "./lib/devtools";

// 初始化 DevTools 快捷键（Cmd+Shift+D 或 Ctrl+Shift+D）
initDevToolsShortcut();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

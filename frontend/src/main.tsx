import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import "./demos/ipc";
// If you want use Node.js, the`nodeIntegration` needs to be enabled in the Main process.
// import './demos/node'

async function enableMocking() {
  if (process.env.NODE_ENV === "development") {
    const { worker } = await import("./mocks/browser");
    return worker.start();
  }
}

enableMocking().then(() => {
  ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
});

postMessage({ payload: "removeLoading" }, "*");

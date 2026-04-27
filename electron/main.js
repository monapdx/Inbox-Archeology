const { app, BrowserWindow, dialog, Menu } = require("electron");
const { spawn } = require("child_process");
const path = require("path");
const http = require("http");
const fs = require("fs");

let mainWindow = null;
let backendProcess = null;
let selectedMboxPath = "";

function resolvePython(projectRoot) {
  const candidates = process.platform === "win32"
    ? [
        path.join(projectRoot, ".venv", "Scripts", "python.exe"),
        path.join(projectRoot, ".venv", "Scripts", "python"),
        "python",
        "py"
      ]
    : [
        path.join(projectRoot, ".venv", "bin", "python3"),
        path.join(projectRoot, ".venv", "bin", "python"),
        "python3",
        "python"
      ];

  for (const candidate of candidates) {
    if (path.isAbsolute(candidate)) {
      if (fs.existsSync(candidate)) {
        return candidate;
      }
      continue;
    }
    return candidate;
  }

  return process.platform === "win32" ? "python" : "python3";
}

function buildAppUrl() {
  const url = new URL("http://127.0.0.1:8501");
  if (selectedMboxPath) {
    url.searchParams.set("mbox", selectedMboxPath);
  }
  return url.toString();
}

function waitForServer(url, timeoutMs = 30000) {
  const start = Date.now();

  return new Promise((resolve, reject) => {
    function tryConnect() {
      http
        .get(url, (res) => {
          res.resume();
          resolve();
        })
        .on("error", () => {
          if (Date.now() - start > timeoutMs) {
            reject(new Error("Timed out waiting for Streamlit server."));
            return;
          }
          setTimeout(tryConnect, 500);
        });
    }

    tryConnect();
  });
}

function startBackend() {
  const projectRoot = path.join(__dirname, "..");
  const pythonCmd = resolvePython(projectRoot);
  console.log(`[inbox-archeology] Using Python: ${pythonCmd}`);

  backendProcess = spawn(
    pythonCmd,
    [
      "-m",
      "streamlit",
      "run",
      path.join(projectRoot, "app.py"),
      "--server.headless=true",
      "--server.port=8501",
      "--server.address=127.0.0.1"
    ],
    {
      cwd: projectRoot,
      windowsHide: true,
      stdio: "inherit"
    }
  );

  backendProcess.on("error", (err) => {
    console.error("[inbox-archeology] Failed to start backend process:", err);
  });
}

async function chooseMboxFile() {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "Choose MBOX File",
    properties: ["openFile"],
    filters: [
      { name: "MBOX files", extensions: ["mbox"] },
      { name: "All files", extensions: ["*"] }
    ]
  });

  if (result.canceled || !result.filePaths.length) {
    return;
  }

  selectedMboxPath = result.filePaths[0];

  if (mainWindow) {
    await mainWindow.loadURL(buildAppUrl());
    mainWindow.setTitle(`Inbox Archeology — ${path.basename(selectedMboxPath)}`);
  }
}

function buildMenu() {
  const template = [
    {
      label: "File",
      submenu: [
        {
          label: "Choose MBOX File",
          accelerator: "CmdOrCtrl+O",
          click: async () => {
            await chooseMboxFile();
          }
        },
        { type: "separator" },
        { role: "quit" }
      ]
    },
    {
      label: "View",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 950,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js")
    }
  });

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });
}

app.whenReady().then(async () => {
  buildMenu();
  startBackend();
  createWindow();

  try {
    await waitForServer("http://127.0.0.1:8501");
    await mainWindow.loadURL(buildAppUrl());

    if (!selectedMboxPath) {
      await chooseMboxFile();
    }
  } catch (err) {
    console.error(err);
    await mainWindow.loadURL("data:text/plain,Failed to start local app server.");
  }
});

app.on("before-quit", () => {
  if (backendProcess) {
    backendProcess.kill();
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    app.quit();
  }
});
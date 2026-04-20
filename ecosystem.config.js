const fs = require("fs");
const path = require("path");

const ROOT = __dirname;
const VENV_PY = path.join(ROOT, ".venv", "bin", "python");
const LOGS = path.join(ROOT, "logs");
const CONFIG_PATH = path.join(ROOT, "mcp-config.json");

function loadConfig() {
  try {
    return JSON.parse(fs.readFileSync(CONFIG_PATH, "utf-8"));
  } catch {
    return {};
  }
}

const cfg = loadConfig();
const server = cfg.server || {};
const HOST = server.host || "0.0.0.0";
const PORT = server.port || 3636;

module.exports = {
  apps: [
    {
      name: "paper-search",
      script: VENV_PY,
      args: `-m uvicorn app.main:app --host ${HOST} --port ${PORT}`,
      cwd: path.join(ROOT, "backend"),
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "500M",
      env: {
        PYTHONUNBUFFERED: "1",
      },
      error_file: path.join(LOGS, "paper-search-error.log"),
      out_file: path.join(LOGS, "paper-search-out.log"),
      log_file: path.join(LOGS, "paper-search-combined.log"),
      time: true,
    },
  ],
};

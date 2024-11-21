const isWindows = process.platform === "win32";

module.exports = {
  apps: [
    {
      name: "grass",
      script: "main.py",
      interpreter: isWindows ? "venv\\Scripts\\pythonw.exe" : "venv/bin/python",
      ignore_watch: ["deploy", "\\.git", "*.log"],
      env_pm2_logrotate: {
        retain: "5", // Keep the last 10 rotated log files
        max_size: "5M", // Maximum size of a log file before rotation
        compress: true, // Compress rotated files
      },
    },
  ],
};

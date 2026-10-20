import json
import platform
import shutil
import socket
from datetime import datetime
from pathlib import Path

def run_health_check():
    disk = shutil.disk_usage("/")
    dns_configured = Path("/etc/resolv.conf").exists()

    checks = {
        "operating_system": platform.system(),
        "distribution_kernel": platform.release(),
        "python_version": platform.python_version(),
        "hostname": socket.gethostname(),
        "disk_free_gb": round(disk.free / (1024 ** 3), 2),
        "dns_configured": dns_configured,
        "tools": {
            name: shutil.which(name) is not None
            for name in ["python3", "git", "ssh", "curl"]
        },
    }

    report = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "project": "Linux Migration Health Check",
        "checks": checks,
    }

    Path("report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("=== LINUX MIGRATION HEALTH CHECK ===")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("\nInforme guardado en report.json")

if __name__ == "__main__":
    run_health_check()

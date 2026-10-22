import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Disable Streamlit telemetry and first-run email prompt
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"

try:
    from streamlit.web import cli as stcli
except ImportError:
    import subprocess
    cmd = [
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    subprocess.run(cmd)
    sys.exit(0)

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    sys.argv = [
        "streamlit", "run", app_path,
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    sys.exit(stcli.main())

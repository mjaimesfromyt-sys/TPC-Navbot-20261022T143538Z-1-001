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
        sys.executable, "-m", "streamlit", "run", os.path.join(os.path.dirname(__file__), "app.py"),
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    sys.exit(subprocess.run(cmd).returncode)

if __name__ == "__main__":
    # Streamlit reads its theme from the working directory, including when the
    # launcher is invoked from an IDE or the parent folder.
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    sys.argv = [
        "streamlit", "run", app_path,
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ]
    sys.exit(stcli.main())

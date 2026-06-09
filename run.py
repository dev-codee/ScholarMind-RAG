import subprocess
import sys
import os
import time

def main():
    # Ensure we are in the correct directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Define commands using the current python executable
    # This bypasses the broken Scripts\streamlit.exe launcher by using python -m streamlit
    backend_cmd = [sys.executable, "main.py"]
    
    # Railway sets the PORT environment variable. If not set, default to 8501.
    port = os.environ.get("PORT", "8501")
    frontend_cmd = [
        sys.executable, "-m", "streamlit", "run", "frontend.py", 
        "--server.port", port, 
        "--server.address", "0.0.0.0"
    ]
    
    print("Starting ScholarMind Backend (FastAPI)...")
    backend_process = subprocess.Popen(backend_cmd)
    
    # Give the backend a second to start up before launching the frontend
    time.sleep(2)
    
    print("Starting ScholarMind Frontend (Streamlit)...")
    frontend_process = subprocess.Popen(frontend_cmd)
    
    try:
        # Wait for both processes indefinitely
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down ScholarMind...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()

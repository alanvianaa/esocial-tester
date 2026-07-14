import subprocess
import sys
import os

def install_pyinstaller():
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build():
    install_pyinstaller()
    
    main_script = "main.py"
    executable_name = "eSocial-tester"
    cacert_path = "Cacert.pem"
    
    if not os.path.exists(main_script):
        print(f"Error: '{main_script}' not found.")
        sys.exit(1)
        
    if not os.path.exists(cacert_path):
        print(f"Error: '{cacert_path}' not found.")
        sys.exit(1)

    command = [
        "pyinstaller",
        "--onefile",
        "--console",
        f"--add-data={cacert_path}:.",
        f"--name={executable_name}",
        main_script,
    ]
    
    print(f"Running command: {' '.join(command)}")
    
    try:
        subprocess.check_call(command)
        print("\nBuild successful!")
        print(f"Executable created in dist/{executable_name}{'.exe' if os.name == 'nt' else ''}")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
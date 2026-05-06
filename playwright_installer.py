import subprocess
import os

def install_playwright_browsers():
    """Install Playwright browsers after package installation."""
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0"
    
    print("Installing Playwright system dependencies...")
    subprocess.run(['playwright', 'install', '--with-deps'], check=True)
    
    print("Installing Playwright Chromium browser...")
    subprocess.run(
        ['playwright', 'install', '--force', 'chromium'],
        env={**os.environ, 'PLAYWRIGHT_BROWSERS_PATH': '0'},
        check=True
    )
    print("Playwright installation complete!")

if __name__ == "__main__":
    install_playwright_browsers()
import os
import sys
import platform
import requests
import zipfile
import io
import subprocess
import json

def get_chromedriver_for_chrome136():
    """Download the correct ChromeDriver for Chrome 136 using Chrome for Testing API"""
    print("Detecting system information...")
    system = platform.system()
    if system == "Windows":
        platform_name = "win64"  # Chrome for Testing uses win64 instead of win32
    elif system == "Darwin":  # macOS
        if platform.machine() == "arm64":
            platform_name = "mac-arm64"
        else:
            platform_name = "mac-x64"
    elif system == "Linux":
        platform_name = "linux64"
    else:
        print(f"Unsupported platform: {system}")
        return False
    
    # Get the latest ChromeDriver for Chrome 136 milestone from Chrome for Testing API
    print("Fetching available ChromeDriver versions for Chrome 136...")
    try:
        # Get known good versions from Chrome for Testing API
        known_good_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        response = requests.get(known_good_url)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        versions_data = response.json()
        
        # Find the latest version for Chrome 136
        chrome_136_versions = []
        for version in versions_data.get("versions", []):
            if version.get("version", "").startswith("136."):
                # Check if it has chromedriver downloads
                if "chromedriver" in version.get("downloads", {}):
                    chrome_136_versions.append(version)
        
        if not chrome_136_versions:
            print("No ChromeDriver found for Chrome 136 in the Chrome for Testing API.")
            print("You may need to manually download from: https://chromedriver.chromium.org/downloads")
            return False
        
        # Sort versions and get the latest one
        chrome_136_versions.sort(key=lambda x: x["version"], reverse=True)
        latest_version = chrome_136_versions[0]
        version_number = latest_version["version"]
        
        # Find the download URL for the current platform
        chromedriver_downloads = latest_version.get("downloads", {}).get("chromedriver", [])
        download_url = None
        
        for download in chromedriver_downloads:
            if download.get("platform") == platform_name:
                download_url = download.get("url")
                break
        
        if not download_url:
            print(f"No ChromeDriver download available for {platform_name} platform.")
            return False
        
        print(f"Found ChromeDriver version {version_number} for Chrome 136")
        print(f"URL: {download_url}")
        
        # Download the ChromeDriver zip
        print("Downloading ChromeDriver...")
        response = requests.get(download_url)
        response.raise_for_status()
        
        # Get the current directory
        destination = os.path.dirname(os.path.abspath(__file__))
        
        # Extract the zip
        print("Extracting ChromeDriver...")
        z = zipfile.ZipFile(io.BytesIO(response.content))
        z.extractall(destination)
        
        # The zip contains a folder structure, we need to move the executable to the root
        chromedriver_folder = os.path.join(destination, f"chromedriver-{platform_name}")
        chromedriver_name = "chromedriver.exe" if system == "Windows" else "chromedriver"
        chromedriver_path_in_zip = os.path.join(chromedriver_folder, chromedriver_name)
        chromedriver_path_dest = os.path.join(destination, chromedriver_name)
        
        # Move the chromedriver executable to the root directory
        if os.path.exists(chromedriver_path_dest):
            print(f"Removing existing ChromeDriver at {chromedriver_path_dest}")
            os.remove(chromedriver_path_dest)
        
        # Make sure the source file exists
        if os.path.exists(chromedriver_path_in_zip):
            import shutil
            shutil.move(chromedriver_path_in_zip, chromedriver_path_dest)
            print(f"Moved ChromeDriver to {chromedriver_path_dest}")
        else:
            # If the expected path is not found, try to find chromedriver in the extracted files
            print("ChromeDriver not found at expected location, searching for it...")
            for root, _, files in os.walk(destination):
                for file in files:
                    if file == chromedriver_name:
                        file_path = os.path.join(root, file)
                        if file_path != chromedriver_path_dest:
                            shutil.move(file_path, chromedriver_path_dest)
                            print(f"Found and moved ChromeDriver to {chromedriver_path_dest}")
                            break
        
        # Make executable on Unix-based systems
        if system in ["Darwin", "Linux"]:
            print("Setting executable permissions...")
            subprocess.check_call(['chmod', '+x', chromedriver_path_dest])
        
        # Clean up the extracted folder
        if os.path.exists(chromedriver_folder):
            import shutil
            shutil.rmtree(chromedriver_folder)
        
        print(f"ChromeDriver successfully installed at: {chromedriver_path_dest}")
        return True
    except Exception as e:
        print(f"Error downloading ChromeDriver: {str(e)}")
        return False

if __name__ == "__main__":
    print("Setting up ChromeDriver for Chrome 136.0.7103.93...")
    success = get_chromedriver_for_chrome136()
    
    if success:
        print("\nSetup complete! You can now run the AI Search Assistant.")
    else:
        print("\nSetup failed. You can try to download ChromeDriver manually from:")
        print("https://chromedriver.chromium.org/downloads")
        print("or check Chrome for Testing: https://googlechromelabs.github.io/chrome-for-testing/") 
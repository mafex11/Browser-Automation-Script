import os
import sys
import platform
import re
import subprocess
import requests
import zipfile
import io
import json
import winreg

def get_chrome_version():
    """Detect installed Chrome version across different platforms"""
    print("Detecting installed Chrome version...")
    version = None
    system = platform.system()
    
    try:
        if system == "Windows":
            # Try registry method first
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                return version
            except:
                # Alternative methods for Windows
                try:
                    paths = [
                        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
                        r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
                        os.path.expanduser(r'~\AppData\Local\Google\Chrome\Application\chrome.exe')
                    ]
                    
                    for path in paths:
                        if os.path.exists(path):
                            # Use PowerShell to get version info
                            cmd = f'powershell -command "(Get-Item \'{path}\').VersionInfo.ProductVersion"'
                            output = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
                            return output
                    
                    # If direct path check fails, try wmic
                    process = subprocess.Popen(
                        ['wmic', 'datafile', 'where', 'name="C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe"', 'get', 'Version', '/value'],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
                    )
                    output, _ = process.communicate()
                    match = re.search(r'Version=(.+)', output.decode('utf-8', errors='ignore'))
                    if match:
                        return match.group(1).strip()
                except Exception as e:
                    print(f"Error detecting Chrome version via file path: {e}")
        
        elif system == "Darwin":  # macOS
            try:
                process = subprocess.Popen(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                output, _ = process.communicate()
                match = re.search(r'Google Chrome ([\d.]+)', output.decode('utf-8'))
                if match:
                    return match.group(1)
            except:
                # Try alternative command
                try:
                    output = subprocess.check_output(['/usr/bin/defaults', 'read', '/Applications/Google Chrome.app/Contents/Info.plist', 'CFBundleShortVersionString']).decode('utf-8')
                    return output.strip()
                except:
                    pass
        
        elif system == "Linux":
            try:
                process = subprocess.Popen(
                    ['google-chrome', '--version'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                output, _ = process.communicate()
                match = re.search(r'Google Chrome ([\d.]+)', output.decode('utf-8'))
                if match:
                    return match.group(1)
            except:
                # Try alternative commands
                try:
                    output = subprocess.check_output(['chromium', '--version']).decode('utf-8')
                    match = re.search(r'Chromium ([\d.]+)', output)
                    if match:
                        return match.group(1)
                except:
                    pass
                    
        # If we couldn't detect automatically, ask the user
        if not version:
            print("\nUnable to automatically detect Chrome version.")
            print("Please check your Chrome version by going to chrome://version in your browser")
            user_input = input("\nEnter your Chrome version (e.g., 136.0.7103.93): ")
            if user_input:
                return user_input.strip()
    
    except Exception as e:
        print(f"Error detecting Chrome version: {e}")
    
    return None

def get_chromedriver_for_version(chrome_version):
    """Download the correct ChromeDriver for the detected Chrome version using Chrome for Testing API"""
    # Extract major version number
    major_version = chrome_version.split('.')[0] if chrome_version else None
    
    if not major_version:
        print("Could not determine Chrome major version.")
        return False
    
    print(f"Looking for ChromeDriver compatible with Chrome {major_version}.x")
    
    # Determine system platform for download
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
    
    try:
        # Get known good versions from Chrome for Testing API
        known_good_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
        response = requests.get(known_good_url)
        response.raise_for_status()
        
        versions_data = response.json()
        
        # Find versions matching our major version
        matching_versions = []
        for version in versions_data.get("versions", []):
            if version.get("version", "").startswith(f"{major_version}."):
                # Check if it has chromedriver downloads
                if "chromedriver" in version.get("downloads", {}):
                    matching_versions.append(version)
        
        if not matching_versions:
            print(f"No ChromeDriver found for Chrome {major_version} in the Chrome for Testing API.")
            # Try fallback for older versions
            return download_chromedriver_fallback(major_version, platform_name)
        
        # Sort versions and get the latest one for this major version
        matching_versions.sort(key=lambda x: x["version"], reverse=True)
        latest_version = matching_versions[0]
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
        
        print(f"Found ChromeDriver version {version_number} for Chrome {major_version}")
        print(f"URL: {download_url}")
        
        # Download and install the driver
        return download_and_install_chromedriver(download_url, platform_name, system)
    
    except Exception as e:
        print(f"Error while fetching ChromeDriver: {str(e)}")
        # Try fallback method
        return download_chromedriver_fallback(major_version, platform_name)

def download_chromedriver_fallback(major_version, platform_name):
    """Fallback method for older Chrome versions or when the API fails"""
    print("Trying fallback method to download ChromeDriver...")
    
    system = platform.system()
    platform_name_legacy = platform_name
    
    # Map new platform names to legacy format
    if platform_name == "win64":
        platform_name_legacy = "win32"  # Legacy downloads use win32 naming
    elif platform_name == "mac-x64":
        platform_name_legacy = "mac64"
    elif platform_name == "mac-arm64":
        platform_name_legacy = "mac64_m1"  # Older naming for Apple Silicon
    
    try:
        # Try to get the latest version for this major version
        release_url = f"https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{major_version}"
        response = requests.get(release_url)
        
        if response.status_code == 200:
            driver_version = response.text.strip()
            download_url = f"https://chromedriver.storage.googleapis.com/{driver_version}/chromedriver_{platform_name_legacy}.zip"
            
            print(f"Found legacy ChromeDriver version {driver_version} for Chrome {major_version}")
            print(f"URL: {download_url}")
            
            return download_and_install_chromedriver(download_url, platform_name, system, is_legacy=True)
        else:
            print(f"Couldn't find a compatible ChromeDriver for Chrome {major_version}.")
            print("Try downloading manually from: https://chromedriver.chromium.org/downloads")
            return False
        
    except Exception as e:
        print(f"Error in fallback ChromeDriver download: {str(e)}")
        return False

def download_and_install_chromedriver(download_url, platform_name, system, is_legacy=False):
    """Download and install ChromeDriver from the given URL"""
    try:
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
        
        chromedriver_name = "chromedriver.exe" if system == "Windows" else "chromedriver"
        chromedriver_path_dest = os.path.join(destination, chromedriver_name)
        
        # Remove existing ChromeDriver if present
        if os.path.exists(chromedriver_path_dest):
            print(f"Removing existing ChromeDriver at {chromedriver_path_dest}")
            os.remove(chromedriver_path_dest)
        
        # For newer Chrome for Testing downloads, the zip contains a folder structure
        if not is_legacy:
            chromedriver_folder = os.path.join(destination, f"chromedriver-{platform_name}")
            chromedriver_path_in_zip = os.path.join(chromedriver_folder, chromedriver_name)
        else:
            # Legacy downloads have the executable directly in the zip
            chromedriver_path_in_zip = os.path.join(destination, chromedriver_name)
        
        # Make sure the source file exists
        if os.path.exists(chromedriver_path_in_zip):
            import shutil
            shutil.move(chromedriver_path_in_zip, chromedriver_path_dest)
            print(f"Moved ChromeDriver to {chromedriver_path_dest}")
        else:
            # If the expected path is not found, try to find chromedriver in the extracted files
            print("ChromeDriver not found at expected location, searching for it...")
            found = False
            for root, _, files in os.walk(destination):
                for file in files:
                    if file == chromedriver_name:
                        file_path = os.path.join(root, file)
                        if file_path != chromedriver_path_dest:
                            import shutil
                            shutil.move(file_path, chromedriver_path_dest)
                            print(f"Found and moved ChromeDriver to {chromedriver_path_dest}")
                            found = True
                            break
                if found:
                    break
            
            if not found:
                print("Could not find ChromeDriver executable in the downloaded package.")
                return False
        
        # Make executable on Unix-based systems
        if system in ["Darwin", "Linux"]:
            print("Setting executable permissions...")
            subprocess.check_call(['chmod', '+x', chromedriver_path_dest])
        
        # Clean up any extracted folders that might remain
        for item in os.listdir(destination):
            item_path = os.path.join(destination, item)
            if os.path.isdir(item_path) and "chromedriver-" in item:
                import shutil
                shutil.rmtree(item_path)
        
        print(f"ChromeDriver successfully installed at: {chromedriver_path_dest}")
        return True
    
    except Exception as e:
        print(f"Error downloading and installing ChromeDriver: {str(e)}")
        return False

def main():
    print("ChromeDriver Auto-Downloader")
    print("============================\n")
    
    # Step 1: Detect Chrome version
    chrome_version = get_chrome_version()
    
    if not chrome_version:
        print("Could not detect Chrome version. Please install Chrome and try again.")
        return
    
    print(f"Detected Chrome version: {chrome_version}")
    
    # Step 2: Download matching ChromeDriver
    success = get_chromedriver_for_version(chrome_version)
    
    if success:
        print("\nSetup complete! You can now run the AI Search Assistant.")
    else:
        print("\nSetup failed. You can try manually downloading ChromeDriver from:")
        print("- Chrome for Testing: https://googlechromelabs.github.io/chrome-for-testing/")
        print("- ChromeDriver: https://chromedriver.chromium.org/downloads")
        print(f"\nMake sure to download a version compatible with Chrome {chrome_version}")

if __name__ == "__main__":
    main() 
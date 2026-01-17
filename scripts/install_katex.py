import os
import io
import json
import urllib.request
import zipfile
import shutil
import ssl

def get_latest_katex_url():
    url = "https://api.github.com/repos/KaTeX/KaTeX/releases/latest"
    req = urllib.request.Request(url, headers={'User-Agent': 'python-urllib'})
    try:
        # Create an SSL context that ignores certificate verification errors
        # This is sometimes needed in certain Docker environments or proxies
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.load(response)
            for asset in data.get('assets', []):
                if asset['name'] == 'katex.zip':
                    return asset['browser_download_url']
    except Exception as e:
        print(f"Error fetching latest release: {e}")
        return None
    return None

def main():
    print("Finding latest KaTeX release...")
    download_url = get_latest_katex_url()
    if not download_url:
        print("Could not find katex.zip in latest release.")
        exit(1)
    
    print(f"Downloading {download_url}...")
    req = urllib.request.Request(download_url, headers={'User-Agent': 'python-urllib'})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    with urllib.request.urlopen(req, context=ctx) as response:
        zip_content = response.read()
    
    print("Extracting...")
    target_base = "mkdocs-material/material/templates/assets"
    
    # Check if repo root exists (sanity check)
    if not os.path.exists("mkdocs-material"):
        print("Error: mkdocs-material directory not found!")
        exit(1)

    # Create target directory if it doesn't exist
    if not os.path.exists(target_base):
            print(f"Target directory {target_base} does not exist. Creating it...")
            os.makedirs(target_base, exist_ok=True)

    # Destination for 'katex' dir (mkdocs-material/material/templates/assets/katex)
    destination = os.path.join(target_base, "katex")
    if os.path.exists(destination):
        shutil.rmtree(destination)
    
    # Unzip
    with zipfile.ZipFile(io.BytesIO(zip_content)) as z:
        # We want to extract the contents of the internal 'katex/' folder 
        # to target_base/katex/.
        # Standard unzip of 'katex/file' to target_base results in target_base/katex/file.
        # So check if zip has 'katex/' prefix.
        has_katex_prefix = any(f.filename.startswith("katex/") for f in z.infolist())
        
        if has_katex_prefix:
            z.extractall(target_base)
        else:
            # If zip structure is flat or different, extract to destination directly
            # This handles cases where zip might not have the top-level folder
            z.extractall(destination)
            
        print(f"Extracted to {target_base}")
    
    # Handle katex.render.js
    # Logic: "把这个项目里的 assets/katex.render.js 放到 template/assets 直接下"
    # Assuming the local `assets/katex.render.js` has been copied to `/app/assets/katex.render.js`
    local_asset = "assets/katex.render.js" 
    target_js = os.path.join(target_base, "katex.render.js")
    
    if os.path.exists(local_asset):
        print(f"Moving {local_asset} to {target_js}")
        shutil.copy(local_asset, target_js)
    else:
        print(f"Warning: {local_asset} not found in /app/assets/.")
        # Try to find it in current dict just in case
        if os.path.exists("katex.render.js"):
             shutil.copy("katex.render.js", target_js)

if __name__ == "__main__":
    main()

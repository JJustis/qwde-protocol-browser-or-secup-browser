"""
QWDE Protocol - Site Packager
Packages QWDE sites into standard website folder structure
"""

import os
import json
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Optional
import re


class SitePackager:
    """Packages QWDE sites into website folders"""
    
    def __init__(self, template_dir: str = 'website_template'):
        self.template_dir = template_dir
        self.output_dir = 'packaged_sites'
        
        # Ensure directories exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def package_site(self, domain: str, content: str, 
                    metadata: dict = None) -> str:
        """
        Package a site into a website folder
        
        Args:
            domain: Site domain (e.g., 'mysite.qwde')
            content: Site HTML/text content
            metadata: Additional metadata (fwild, version, etc.)
        
        Returns:
            Path to packaged site folder
        """
        if metadata is None:
            metadata = {}
        
        # Create site folder
        safe_domain = re.sub(r'[^\w\-_]', '_', domain)
        site_folder = os.path.join(self.output_dir, safe_domain)
        
        if os.path.exists(site_folder):
            shutil.rmtree(site_folder)
        os.makedirs(site_folder)
        os.makedirs(os.path.join(site_folder, 'css'), exist_ok=True)
        os.makedirs(os.path.join(site_folder, 'js'), exist_ok=True)
        os.makedirs(os.path.join(site_folder, 'assets'), exist_ok=True)
        
        # Prepare metadata
        site_metadata = {
            'domain': domain,
            'fwild': metadata.get('fwild', 0),
            'version': metadata.get('version', 1),
            'protocol_prefix': metadata.get('protocol_prefix', 'qwde'),
            'created_at': datetime.now().isoformat(),
            'content_hash': hashlib.sha256(content.encode()).hexdigest()
        }
        
        # Process content
        processed_content = self._process_content(content, site_folder)
        
        # Generate index.html from template
        index_html = self._generate_index_html(processed_content, site_metadata)
        
        with open(os.path.join(site_folder, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        # Copy template assets
        self._copy_template_assets(site_folder)
        
        # Save metadata
        with open(os.path.join(site_folder, 'qwde_metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(site_metadata, f, indent=2)
        
        # Save original content
        with open(os.path.join(site_folder, 'original_content.txt'), 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ Packaged site: {domain}")
        print(f"  Output: {site_folder}")
        print(f"  Fwild: {site_metadata['fwild']}")
        print(f"  Version: {site_metadata['version']}")
        
        return site_folder
    
    def _process_content(self, content: str, site_folder: str) -> str:
        """Process content and extract assets"""
        # If content is plain text, wrap in basic HTML
        if not content.strip().startswith('<'):
            content = f"""
            <div class="container">
                <h1>Site Content</h1>
                <div class="content">
                    {content.replace(chr(10), '<br>')}
                </div>
            </div>
            """
        
        # Extract and save images (data URLs)
        img_pattern = r'data:image/(png|jpg|jpeg|gif);base64,([A-Za-z0-9+/=]+)'
        matches = re.findall(img_pattern, content)
        
        for i, (img_type, img_data) in enumerate(matches):
            img_filename = f'image_{i}.{img_type}'
            img_path = os.path.join(site_folder, 'assets', img_filename)
            
            import base64
            with open(img_path, 'wb') as f:
                f.write(base64.b64decode(img_data))
            
            # Replace data URL with relative path
            content = content.replace(
                f'data:image/{img_type};base64,{img_data}',
                f'assets/{img_filename}'
            )
        
        return content
    
    def _generate_index_html(self, content: str, metadata: dict) -> str:
        """Generate index.html from template"""
        template_path = os.path.join(self.template_dir, 'index.html')
        
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        else:
            # Default template if file not found
            template = """<!DOCTYPE html>
<html>
<head>
    <title>{{SITE_TITLE}}</title>
    <meta charset="UTF-8">
</head>
<body>
    {{SITE_CONTENT}}
</body>
</html>"""
        
        # Replace placeholders
        html = template
        html = html.replace('{{SITE_TITLE}}', metadata['domain'])
        html = html.replace('{{DOMAIN}}', metadata['domain'])
        html = html.replace('{{FWILD}}', str(metadata['fwild']))
        html = html.replace('{{VERSION}}', str(metadata['version']))
        html = html.replace('{{PROTOCOL_PREFIX}}', metadata['protocol_prefix'])
        html = html.replace('{{CREATED_AT}}', metadata['created_at'])
        html = html.replace('{{SITE_CONTENT}}', content)
        
        return html
    
    def _copy_template_assets(self, site_folder: str):
        """Copy CSS, JS, and other assets from template"""
        # Copy CSS
        css_src = os.path.join(self.template_dir, 'css', 'style.css')
        css_dest = os.path.join(site_folder, 'css', 'style.css')
        
        if os.path.exists(css_src):
            shutil.copy2(css_src, css_dest)
        else:
            # Create default CSS
            os.makedirs(os.path.join(site_folder, 'css'), exist_ok=True)
            with open(css_dest, 'w', encoding='utf-8') as f:
                f.write("body { font-family: sans-serif; padding: 20px; }")
        
        # Copy JS
        js_src = os.path.join(self.template_dir, 'js', 'main.js')
        js_dest = os.path.join(site_folder, 'js', 'main.js')
        
        if os.path.exists(js_src):
            shutil.copy2(js_src, js_dest)
        else:
            # Create default JS
            os.makedirs(os.path.join(site_folder, 'js'), exist_ok=True)
            with open(js_dest, 'w', encoding='utf-8') as f:
                f.write("// QWDE Site JavaScript\n")
    
    def package_to_zip(self, site_folder: str) -> str:
        """Package site folder into ZIP file"""
        import zipfile
        
        zip_path = site_folder + '.zip'
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(site_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(site_folder))
                    zipf.write(file_path, arcname)
        
        print(f"✓ Created ZIP: {zip_path}")
        return zip_path
    
    def export_all_sites(self) -> list:
        """Export all packaged sites to ZIP files"""
        zip_files = []
        
        for site_folder in os.listdir(self.output_dir):
            full_path = os.path.join(self.output_dir, site_folder)
            if os.path.isdir(full_path):
                zip_path = self.package_to_zip(full_path)
                zip_files.append(zip_path)
        
        return zip_files


# Test the packager
if __name__ == '__main__':
    packager = SitePackager()
    
    # Test packaging
    test_content = """
    <h1>Test QWDE Site</h1>
    <p>This is a test site packaged by QWDE Protocol.</p>
    <ul>
        <li>Feature 1</li>
        <li>Feature 2</li>
        <li>Feature 3</li>
    </ul>
    """
    
    site_path = packager.package_site(
        domain='test.qwde',
        content=test_content,
        metadata={
            'fwild': 1,
            'version': 1,
            'protocol_prefix': 'qwde'
        }
    )
    
    print(f"\nSite packaged to: {site_path}")
    
    # Create ZIP
    zip_path = packager.package_to_zip(site_path)
    print(f"ZIP created: {zip_path}")

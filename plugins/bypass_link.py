# file name: bypass_link.py
import aiohttp
import re
from urllib.parse import urlparse, parse_qs
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import asyncio

ADMIN_USER_ID = Config.ADMIN

# Common shortener patterns
SHORTENER_DOMAINS = [
    "gplinks.in", "gplinks.com", "gplink.co", "gplink.in",
    "linkvertise.com", "linkvertise.net",
    "droplink.co", "droplink.in",
    "earn4link.in", "earn.money",
    "gtlinks.me", "gplinks.me",
    "short2url.in", "short2url.com",
    "shorturl.at", "tinyurl.com",
    "bit.ly", "goo.gl", "ow.ly",
    "adf.ly", "bc.vc", "shorte.st",
    "ouo.io", "ouo.press",
    "g.link", "gyanilinks.com",
    "za.gl", "urlshortx.com"
]

class LinkBypasser:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    async def get_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self.headers)
        return self.session
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    def is_shortener_link(self, url):
        """Check if the URL is from a known shortener"""
        try:
            domain = urlparse(url).netloc.lower()
            # Remove www. prefix if present
            domain = domain.replace('www.', '')
            
            # Check against known shortener domains
            for short_domain in SHORTENER_DOMAINS:
                if domain == short_domain or domain.endswith(f'.{short_domain}'):
                    return True
            
            # Also check for patterns like link shorteners
            if any(pattern in domain for pattern in ['link', 'short', 'tiny', 'bit', 'goo', 'ow', 'adf', 'shorte', 'ouo']):
                return True
                
            return False
        except:
            return False
    
    async def bypass_gplinks(self, url):
        """Bypass GPLinks shortener"""
        try:
            session = await self.get_session()
            
            # First, get the initial page
            async with session.get(url, allow_redirects=False) as response:
                if response.status in [301, 302, 303, 307, 308]:
                    location = response.headers.get('Location', '')
                    if location:
                        return location
                
                html = await response.text()
                
                # Try to find JavaScript redirect
                patterns = [
                    r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                    r'window\.location\s*=\s*["\']([^"\']+)["\']',
                    r'location\.href\s*=\s*["\']([^"\']+)["\']',
                    r'<meta[^>]*?url=([^"\'>]+)',
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?id=["\']get_link["\']',
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?class=["\']redirect["\']',
                    r'document\.getElementById\(["\']\w+["\']\)\.href\s*=\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        found_url = match.group(1)
                        if not found_url.startswith(('http://', 'https://')):
                            # Construct full URL
                            parsed = urlparse(url)
                            found_url = f"{parsed.scheme}://{parsed.netloc}{found_url}"
                        return found_url
                
                # Try to find form with action
                form_pattern = r'<form[^>]*?action=["\']([^"\']+)["\'][^>]*?>'
                form_match = re.search(form_pattern, html, re.IGNORECASE)
                if form_match:
                    form_action = form_match.group(1)
                    if form_action:
                        return await self.bypass_gplinks(f"{urlparse(url).scheme}://{urlparse(url).netloc}{form_action}")
            
            return url
        except Exception as e:
            print(f"Error bypassing GPLinks: {e}")
            return url
    
    async def bypass_linkvertise(self, url):
        """Bypass Linkvertise shortener"""
        try:
            session = await self.get_session()
            
            # Add referer header
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.google.com/'
            
            async with session.get(url, headers=headers, allow_redirects=False) as response:
                # Follow redirects manually
                if response.status in [301, 302, 303, 307, 308]:
                    location = response.headers.get('Location', '')
                    if location:
                        if not location.startswith(('http://', 'https://')):
                            parsed = urlparse(url)
                            location = f"{parsed.scheme}://{parsed.netloc}{location}"
                        return await self.bypass_linkvertise(location)
                
                html = await response.text()
                
                # Look for bypass methods in Linkvertise
                # Method 1: Look for direct link in script
                script_patterns = [
                    r'"direct_link":"([^"]+)"',
                    r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?class=["\']btn-primary["\']',
                    r'https?://[^\s"\']+\.(mp4|m3u8|mkv|avi|mov)[^\s"\']*'
                ]
                
                for pattern in script_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        if 'linkvertise' not in match.lower() and match.startswith('http'):
                            return match
                
                # Method 2: Try to find iframe source
                iframe_pattern = r'<iframe[^>]*?src=["\']([^"\']+)["\']'
                iframe_match = re.search(iframe_pattern, html, re.IGNORECASE)
                if iframe_match:
                    iframe_src = iframe_match.group(1)
                    if iframe_src.startswith('http'):
                        return await self.bypass_linkvertise(iframe_src)
            
            return url
        except Exception as e:
            print(f"Error bypassing Linkvertise: {e}")
            return url
    
    async def bypass_ouo(self, url):
        """Bypass Ouo.io shortener"""
        try:
            session = await self.get_session()
            
            # First request to get the page
            async with session.get(url, allow_redirects=False) as response:
                html = await response.text()
                
                # Look for form data
                form_pattern = r'<form[^>]*?action=["\']([^"\']+)["\'][^>]*?>([\s\S]*?)</form>'
                form_match = re.search(form_pattern, html, re.IGNORECASE)
                
                if form_match:
                    form_action = form_match.group(1)
                    form_content = form_match.group(2)
                    
                    # Extract all input fields
                    inputs = {}
                    input_pattern = r'<input[^>]*?name=["\']([^"\']+)["\'][^>]*?value=["\']([^"\']*)["\']'
                    for name, value in re.findall(input_pattern, form_content):
                        inputs[name] = value
                    
                    # Also look for hidden inputs without value
                    hidden_pattern = r'<input[^>]*?type=["\']hidden["\'][^>]*?name=["\']([^"\']+)["\']'
                    hidden_matches = re.findall(hidden_pattern, form_content)
                    for name in hidden_matches:
                        if name not in inputs:
                            inputs[name] = ""
                    
                    # Submit the form
                    if form_action and inputs:
                        if not form_action.startswith('http'):
                            parsed = urlparse(url)
                            form_action = f"{parsed.scheme}://{parsed.netloc}{form_action}"
                        
                        async with session.post(form_action, data=inputs, allow_redirects=False) as post_response:
                            if post_response.status in [301, 302, 303, 307, 308]:
                                location = post_response.headers.get('Location', '')
                                if location:
                                    return location
            
            return url
        except Exception as e:
            print(f"Error bypassing Ouo: {e}")
            return url
    
    async def bypass_generic(self, url):
        """Generic bypass method for unknown shorteners"""
        try:
            session = await self.get_session()
            
            # Try to follow all redirects
            async with session.get(url, allow_redirects=True) as response:
                final_url = str(response.url)
                
                # If final URL is different from original, return it
                if final_url != url and not self.is_shortener_link(final_url):
                    return final_url
                
                # Try to get from page content
                html = await response.text()
                
                # Look for common redirect patterns
                patterns = [
                    r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                    r'window\.location\s*=\s*["\']([^"\']+)["\']',
                    r'location\.href\s*=\s*["\']([^"\']+)["\']',
                    r'<meta[^>]*?http-equiv=["\']refresh["\'][^>]*?content=["\'][^"\']*?url=([^"\'>]+)',
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?(id|class)=["\'](get_link|redirect|skip|continue|proceed)["\']',
                    r'"url":"([^"]+)"',
                    r'var\s+url\s*=\s*["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('http'):
                            return match
                        elif match.startswith('/'):
                            parsed = urlparse(url)
                            return f"{parsed.scheme}://{parsed.netloc}{match}"
            
            return url
        except Exception as e:
            print(f"Error in generic bypass: {e}")
            return url
    
    async def bypass_url(self, url):
        """Main bypass function - detects shortener type and applies appropriate bypass"""
        if not self.is_shortener_link(url):
            return url, False  # Not a shortener link
        
        original_url = url
        
        try:
            domain = urlparse(url).netloc.lower().replace('www.', '')
            
            # Apply specific bypass based on domain
            if 'gplinks' in domain:
                result = await self.bypass_gplinks(url)
            elif 'linkvertise' in domain:
                result = await self.bypass_linkvertise(url)
            elif 'ouo' in domain:
                result = await self.bypass_ouo(url)
            else:
                result = await self.bypass_generic(url)
            
            # If result is same as input, try recursive bypass
            if result == url or self.is_shortener_link(result):
                # Try one more time with generic method
                result = await self.bypass_generic(url)
            
            success = result != url and not self.is_shortener_link(result)
            return result, success
            
        except Exception as e:
            print(f"Error in bypass_url: {e}")
            return url, False

# Global bypasser instance
bypasser = LinkBypasser()

@Client.on_message(filters.command("link") & filters.user(ADMIN_USER_ID))
async def bypass_link_command(client, message: Message):
    """Admin command to bypass shortener links"""
    if len(message.command) < 2:
        await message.reply_text(
            "**Usage:** `/link <shortener_url>`\n\n"
            "**Example:** `/link https://gplinks.in/xyz`\n"
            "**Multiple links:** `/link https://link1 https://link2`"
        )
        return
    
    # Extract URLs from message
    urls = []
    for arg in message.command[1:]:
        if arg.startswith(('http://', 'https://')):
            urls.append(arg)
        elif ' ' in arg:
            # Handle case where URLs might be separated by spaces
            urls.extend([u for u in arg.split() if u.startswith(('http://', 'https://'))])
    
    if not urls:
        await message.reply_text("❌ No valid URLs found. Please provide valid http:// or https:// links.")
        return
    
    processing_msg = await message.reply_text(f"⏳ Processing {len(urls)} link(s)...")
    
    results = []
    successful = 0
    
    for url in urls:
        try:
            # Check if it's a shortener link
            if not bypasser.is_shortener_link(url):
                results.append(f"❌ `{url}`\n   └ Not a shortener link")
                continue
            
            # Bypass the link
            original_url, success = await bypasser.bypass_url(url)
            
            if success:
                results.append(f"✅ `{url}`\n   └ **Original:** `{original_url}`")
                successful += 1
            else:
                results.append(f"❌ `{url}`\n   └ Failed to bypass")
        
        except Exception as e:
            results.append(f"⚠️ `{url}`\n   └ Error: {str(e)[:50]}...")
    
    # Format results
    result_text = f"**📊 Link Bypass Results**\n\n"
    result_text += f"• Total links: {len(urls)}\n"
    result_text += f"• Successfully bypassed: {successful}\n"
    result_text += f"• Failed: {len(urls) - successful}\n\n"
    
    if results:
        result_text += "\n".join(results[:10])  # Show first 10 results
    
    if len(results) > 10:
        result_text += f"\n\n... and {len(results) - 10} more results"
    
    await processing_msg.edit_text(result_text)

@Client.on_message(filters.command("shorteners") & filters.user(ADMIN_USER_ID))
async def list_shorteners_command(client, message: Message):
    """List all supported shortener domains"""
    domains_text = "**📋 Supported Shortener Domains:**\n\n"
    
    # Group domains for better display
    grouped_domains = {}
    for domain in SHORTENER_DOMAINS:
        first_letter = domain[0].upper()
        if first_letter not in grouped_domains:
            grouped_domains[first_letter] = []
        grouped_domains[first_letter].append(domain)
    
    for letter in sorted(grouped_domains.keys()):
        domains_text += f"**{letter}:**\n"
        domains = sorted(grouped_domains[letter])
        for i in range(0, len(domains), 3):
            row = domains[i:i+3]
            domains_text += "  " + "  |  ".join(f"`{d}`" for d in row) + "\n"
        domains_text += "\n"
    
    domains_text += f"\n**Total:** {len(SHORTENER_DOMAINS)} domains supported"
    
    await message.reply_text(domains_text)

@Client.on_message(filters.command("addshortener") & filters.user(ADMIN_USER_ID))
async def add_shortener_command(client, message: Message):
    """Add a new shortener domain to the list"""
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/addshortener <domain>`\n\n**Example:** `/addshortener example.com`")
        return
    
    domain = message.command[1].lower().strip()
    
    # Remove http:// or https:// if present
    if domain.startswith(('http://', 'https://')):
        from urllib.parse import urlparse
        parsed = urlparse(domain)
        domain = parsed.netloc
    
    # Remove www. prefix
    domain = domain.replace('www.', '')
    
    if domain in SHORTENER_DOMAINS:
        await message.reply_text(f"`{domain}` is already in the list.")
    else:
        SHORTENER_DOMAINS.append(domain)
        await message.reply_text(f"✅ Added `{domain}` to shortener domains list.")

# Clean up session on bot shutdown
async def cleanup():
    await bypasser.close_session()

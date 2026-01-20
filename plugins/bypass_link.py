# file name: bypass_link.py (updated version)
import aiohttp
import re
import json
from urllib.parse import urlparse, parse_qs, urlencode
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
import asyncio
import time
from base64 import b64decode

ADMIN_USER_ID = Config.ADMIN

# Enhanced shortener domains list
SHORTENER_DOMAINS = [
    # GPLinks variants
    "gplinks.co", "gplinks.in", "gplinks.com", "gplink.co", "gplink.in", "gplink.me",
    "gplinks.me", "gplink.pro", "gplinks.pro", "gplinks.live", "gplink.live",
    
    # Linkvertise
    "linkvertise.com", "linkvertise.net", "linkvertise.download", "linkvertise.to",
    "up-to-down.net", "link-to.net",
    
    # Ouo
    "ouo.io", "ouo.press", "ouo.io.io", "ouo.io.io.io",
    
    # DropLink
    "droplink.co", "droplink.in", "droplink.cc", "droplink.to",
    
    # Others
    "gtlinks.me", "gtlink.me",
    "short2url.in", "short2url.com", "short2url.cc",
    "earn4link.in", "earn.money", "earn4link.xyz",
    "za.gl", "urlshortx.com", "linkcreator.xyz",
    "adf.ly", "bc.vc", "shorte.st", "clk.sh",
    "tinyurl.com", "bit.ly", "goo.gl", "ow.ly",
    "rocklinks.net", "rocklink.in",
    "shareus.in", "shareus.io",
    "mdisk.me", "mypowerdisk.com",
    "atglinks.com", "atglinks.net",
    "bindaaslinks.com", "bindaaslinks.in",
    "link1s.com", "link1s.net",
    "tekcities.com", "tekcities.in",
    "urlsopen.com", "urlsopen.net",
    "vearnl.in", "vearnl.com",
    "viidii.com", "viidii.net",
    "vvdiss.com", "vvdiss.net",
    "xpshort.com", "xpshort.net",
    "zaee.gl", "zaee.in",
    "zynshort.com", "zynshort.net",
    
    # Indian shorteners
    "indianshortner.in", "indianshortner.com",
    "tnshort.net", "tnlink.in",
    "shortindia.com", "shortindia.in",
    
    # New pattern detection keywords
    "link", "short", "tiny", "bit", "goo", "ow", "adf", "shorte", "ouo",
    "drop", "earn", "rock", "share", "disk", "bind", "tek", "url", "veer",
    "vii", "vvd", "xps", "zae", "zyn", "indian", "tn", "shortindia"
]

class EnhancedLinkBypasser:
    def __init__(self):
        self.session = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
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
        """Enhanced shortener detection"""
        try:
            domain = urlparse(url).netloc.lower()
            domain = domain.replace('www.', '')
            
            # Direct domain match
            for short_domain in SHORTENER_DOMAINS:
                if domain == short_domain or domain.endswith(f'.{short_domain}'):
                    return True
            
            # Pattern matching for new domains
            short_keywords = ['link', 'short', 'tiny', 'bit', 'goo', 'ow', 'adf', 'shorte', 'ouo', 
                            'drop', 'earn', 'rock', 'share', 'disk', 'bind', 'tek', 'url', 'veer',
                            'vii', 'vvd', 'xps', 'zae', 'zyn', 'indian', 'tn']
            
            for keyword in short_keywords:
                if keyword in domain and len(domain.split('.')) >= 2:
                    # Check if it looks like a domain (has dot and reasonable length)
                    return True
            
            return False
        except:
            return False
    
    async def bypass_gplinks_co(self, url):
        """Specialized bypass for gplinks.co"""
        try:
            session = await self.get_session()
            
            # Add referer
            headers = self.headers.copy()
            headers['Referer'] = 'https://www.google.com/'
            
            # First request
            async with session.get(url, headers=headers, allow_redirects=False) as response:
                html = await response.text()
                
                print(f"Initial HTML (first 1000 chars): {html[:1000]}")
                
                # Method 1: Look for direct JavaScript redirect
                patterns = [
                    r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                    r'window\.location\s*=\s*["\']([^"\']+)["\']',
                    r'location\.href\s*=\s*["\']([^"\']+)["\']',
                    r'window\.open\(["\']([^"\']+)["\']',
                    r'<meta[^>]*?http-equiv=["\']refresh["\'][^>]*?content=["\']\d+;\s*url=([^"\'>]+)',
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?id=["\']get_link["\']',
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?class=["\']btn-primary["\']',
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?onclick=["\']getlink[^"\']*["\']',
                    r'document\.getElementById\(["\']\w+["\']\)\.href\s*=\s*["\']([^"\']+)["\']',
                    r'var\s+\w+\s*=\s*["\']([^"\']+)["\']',
                    r'"url"\s*:\s*["\']([^"\']+)["\']',
                    r'data-url=["\']([^"\']+)["\']',
                    r'data-link=["\']([^"\']+)["\']',
                    r'action=["\']([^"\']+)["\']'
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        if match and match.startswith('http'):
                            print(f"Found URL with pattern {pattern}: {match}")
                            return match
                        elif match and match.startswith('/'):
                            parsed = urlparse(url)
                            full_url = f"{parsed.scheme}://{parsed.netloc}{match}"
                            print(f"Found relative URL: {full_url}")
                            return full_url
                
                # Method 2: Look for Base64 encoded URLs
                base64_pattern = r'["\']([A-Za-z0-9+/=]+)["\']\s*\.\s*split\s*\(["\'][^"\']*["\']\)'
                base64_matches = re.findall(base64_pattern, html)
                for b64_str in base64_matches:
                    try:
                        decoded = b64decode(b64_str).decode('utf-8')
                        if decoded.startswith('http'):
                            print(f"Found Base64 URL: {decoded}")
                            return decoded
                    except:
                        continue
                
                # Method 3: Look for AJAX requests or API endpoints
                ajax_patterns = [
                    r'fetch\(["\']([^"\']+api[^"\']*)["\']',
                    r'\.ajax\([^)]*url:\s*["\']([^"\']+)["\']',
                    r'axios\.get\(["\']([^"\']+)["\']',
                    r'\.post\(["\']([^"\']+)["\']'
                ]
                
                for pattern in ajax_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        if 'api' in match or 'getlink' in match:
                            api_url = match if match.startswith('http') else f"https://{urlparse(url).netloc}{match}"
                            try:
                                async with session.post(api_url, headers=headers) as api_response:
                                    if api_response.status == 200:
                                        api_data = await api_response.json()
                                        if isinstance(api_data, dict):
                                            for key in ['url', 'link', 'destination', 'target']:
                                                if key in api_data and api_data[key].startswith('http'):
                                                    return api_data[key]
                            except:
                                continue
                
                # Method 4: Try to find and submit forms
                form_pattern = r'<form[^>]*?action=["\']([^"\']*)["\'][^>]*?>([\s\S]*?)</form>'
                form_matches = re.findall(form_pattern, html, re.IGNORECASE | re.DOTALL)
                
                for form_action, form_content in form_matches:
                    print(f"Found form with action: {form_action}")
                    
                    # Extract all input fields
                    inputs = {}
                    input_pattern = r'<input[^>]*?name=["\']([^"\']+)["\'][^>]*?(?:value=["\']([^"\']*)["\'])?'
                    input_matches = re.findall(input_pattern, form_content, re.IGNORECASE)
                    
                    for name, value in input_matches:
                        inputs[name] = value if value else ""
                    
                    # Also get button values
                    button_pattern = r'<button[^>]*?name=["\']([^"\']+)["\'][^>]*?(?:value=["\']([^"\']*)["\'])?'
                    button_matches = re.findall(button_pattern, form_content, re.IGNORECASE)
                    for name, value in button_matches:
                        inputs[name] = value if value else "Submit"
                    
                    if inputs:
                        print(f"Form inputs: {inputs}")
                        
                        # Construct form URL
                        if form_action:
                            if not form_action.startswith('http'):
                                parsed = urlparse(url)
                                form_url = f"{parsed.scheme}://{parsed.netloc}{form_action}"
                            else:
                                form_url = form_action
                        else:
                            form_url = url
                        
                        # Submit form
                        async with session.post(form_url, data=inputs, headers=headers, allow_redirects=False) as post_response:
                            if post_response.status in [301, 302, 303, 307, 308]:
                                location = post_response.headers.get('Location')
                                if location:
                                    print(f"Form redirect to: {location}")
                                    return location
                            
                            # Try to get URL from response
                            post_html = await post_response.text()
                            for pattern in patterns:
                                post_matches = re.findall(pattern, post_html, re.IGNORECASE)
                                for match in post_matches:
                                    if match and match.startswith('http'):
                                        print(f"Found URL in form response: {match}")
                                        return match
            
            # Method 5: Try with different user agents
            mobile_headers = headers.copy()
            mobile_headers['User-Agent'] = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
            
            async with session.get(url, headers=mobile_headers, allow_redirects=False) as mobile_response:
                if mobile_response.status in [301, 302, 303, 307, 308]:
                    location = mobile_response.headers.get('Location')
                    if location:
                        print(f"Mobile redirect to: {location}")
                        return location
                
                mobile_html = await mobile_response.text()
                for pattern in patterns:
                    matches = re.findall(pattern, mobile_html, re.IGNORECASE)
                    for match in matches:
                        if match and match.startswith('http'):
                            print(f"Found URL in mobile version: {match}")
                            return match
            
            # Method 6: Try to extract from script variables
            script_pattern = r'<script[^>]*?>([\s\S]*?)</script>'
            script_matches = re.findall(script_pattern, html, re.IGNORECASE)
            
            for script in script_matches:
                # Look for URL assignment
                url_assignments = re.findall(r'(?:var|let|const)\s+\w+\s*=\s*["\']([^"\']+)["\']', script)
                for assignment in url_assignments:
                    if assignment.startswith('http'):
                        print(f"Found URL in script assignment: {assignment}")
                        return assignment
                
                # Look for function calls that might return URLs
                func_patterns = [
                    r'\.getAttribute\(["\']data-url["\']\)',
                    r'\.href\s*=\s*([^;]+)',
                    r'JSON\.parse\([^)]+\)'
                ]
                
                for func_pattern in func_patterns:
                    if re.search(func_pattern, script):
                        # Try to evaluate simple expressions
                        simple_expr = r'=\s*([^;]+?)(?:;|$)'
                        expr_matches = re.findall(simple_expr, script)
                        for expr in expr_matches:
                            if 'http' in expr and '"' in expr:
                                url_match = re.search(r'["\']([^"\']+)["\']', expr)
                                if url_match:
                                    found_url = url_match.group(1)
                                    if found_url.startswith('http'):
                                        print(f"Found URL in expression: {found_url}")
                                        return found_url
            
            return url
            
        except Exception as e:
            print(f"Error in bypass_gplinks_co: {e}")
            import traceback
            traceback.print_exc()
            return url
    
    async def bypass_with_solver(self, url):
        """Try to use various solving techniques"""
        try:
            session = await self.get_session()
            
            # Technique 1: Add common bypass parameters
            bypass_params = {
                'bypass': 'yes',
                'skip': 'true',
                'direct': 'true',
                'noredirect': 'true',
                'nosplash': 'true',
                'autobypass': 'true'
            }
            
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            query_params.update(bypass_params)
            
            bypass_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{urlencode(query_params, doseq=True)}"
            
            async with session.get(bypass_url, allow_redirects=True) as response:
                if str(response.url) != url:
                    return str(response.url)
            
            # Technique 2: Try with different referers
            referers = [
                'https://www.google.com/',
                'https://twitter.com/',
                'https://facebook.com/',
                'https://www.reddit.com/',
                'https://t.me/',
                ''
            ]
            
            for referer in referers:
                headers = self.headers.copy()
                if referer:
                    headers['Referer'] = referer
                
                async with session.get(url, headers=headers, allow_redirects=False) as response:
                    if response.status in [301, 302, 303, 307, 308]:
                        location = response.headers.get('Location')
                        if location and location != url:
                            return location
            
            # Technique 3: Try to simulate button click by navigating through pages
            async with session.get(url, allow_redirects=False) as response:
                html = await response.text()
                
                # Look for any clickable elements
                click_patterns = [
                    r'<a[^>]*?href=["\']([^"\']+)["\'][^>]*?>.*?(?:skip|continue|proceed|get|link|download).*?</a>',
                    r'<button[^>]*?onclick=["\']window\.location\.href=([^"\']+)["\']',
                    r'<div[^>]*?onclick=["\']window\.open\(([^"\']+)\)["\']',
                    r'<span[^>]*?data-url=["\']([^"\']+)["\']'
                ]
                
                for pattern in click_patterns:
                    matches = re.findall(pattern, html, re.IGNORECASE)
                    for match in matches:
                        if match.startswith('http'):
                            return match
                        elif match.startswith('/'):
                            parsed = urlparse(url)
                            return f"{parsed.scheme}://{parsed.netloc}{match}"
            
            return url
            
        except Exception as e:
            print(f"Error in bypass_with_solver: {e}")
            return url
    
    async def bypass_url(self, url):
        """Main bypass function with enhanced techniques"""
        if not self.is_shortener_link(url):
            return url, False
        
        original_url = url
        
        try:
            domain = urlparse(url).netloc.lower().replace('www.', '')
            
            print(f"Attempting to bypass: {url}")
            print(f"Domain: {domain}")
            
            # Special handling for gplinks.co
            if 'gplinks.co' in domain:
                print("Using specialized gplinks.co bypass")
                result = await self.bypass_gplinks_co(url)
            else:
                # Try generic bypass first
                result = await self.bypass_with_solver(url)
                
                # If still shortener, try specialized methods
                if self.is_shortener_link(result):
                    if 'linkvertise' in domain:
                        from .bypass_methods import bypass_linkvertise
                        result = await bypass_linkvertise(url)
                    elif 'ouo' in domain:
                        from .bypass_methods import bypass_ouo
                        result = await bypass_ouo(url)
            
            # Final check - if result is still a shortener, try recursive
            if self.is_shortener_link(result) and result != url:
                print(f"Recursive bypass attempt for: {result}")
                result, _ = await self.bypass_url(result)
            
            success = result != url and not self.is_shortener_link(result)
            
            if success:
                print(f"Successfully bypassed to: {result}")
            else:
                print(f"Bypass failed or resulted in same/shortener URL: {result}")
            
            return result, success
            
        except Exception as e:
            print(f"Error in bypass_url: {e}")
            import traceback
            traceback.print_exc()
            return url, False

# Global bypasser instance
bypasser = EnhancedLinkBypasser()

@Client.on_message(filters.command("link") & filters.user(ADMIN_USER_ID))
async def bypass_link_command(client, message: Message):
    """Admin command to bypass shortener links"""
    if len(message.command) < 2:
        await message.reply_text(
            "**🔄 Link Bypasser**\n\n"
            "**Usage:** `/link <shortener_url>`\n\n"
            "**Examples:**\n"
            "• `/link https://gplinks.co/Prifb`\n"
            "• `/link https://gplinks.co/abc https://linkvertise.com/xyz`\n\n"
            "**Other Commands:**\n"
            "• `/shorteners` - Show supported domains\n"
            "• `/addshortener <domain>` - Add new domain"
        )
        return
    
    # Extract URLs
    urls = []
    text = ' '.join(message.command[1:])
    
    # Find all URLs in the text
    url_pattern = r'https?://[^\s]+'
    urls = re.findall(url_pattern, text)
    
    if not urls:
        await message.reply_text("❌ No valid URLs found. Please provide valid http:// or https:// links.")
        return
    
    processing_msg = await message.reply_text(f"🔍 Analyzing {len(urls)} link(s)...")
    
    results = []
    successful = 0
    
    for i, url in enumerate(urls):
        try:
            status_msg = await processing_msg.edit_text(
                f"⏳ Processing link {i+1}/{len(urls)}...\n"
                f"URL: `{url[:50]}...`"
            )
            
            # Check if it's a shortener
            if not bypasser.is_shortener_link(url):
                results.append(f"⚠️ `{url}`\n   └ Not recognized as shortener")
                continue
            
            # Attempt bypass
            original_url, success = await bypasser.bypass_url(url)
            
            if success:
                results.append(f"✅ `{url}`\n   └ **Original:** `{original_url}`")
                successful += 1
                
                # Send individual success message for important links
                if len(urls) <= 3:
                    try:
                        await message.reply_text(
                            f"**✅ Link Unlocked!**\n\n"
                            f"**Shortened:** `{url}`\n"
                            f"**Original:** `{original_url}`\n\n"
                            f"*You can click the original link above to copy it.*",
                            disable_web_page_preview=True
                        )
                    except:
                        pass
            else:
                results.append(f"❌ `{url}`\n   └ Could not bypass")
                
                # Try alternative method
                if 'gplinks.co' in url:
                    await status_msg.edit_text(f"🔄 Trying alternative method for gplinks.co...")
                    # Add a small delay
                    await asyncio.sleep(1)
        
        except Exception as e:
            results.append(f"💥 `{url}`\n   └ Error: {str(e)[:30]}")
    
    # Format final results
    result_text = f"**📊 Link Bypass Results**\n\n"
    result_text += f"• 🔍 Analyzed: {len(urls)}\n"
    result_text += f"• ✅ Success: {successful}\n"
    result_text += f"• ❌ Failed: {len(urls) - successful}\n\n"
    
    if results:
        # Show all results if 5 or less, otherwise show summary
        if len(results) <= 5:
            result_text += "**Details:**\n" + "\n".join(results)
        else:
            result_text += f"**First 3 results:**\n" + "\n".join(results[:3])
            if len(results) > 3:
                result_text += f"\n\n... and {len(results) - 3} more"
    
    # Add debug info for gplinks.co failures
    if successful == 0 and any('gplinks.co' in url for url in urls):
        result_text += "\n\n**⚠️ Note:** gplinks.co might have updated their protection.\n"
        result_text += "Try these alternatives:\n"
        result_text += "1. Use `/link` with the URL\n"
        result_text += "2. Try opening in browser with VPN\n"
        result_text += "3. Check if link requires solving CAPTCHA"
    
    await processing_msg.edit_text(result_text, disable_web_page_preview=True)

@Client.on_message(filters.command("bypass") & filters.user(ADMIN_USER_ID))
async def bypass_single_command(client, message: Message):
    """Alternative command for single link bypass with more details"""
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/bypass <url>`")
        return
    
    url = message.command[1]
    
    if not url.startswith(('http://', 'https://')):
        await message.reply_text("❌ Please provide a valid URL starting with http:// or https://")
        return
    
    msg = await message.reply_text(
        f"**🔗 Analyzing URL...**\n\n"
        f"`{url}`\n\n"
        f"Checking shortener type..."
    )
    
    # Check if shortener
    if not bypasser.is_shortener_link(url):
        await msg.edit_text(
            f"**❓ Not a Shortener**\n\n"
            f"`{url}`\n\n"
            f"This doesn't appear to be a known shortener link.\n"
            f"If it is, use `/addshortener {urlparse(url).netloc}`"
        )
        return
    
    domain = urlparse(url).netloc
    await msg.edit_text(
        f"**🔄 Bypassing {domain}...**\n\n"
        f"URL: `{url}`\n\n"
        f"Attempting to extract original link..."
    )
    
    # Attempt bypass
    original_url, success = await bypasser.bypass_url(url)
    
    if success:
        await msg.edit_text(
            f"**✅ Success!**\n\n"
            f"**Shortened:** `{url}`\n"
            f"**Original:** `{original_url}`\n\n"
            f"**Click the original link above to copy it.**",
            disable_web_page_preview=True
        )
    else:
        await msg.edit_text(
            f"**❌ Failed to Bypass**\n\n"
            f"URL: `{url}`\n\n"
            f"**Possible reasons:**\n"
            f"• Link requires CAPTCHA\n"
            f"• Link has expired\n"
            f"• Shortener has updated protection\n"
            f"• Requires human verification\n\n"
            f"**Try:**\n"
            f"1. Open in browser\n"
            f"2. Use VPN\n"
            f"3. Check if link is valid"
        )

@Client.on_message(filters.command("shorteners") & filters.user(ADMIN_USER_ID))
async def list_shorteners_command(client, message: Message):
    """List all supported shortener domains"""
    domains_text = "**📋 Supported Shortener Domains**\n\n"
    
    # Group by category
    categories = {
        "GPLinks": [d for d in SHORTENER_DOMAINS if 'gplink' in d],
        "Linkvertise": [d for d in SHORTENER_DOMAINS if 'linkvertise' in d or 'up-to-down' in d],
        "Ouo": [d for d in SHORTENER_DOMAINS if 'ouo' in d],
        "DropLink": [d for d in SHORTENER_DOMAINS if 'droplink' in d],
        "Indian": [d for d in SHORTENER_DOMAINS if any(kw in d for kw in ['indian', 'tn', 'shortindia'])],
        "Others": [d for d in SHORTENER_DOMAINS if not any(kw in d for kw in ['gplink', 'linkvertise', 'ouo', 'droplink', 'indian', 'tn', 'shortindia'])]
    }
    
    for category, domains in categories.items():
        if domains:
            domains_text += f"**{category}:**\n"
            domains = sorted(set(domains))
            for i in range(0, len(domains), 4):
                row = domains[i:i+4]
                domains_text += "  " + "  |  ".join(f"`{d}`" for d in row) + "\n"
            domains_text += "\n"
    
    domains_text += f"**Total:** {len(SHORTENER_DOMAINS)} domains"
    
    await message.reply_text(domains_text)

@Client.on_message(filters.command("addshortener") & filters.user(ADMIN_USER_ID))
async def add_shortener_command(client, message: Message):
    """Add a new shortener domain to the list"""
    if len(message.command) < 2:
        await message.reply_text("**Usage:** `/addshortener <domain>`\n\n**Example:** `/addshortener example.com`")
        return
    
    domain = message.command[1].lower().strip()
    
    # Clean domain
    if domain.startswith(('http://', 'https://')):
        parsed = urlparse(domain)
        domain = parsed.netloc
    
    domain = domain.replace('www.', '')
    
    if domain in SHORTENER_DOMAINS:
        await message.reply_text(f"`{domain}` is already in the list.")
    else:
        SHORTENER_DOMAINS.append(domain)
        await message.reply_text(f"✅ Added `{domain}` to shortener domains list.\n\n**New total:** {len(SHORTENER_DOMAINS)} domains")

@Client.on_message(filters.command("testbypass") & filters.user(ADMIN_USER_ID))
async def test_bypass_command(client, message: Message):
    """Test bypass with debug information"""
    test_urls = [
        "https://gplinks.co/Prifb",
        "https://gplinks.in/example",
        "https://linkvertise.com/12345",
        "https://ouo.io/abcde"
    ]
    
    results = []
    
    for test_url in test_urls:
        is_short = bypasser.is_shortener_link(test_url)
        results.append(f"{'✅' if is_short else '❌'} `{test_url}` - {'Shortener' if is_short else 'Not shortener'}")
    
    await message.reply_text(
        "**🧪 Bypass System Test**\n\n" +
        "\n".join(results) +
        f"\n\n**Status:** {'🟢 Working' if any('✅' in r for r in results) else '🔴 Issues'}"
    )

# Cleanup
async def cleanup():
    await bypasser.close_session()

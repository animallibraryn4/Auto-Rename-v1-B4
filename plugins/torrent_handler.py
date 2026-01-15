import os
import re
import time
import asyncio
import hashlib
import libtorrent as lt
from typing import Optional, Tuple
from pathlib import Path
from urllib.parse import urlparse

class TorrentManager:
    def __init__(self, download_dir: str = "torrents"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        self.sessions = {}  # user_id -> session
        
    async def create_session(self, user_id: int) -> lt.session:
        """Create or get existing session for user"""
        if user_id not in self.sessions:
            ses = lt.session()
            ses.listen_on(6881, 6891)
            self.sessions[user_id] = ses
        return self.sessions[user_id]
    
    async def cleanup_session(self, user_id: int):
        """Clean up torrent session for user"""
        if user_id in self.sessions:
            self.sessions.pop(user_id, None)
    
    def is_magnet_link(self, text: str) -> bool:
        """Check if text is a magnet link"""
        return text.startswith('magnet:?')
    
    def is_torrent_file(self, filename: str) -> bool:
        """Check if file is a .torrent file"""
        return filename.lower().endswith('.torrent')
    
    def get_torrent_info_hash(self, magnet_link: str) -> Optional[str]:
        """Extract info hash from magnet link"""
        match = re.search(r'xt=urn:btih:([a-fA-F0-9]{40})', magnet_link)
        if match:
            return match.group(1).lower()
        return None
    
    async def download_torrent(self, magnet_link: str, save_path: str) -> Optional[lt.torrent_info]:
        """Download .torrent file from magnet link"""
        try:
            info_hash = self.get_torrent_info_hash(magnet_link)
            if not info_hash:
                return None
            
            # Create session for downloading metadata
            ses = lt.session()
            params = lt.parse_magnet_uri(magnet_link)
            handle = ses.add_torrent(params)
            
            # Wait for metadata
            print("Downloading torrent metadata...")
            while not handle.has_metadata():
                await asyncio.sleep(1)
            
            # Create torrent info
            torrent_info = handle.get_torrent_info()
            
            # Save .torrent file
            torrent_file = lt.create_torrent(torrent_info)
            torrent_data = lt.bencode(torrent_file.generate())
            
            torrent_path = os.path.join(save_path, f"{info_hash}.torrent")
            with open(torrent_path, 'wb') as f:
                f.write(torrent_data)
            
            ses.remove_torrent(handle)
            return torrent_info
        except Exception as e:
            print(f"Error downloading torrent: {e}")
            return None
    
    async def get_torrent_files(self, torrent_info: lt.torrent_info, user_id: int) -> list:
        """Get list of files in torrent"""
        files = []
        for i in range(torrent_info.num_files()):
            file_entry = torrent_info.file_at(i)
            files.append({
                'index': i,
                'path': file_entry.path,
                'size': file_entry.size,
                'name': os.path.basename(file_entry.path)
            })
        return files
    
    async def download_torrent_content(
        self, 
        user_id: int, 
        magnet_link: str = None, 
        torrent_path: str = None,
        selected_file_index: int = None
    ) -> Optional[str]:
        """Download torrent content"""
        try:
            # Create user-specific directory
            user_dir = self.download_dir / str(user_id)
            user_dir.mkdir(exist_ok=True)
            
            # Get session
            ses = await self.create_session(user_id)
            
            # Add torrent to session
            if magnet_link:
                params = lt.parse_magnet_uri(magnet_link)
                params.save_path = str(user_dir)
                handle = ses.add_torrent(params)
            elif torrent_path:
                ti = lt.torrent_info(torrent_path)
                params = {
                    'ti': ti,
                    'save_path': str(user_dir)
                }
                handle = ses.add_torrent(params)
            else:
                return None
            
            # Wait for download to complete
            print("Downloading torrent content...")
            while not handle.status().is_seeding:
                status = handle.status()
                state_str = status.state
                
                if status.paused:
                    print("Torrent is paused")
                    break
                
                print(f"\rProgress: {status.progress * 100:.1f}% | "
                      f"Download rate: {status.download_rate / 1000:.1f} kB/s | "
                      f"Peers: {status.num_peers}", end='')
                
                await asyncio.sleep(1)
            
            print("\nDownload completed!")
            
            # Get the downloaded file path
            torrent_info = handle.get_torrent_info()
            
            if selected_file_index is not None:
                # Download specific file
                file_entry = torrent_info.file_at(selected_file_index)
                file_path = user_dir / file_entry.path
            else:
                # For single file torrents
                if torrent_info.num_files() == 1:
                    file_entry = torrent_info.file_at(0)
                    file_path = user_dir / file_entry.path
                else:
                    # For multi-file torrents, create a zip or return directory
                    # For now, we'll handle this case in the main handler
                    file_path = user_dir
            
            # Pause and remove torrent
            handle.pause()
            ses.remove_torrent(handle)
            
            return str(file_path)
            
        except Exception as e:
            print(f"Error downloading torrent content: {e}")
            return None
    
    async def cleanup_user_files(self, user_id: int):
        """Clean up downloaded files for user"""
        user_dir = self.download_dir / str(user_id)
        if user_dir.exists():
            import shutil
            try:
                shutil.rmtree(user_dir)
            except:
                pass

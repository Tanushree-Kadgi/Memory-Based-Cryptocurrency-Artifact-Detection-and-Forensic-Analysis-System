"""
Memory Acquisition Module for SeedTrace
Integrates with winpmem.exe for automated RAM dump acquisition
"""
import os
import subprocess
import shutil
from datetime import datetime
from typing import Optional, Tuple


class MemoryAcquirer:
    """Handles automated memory acquisition using winpmem.exe"""
    
    def __init__(self, winpmem_path: str = None, dumps_dir: str = "dumps"):
        """
        Initialize the memory acquirer
        
        Args:
            winpmem_path: Path to winpmem.exe executable
            dumps_dir: Directory to store memory dumps
        """
        self.dumps_dir = dumps_dir
        os.makedirs(dumps_dir, exist_ok=True)
        
        # Try to find winpmem.exe
        if winpmem_path and os.path.exists(winpmem_path):
            self.winpmem_path = winpmem_path
        else:
            self.winpmem_path = self._find_winpmem()
        
        self.is_available = self.winpmem_path is not None
    
    def _find_winpmem(self) -> Optional[str]:
        """
        Search for winpmem.exe in common locations
        """
        search_paths = [
            "winpmem.exe",
            "tools/winpmem.exe",
            "tools/winpmem/winpmem.exe",
            os.path.join(os.getcwd(), "winpmem.exe"),
            os.path.join(os.getcwd(), "tools", "winpmem.exe"),
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def acquire_memory(self, output_filename: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Acquire system memory using winpmem.exe
        
        Args:
            output_filename: Optional custom filename for the dump
            
        Returns:
            Tuple of (success: bool, message: str, filepath: Optional[str])
        """
        if not self.is_available:
            return False, "winpmem.exe not found. Please place winpmem.exe in the tools/ directory.", None
        
        # Generate filename if not provided
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"memory_dump_{timestamp}.raw"
        
        output_path = os.path.join(self.dumps_dir, output_filename)
        
        try:
            # Check if winpmem requires admin privileges
            # On Windows, memory acquisition typically requires admin rights
            # Normalize path for Windows and wrap in quotes to handle spaces
            winpmem_exe = os.path.abspath(self.winpmem_path)
            
            # winpmem.exe acquire <path>
            command = [winpmem_exe, "acquire", os.path.abspath(output_path)]
            
            print(f"[*] Executing command: {command}")
            
            # Run the command directly as a list (no shell=True) for better reliability
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0:
                file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                message = f"Memory acquisition successful. File: {output_filename} ({file_size / (1024**3):.2f} GB)"
                return True, message, output_path
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                return False, f"Memory acquisition failed: {error_msg}", None
                
        except subprocess.TimeoutExpired:
            return False, "Memory acquisition timed out (10 minutes)", None
        except PermissionError:
            return False, "Permission denied. Memory acquisition requires administrator privileges.", None
        except Exception as e:
            return False, f"Memory acquisition error: {str(e)}", None
    
    def get_available_space(self) -> float:
        """
        Get available disk space in GB
        """
        try:
            stat = shutil.disk_usage(self.dumps_dir)
            return stat.free / (1024**3)
        except Exception:
            return 0.0
    
    def check_requirements(self) -> dict:
        """
        Check if memory acquisition requirements are met
        """
        checks = {
            "winpmem_available": self.is_available,
            "winpmem_path": self.winpmem_path,
            "dumps_directory_exists": os.path.exists(self.dumps_dir),
            "dumps_directory_writable": os.access(self.dumps_dir, os.W_OK),
            "available_space_gb": self.get_available_space(),
            "admin_privileges": self._check_admin()
        }
        
        return checks
    
    def _check_admin(self) -> bool:
        """
        Check if running with administrator privileges
        """
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    def estimate_dump_size(self) -> float:
        """
        Estimate the size of memory dump in GB
        This is a rough estimate based on total system memory
        """
        try:
            import psutil
            total_memory = psutil.virtual_memory().total
            return total_memory / (1024**3)
        except Exception:
            return 0.0


if __name__ == "__main__":
    # Test the memory acquirer
    acquirer = MemoryAcquirer()
    
    print("=== Memory Acquisition Module Test ===")
    print(f"winpmem.exe available: {acquirer.is_available}")
    print(f"winpmem.exe path: {acquirer.winpmem_path}")
    
    checks = acquirer.check_requirements()
    print("\n=== Requirements Check ===")
    for key, value in checks.items():
        print(f"{key}: {value}")
    
    if acquirer.is_available:
        print("\n=== Ready to acquire memory ===")
        print("To acquire memory, call: acquirer.acquire_memory()")
    else:
        print("\n=== winpmem.exe not found ===")
        print("Please download winpmem.exe from: https://github.com/Velocidex/WinPmem")
        print("Place it in the tools/ directory or specify the path when initializing.")

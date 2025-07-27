#!/usr/bin/env python3
"""
Free your VRAM!

Usage:
    python gpu_cleaner.py [options]
    or install as a package and use:
    gpu-clean [options]
"""

import subprocess
import re
import os
import signal
import sys
import argparse
import time
from typing import List, Dict, Optional, Tuple


class GPUMemoryCleaner:
    
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.nvidia_smi_available = self._check_nvidia_smi()
    
    def _check_nvidia_smi(self) -> bool:
         
        try:
            subprocess.run(['nvidia-smi', '--version'], 
                         capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _log(self, message: str):
        
        if self.verbose:
            print(f"[GPU-CLEANER] {message}")
    
    def get_gpu_processes(self) -> List[Dict[str, str]]:
        if not self.nvidia_smi_available:
            raise RuntimeError("nvidia-smi not found. Make sure NVIDIA drivers are installed.")
        
        try:
            # Run nvidia-smi to get process information
            cmd = ['nvidia-smi', 'pmon', '-c', '1', '-s', 'um']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            processes = []
            lines = result.stdout.strip().split('\n')
            
            # Skip header lines
            data_lines = [line for line in lines if not line.startswith('#') and line.strip()]
            
            for line in data_lines:
                # Parse the output: gpu pid type sm mem enc dec command
                parts = line.split()
                if len(parts) >= 7:
                    processes.append({
                        'gpu_id': parts[0],
                        'pid': parts[1],
                        'type': parts[2],
                        'sm': parts[3],
                        'mem': parts[4],
                        'enc': parts[5],
                        'dec': parts[6],
                        'command': ' '.join(parts[7:]) if len(parts) > 7 else 'N/A'
                    })
            
            # Alternative method using nvidia-smi query if pmon doesn't work
            if not processes:
                processes = self._get_processes_alternative()
                
            return processes
            
        except subprocess.CalledProcessError as e:
            self._log(f"Error running nvidia-smi: {e}")
            return self._get_processes_alternative()
    
    def _get_processes_alternative(self) -> List[Dict[str, str]]:
         
        try:
            cmd = ['nvidia-smi', '--query-compute-apps=pid,process_name,gpu_uuid,used_memory', 
                   '--format=csv,noheader,nounits']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            processes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 4:
                        processes.append({
                            'pid': parts[0],
                            'command': parts[1],
                            'gpu_uuid': parts[2],
                            'memory': parts[3],
                            'gpu_id': '0'  # Default, could be enhanced
                        })
            
            return processes
            
        except subprocess.CalledProcessError:
            return []
    
    def get_memory_usage(self) -> List[Dict[str, str]]:
         
        try:
            cmd = ['nvidia-smi', '--query-gpu=index,memory.used,memory.total,memory.free', 
                   '--format=csv,noheader,nounits']
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            memory_info = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = [part.strip() for part in line.split(',')]
                    if len(parts) >= 4:
                        memory_info.append({
                            'gpu_id': parts[0],
                            'used': parts[1],
                            'total': parts[2],
                            'free': parts[3]
                        })
            
            return memory_info
            
        except subprocess.CalledProcessError:
            return []
    
    def terminate_process(self, pid: str, force: bool = False) -> bool:
     
        
        try:
            pid_int = int(pid)
            if force:
                os.kill(pid_int, signal.SIGKILL)
                self._log(f"Force killed process {pid}")
            else:
                os.kill(pid_int, signal.SIGTERM)
                self._log(f"Terminated process {pid}")
            return True
        except (ValueError, ProcessLookupError, PermissionError) as e:
            self._log(f"Failed to terminate process {pid}: {e}")
            return False
    
    def clear_gpu_memory(self, gpu_ids: Optional[List[str]] = None, 
                        exclude_pids: Optional[List[str]] = None,
                        force: bool = False,
                        dry_run: bool = False) -> Tuple[int, int]:
        

        if exclude_pids is None:
            exclude_pids = []
        
        processes = self.get_gpu_processes()
        
        if not processes:
            self._log("No GPU processes found")
            return 0, 0
        
        # Filter processes by GPU ID if specified
        if gpu_ids:
            processes = [p for p in processes if p.get('gpu_id') in gpu_ids]
        
        # Filter out excluded PIDs
        processes = [p for p in processes if p.get('pid') not in exclude_pids]
        
        processes_found = len(processes)
        processes_terminated = 0
        
        if dry_run:
            print(f"DRY RUN: Would terminate {processes_found} processes:")
            for proc in processes:
                print(f"  PID: {proc.get('pid')}, Command: {proc.get('command', 'N/A')}")
            return processes_found, 0
        
        for proc in processes:
            pid = proc.get('pid')
            if pid and self.terminate_process(pid, force):
                processes_terminated += 1
        
        # Wait a moment for processes to actually terminate
        if processes_terminated > 0:
            time.sleep(1)
        
        return processes_found, processes_terminated
    
    def display_status(self):
        
        print("=== GPU Memory Status ===")
        
        memory_info = self.get_memory_usage()
        if memory_info:
            for gpu in memory_info:
                used_mb = int(gpu['used'])
                total_mb = int(gpu['total'])
                free_mb = int(gpu['free'])
                usage_percent = (used_mb / total_mb) * 100 if total_mb > 0 else 0
                
                print(f"GPU {gpu['gpu_id']}: {used_mb}MB / {total_mb}MB "
                      f"({usage_percent:.1f}% used, {free_mb}MB free)")
        
        print("\n=== GPU Processes ===")
        processes = self.get_gpu_processes()
        if processes:
            for proc in processes:
                print(f"PID: {proc.get('pid'):<8} "
                      f"GPU: {proc.get('gpu_id', 'N/A'):<3} "
                      f"Memory: {proc.get('memory', proc.get('mem', 'N/A')):<8} "
                      f"Command: {proc.get('command', 'N/A')}")
        else:
            print("No GPU processes found")


def main():
     
    parser = argparse.ArgumentParser(
        description="Clear NVIDIA GPU memory by terminating processes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  gpu-clean --status                    # Show GPU status
  gpu-clean --clear                     # Clear all GPU processes
  gpu-clean --clear --force             # Force kill all GPU processes
  gpu-clean --clear --gpu 0,1           # Clear processes on GPU 0 and 1
  gpu-clean --clear --exclude 1234,5678 # Clear all except PIDs 1234,5678
  gpu-clean --clear --dry-run           # Show what would be cleared
        """
    )
    
    parser.add_argument('--status', '-s', action='store_true',
                       help='Show current GPU memory status and processes')
    parser.add_argument('--clear', '-c', action='store_true',
                       help='Clear GPU memory by terminating processes')
    parser.add_argument('--force', '-f', action='store_true',
                       help='Use SIGKILL instead of SIGTERM (more forceful)')
    parser.add_argument('--gpu', '-g', type=str,
                       help='Comma-separated list of GPU IDs to target (e.g., "0,1")')
    parser.add_argument('--exclude', '-e', type=str,
                       help='Comma-separated list of PIDs to exclude from termination')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Show what would be done without actually doing it')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
     
    if not (args.status or args.clear):
        args.status = True
    
    cleaner = GPUMemoryCleaner(verbose=args.verbose)
    
    try:
        if args.status:
            cleaner.display_status()
        
        if args.clear:
            gpu_ids = args.gpu.split(',') if args.gpu else None
            exclude_pids = args.exclude.split(',') if args.exclude else None
            
            found, terminated = cleaner.clear_gpu_memory(
                gpu_ids=gpu_ids,
                exclude_pids=exclude_pids,
                force=args.force,
                dry_run=args.dry_run
            )
            
            if args.dry_run:
                print(f"\nDry run complete. Found {found} processes to terminate.")
            else:
                print(f"\nCleared {terminated}/{found} GPU processes.")
                if terminated > 0:
                    print("\nUpdated GPU status:")
                    cleaner.display_status()
    
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
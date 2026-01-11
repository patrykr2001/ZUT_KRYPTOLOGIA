"""
Zadanie 11.3 - Launcher Script
Spawns broker and 4 mining nodes for distributed PoW simulation.
"""
import subprocess
import time
import sys
import os


def launch_distributed_pow(difficulty=20):
    """
    Launch the distributed PoW simulation system
    
    Args:
        difficulty: Mining difficulty in leading zero bits (default: 20)
    """
    print("\n" + "="*80)
    print("DISTRIBUTED POW SIMULATION - LAUNCHER")
    print("="*80)
    print(f"Difficulty: {difficulty} leading zero bits")
    print("Nodes: 1 Broker + 4 Mining Nodes")
    print("="*80 + "\n")
    
    processes = []
    
    try:
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Launch broker
        print("Starting broker node...")
        broker_cmd = [
            sys.executable,
            os.path.join(current_dir, "zad3_broker.py")
        ]
        
        # Use CREATE_NEW_CONSOLE on Windows to open in new window
        if sys.platform == 'win32':
            broker_process = subprocess.Popen(
                broker_cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # For Linux/Mac, run in background
            broker_process = subprocess.Popen(
                broker_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        
        processes.append(('Broker', broker_process))
        print(f"✅ Broker started (PID: {broker_process.pid})")
        
        # Wait for broker to initialize
        print("\nWaiting for broker to initialize...")
        time.sleep(2)
        
        # Launch 4 mining nodes
        for node_id in range(1, 5):
            print(f"Starting mining node {node_id}...")
            
            miner_cmd = [
                sys.executable,
                os.path.join(current_dir, "zad3_miner.py"),
                str(node_id)
            ]
            
            if sys.platform == 'win32':
                miner_process = subprocess.Popen(
                    miner_cmd,
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                miner_process = subprocess.Popen(
                    miner_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            processes.append((f'Miner {node_id}', miner_process))
            print(f"✅ Mining node {node_id} started (PID: {miner_process.pid})")
            time.sleep(0.5)
        
        print("\n" + "="*80)
        print("ALL NODES STARTED SUCCESSFULLY")
        print("="*80)
        print("\nThe distributed PoW simulation is now running in separate windows.")
        print("Watch the broker window for block acceptance notifications.")
        print("Watch the miner windows for mining progress and block discoveries.")
        print("\nPress Ctrl+C here to stop all processes...")
        print("="*80 + "\n")
        
        # Wait for user interrupt
        while True:
            time.sleep(1)
            # Check if any process has terminated unexpectedly
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n⚠️  {name} terminated unexpectedly (exit code: {proc.returncode})")
    
    except KeyboardInterrupt:
        print("\n\nShutting down all processes...")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    finally:
        # Terminate all processes
        print("\nTerminating processes...")
        for name, proc in processes:
            try:
                proc.terminate()
                print(f"  Stopped {name} (PID: {proc.pid})")
            except Exception as e:
                print(f"  Error stopping {name}: {e}")
        
        # Wait for processes to terminate
        time.sleep(1)
        
        # Force kill if still running
        for name, proc in processes:
            if proc.poll() is None:
                try:
                    proc.kill()
                    print(f"  Force killed {name}")
                except:
                    pass
        
        print("\n✅ All processes terminated")
        print("="*80 + "\n")


if __name__ == "__main__":
    # Get difficulty from command line or use default
    difficulty = 20
    if len(sys.argv) > 1:
        try:
            difficulty = int(sys.argv[1])
            print(f"Using custom difficulty: {difficulty} bits")
        except ValueError:
            print(f"Invalid difficulty, using default: {difficulty} bits")
    
    launch_distributed_pow(difficulty=difficulty)

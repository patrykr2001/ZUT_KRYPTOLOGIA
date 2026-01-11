"""
Zadanie 11.3 - Mining Node
Connects to broker, receives mining tasks, mines blocks using PoW, and handles cancellation.
"""
import socket
import pickle
import threading
import time
import sys
from blockchain_mining import BlockMiner, Block


class MiningNode:
    def __init__(self, node_id, broker_host='localhost', broker_port=5000):
        self.node_id = node_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Mining state
        self.miner = None
        self.current_task = None
        self.mining_active = threading.Event()
        self.stop_mining = threading.Event()
        
        # Connection
        self.socket = None
        self.connected = False
        
    def send_message(self, message):
        """Send pickled message with length prefix"""
        try:
            data = pickle.dumps(message)
            length = len(data).to_bytes(4, byteorder='big')
            self.socket.sendall(length + data)
            return True
        except Exception as e:
            print(f"[Node {self.node_id}] Error sending message: {e}")
            return False
    
    def receive_message(self):
        """Receive pickled message with length prefix"""
        try:
            # Receive length prefix (4 bytes)
            length_data = b''
            while len(length_data) < 4:
                chunk = self.socket.recv(4 - len(length_data))
                if not chunk:
                    return None
                length_data += chunk
            
            message_length = int.from_bytes(length_data, byteorder='big')
            
            # Receive message data
            data = b''
            while len(data) < message_length:
                chunk = self.socket.recv(min(4096, message_length - len(data)))
                if not chunk:
                    return None
                data += chunk
            
            return pickle.loads(data)
        except Exception as e:
            print(f"[Node {self.node_id}] Error receiving message: {e}")
            return None
    
    def mine_block_interruptible(self, transactions, previous_hash, block_number, difficulty):
        """
        Mine a block with ability to interrupt
        Based on BlockMiner.mine_block() but checks stop_mining flag periodically
        """
        from blockchain_mining import MerkleTree
        import hashlib
        
        # Compute Merkle root
        merkle_root = MerkleTree.build_merkle_tree(transactions)
        timestamp = int(time.time())
        
        nonce = 0
        attempts = 0
        start_time = time.time()
        check_interval = 10000  # Check for cancellation every N attempts
        
        while not self.stop_mining.is_set():
            # Compute block hash
            block_data = merkle_root + previous_hash + timestamp.to_bytes(8, byteorder='big') + \
                        block_number.to_bytes(8, byteorder='big') + nonce.to_bytes(8, byteorder='big')
            block_hash = hashlib.sha256(block_data).digest()
            
            attempts += 1
            
            # Check if hash meets difficulty
            if BlockMiner.hash_has_leading_zero_bits(block_hash, difficulty):
                elapsed = time.time() - start_time
                
                # Create block
                block = Block(
                    merkle_root=merkle_root,
                    previous_hash=previous_hash,
                    timestamp=timestamp,
                    block_number=block_number,
                    nonce=nonce,
                    block_hash=block_hash
                )
                
                return block, attempts, elapsed
            
            nonce += 1
            
            # Periodically check for cancellation and show progress
            if attempts % check_interval == 0:
                if self.stop_mining.is_set():
                    return None, attempts, time.time() - start_time
                
                elapsed = time.time() - start_time
                hash_rate = attempts / elapsed if elapsed > 0 else 0
                print(f"[Node {self.node_id}] Mining... {attempts:,} attempts, {hash_rate:.2f} H/s")
        
        # Mining was cancelled
        return None, attempts, time.time() - start_time
    
    def mining_worker(self):
        """Worker thread that performs mining"""
        while self.connected:
            # Wait for a mining task
            self.mining_active.wait()
            
            if not self.connected or self.current_task is None:
                break
            
            task = self.current_task
            print(f"\n[Node {self.node_id}] 🔨 Starting mining for block {task['block_number']}")
            print(f"[Node {self.node_id}]    Difficulty: {task['difficulty']} bits")
            print(f"[Node {self.node_id}]    Transactions: {len(task['transactions'])}")
            
            # Reset stop flag
            self.stop_mining.clear()
            
            # Mine the block
            result = self.mine_block_interruptible(
                transactions=task['transactions'],
                previous_hash=task['previous_hash'],
                block_number=task['block_number'],
                difficulty=task['difficulty']
            )
            
            block, attempts, elapsed = result
            
            if block is not None:
                # Successfully mined!
                print(f"\n[Node {self.node_id}] ✅ Block {block.block_number} MINED!")
                print(f"[Node {self.node_id}]    Hash: {block.block_hash.hex()[:32]}...")
                print(f"[Node {self.node_id}]    Nonce: {block.nonce}")
                print(f"[Node {self.node_id}]    Attempts: {attempts:,}")
                print(f"[Node {self.node_id}]    Time: {elapsed:.2f}s")
                
                # Send to broker
                message = {
                    'type': 'BLOCK_MINED',
                    'block': block,
                    'attempts': attempts,
                    'elapsed': elapsed
                }
                self.send_message(message)
            else:
                # Mining was cancelled
                print(f"[Node {self.node_id}] ⏸️  Mining cancelled for block {task['block_number']} after {attempts:,} attempts ({elapsed:.2f}s)")
            
            # Clear mining state
            self.mining_active.clear()
    
    def handle_new_task(self, message):
        """Handle new mining task from broker"""
        # Stop current mining if active
        if self.mining_active.is_set():
            print(f"[Node {self.node_id}] Stopping current mining task...")
            self.stop_mining.set()
            self.mining_active.clear()
            time.sleep(0.1)  # Give mining thread time to stop
        
        # Set new task
        self.current_task = message
        
        print(f"\n[Node {self.node_id}] 📩 New mining task received for block {message['block_number']}")
        
        # Start mining
        self.mining_active.set()
    
    def handle_block_accepted(self, message):
        """Handle block acceptance notification from broker"""
        block = message['block']
        winning_node = message['winning_node']
        
        if winning_node == self.node_id:
            print(f"\n[Node {self.node_id}] 🎉 MY BLOCK WAS ACCEPTED! Block #{block.block_number}")
        else:
            print(f"\n[Node {self.node_id}] 📢 Block {block.block_number} mined by Node {winning_node}")
            print(f"[Node {self.node_id}]    Stopping current mining...")
        
        # Stop current mining
        self.stop_mining.set()
        self.mining_active.clear()
    
    def message_listener(self):
        """Listen for messages from broker"""
        while self.connected:
            message = self.receive_message()
            if not message:
                print(f"[Node {self.node_id}] Connection to broker lost")
                self.connected = False
                break
            
            msg_type = message.get('type')
            
            if msg_type == 'NEW_TASK':
                self.handle_new_task(message)
            elif msg_type == 'BLOCK_ACCEPTED':
                self.handle_block_accepted(message)
            elif msg_type == 'CANCEL_MINING':
                print(f"[Node {self.node_id}] Received cancellation signal")
                self.stop_mining.set()
                self.mining_active.clear()
    
    def connect_and_run(self):
        """Connect to broker and start mining"""
        print(f"\n[Node {self.node_id}] Connecting to broker at {self.broker_host}:{self.broker_port}")
        
        try:
            # Connect to broker
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.broker_host, self.broker_port))
            self.connected = True
            
            print(f"[Node {self.node_id}] Connected to broker")
            
            # Register with broker
            registration = {
                'type': 'REGISTER',
                'node_id': self.node_id
            }
            self.send_message(registration)
            
            # Start mining worker thread
            mining_thread = threading.Thread(target=self.mining_worker, daemon=True)
            mining_thread.start()
            
            # Start message listener (blocking)
            self.message_listener()
            
        except Exception as e:
            print(f"[Node {self.node_id}] Error: {e}")
        finally:
            self.connected = False
            if self.socket:
                self.socket.close()
            print(f"[Node {self.node_id}] Disconnected")


if __name__ == "__main__":
    # Get node ID from command line argument
    if len(sys.argv) > 1:
        node_id = int(sys.argv[1])
    else:
        node_id = 1
    
    miner = MiningNode(node_id=node_id)
    
    try:
        miner.connect_and_run()
    except KeyboardInterrupt:
        print(f"\n[Node {node_id}] Shutting down...")
        miner.connected = False

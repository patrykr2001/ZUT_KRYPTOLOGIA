"""
Zadanie 11.3 - Broker Node (Intermediary/Network Simulator)
Generates transaction hashes every 1 second and coordinates mining across 4 nodes.
"""
import socket
import pickle
import threading
import time
import random
import string
from datetime import datetime


class BrokerNode:
    def __init__(self, host='localhost', port=5000, difficulty=20):
        self.host = host
        self.port = port
        self.difficulty = difficulty
        
        # Blockchain state
        self.current_block_number = 0
        self.previous_hash = b'\x00' * 32  # Genesis block
        
        # Connected mining nodes
        self.mining_nodes = {}  # {node_id: socket}
        self.nodes_lock = threading.Lock()
        
        # Server socket
        self.server_socket = None
        self.running = False
        
        # Transaction generation
        self.current_transactions = []
        
    def generate_random_transactions(self, count=5):
        """Generate random transaction strings"""
        transactions = []
        for i in range(count):
            tx_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            amount = random.randint(1, 1000)
            sender = ''.join(random.choices(string.ascii_uppercase, k=8))
            receiver = ''.join(random.choices(string.ascii_uppercase, k=8))
            tx = f"TX_{tx_id}: {sender} -> {receiver} [{amount} units]"
            transactions.append(tx)
        return transactions
    
    def send_message(self, sock, message):
        """Send pickled message with length prefix"""
        try:
            data = pickle.dumps(message)
            length = len(data).to_bytes(4, byteorder='big')
            sock.sendall(length + data)
            return True
        except Exception as e:
            print(f"[BROKER] Error sending message: {e}")
            return False
    
    def receive_message(self, sock):
        """Receive pickled message with length prefix"""
        try:
            # Receive length prefix (4 bytes)
            length_data = b''
            while len(length_data) < 4:
                chunk = sock.recv(4 - len(length_data))
                if not chunk:
                    return None
                length_data += chunk
            
            message_length = int.from_bytes(length_data, byteorder='big')
            
            # Receive message data
            data = b''
            while len(data) < message_length:
                chunk = sock.recv(min(4096, message_length - len(data)))
                if not chunk:
                    return None
                data += chunk
            
            return pickle.loads(data)
        except Exception as e:
            print(f"[BROKER] Error receiving message: {e}")
            return None
    
    def broadcast_to_miners(self, message, exclude_node_id=None):
        """Broadcast message to all connected mining nodes"""
        with self.nodes_lock:
            dead_nodes = []
            for node_id, sock in self.mining_nodes.items():
                if exclude_node_id is not None and node_id == exclude_node_id:
                    continue
                
                if not self.send_message(sock, message):
                    dead_nodes.append(node_id)
            
            # Remove disconnected nodes
            for node_id in dead_nodes:
                print(f"[BROKER] Node {node_id} disconnected, removing from list")
                del self.mining_nodes[node_id]
    
    def handle_mining_node(self, client_socket, address):
        """Handle connection from a mining node"""
        node_id = None
        try:
            # Receive initial registration
            reg_message = self.receive_message(client_socket)
            if not reg_message or reg_message.get('type') != 'REGISTER':
                print(f"[BROKER] Invalid registration from {address}")
                client_socket.close()
                return
            
            node_id = reg_message['node_id']
            
            with self.nodes_lock:
                self.mining_nodes[node_id] = client_socket
            
            print(f"[BROKER] Node {node_id} registered from {address}")
            
            # Send initial mining task
            task_message = {
                'type': 'NEW_TASK',
                'transactions': self.current_transactions,
                'previous_hash': self.previous_hash,
                'block_number': self.current_block_number,
                'difficulty': self.difficulty
            }
            self.send_message(client_socket, task_message)
            
            # Listen for mined blocks from this node
            while self.running:
                message = self.receive_message(client_socket)
                if not message:
                    break
                
                if message['type'] == 'BLOCK_MINED':
                    self.handle_mined_block(message, node_id)
        
        except Exception as e:
            print(f"[BROKER] Error handling node {node_id}: {e}")
        finally:
            with self.nodes_lock:
                if node_id and node_id in self.mining_nodes:
                    del self.mining_nodes[node_id]
            client_socket.close()
            print(f"[BROKER] Node {node_id} connection closed")
    
    def handle_mined_block(self, message, node_id):
        """Process a mined block from a mining node"""
        block = message['block']
        attempts = message.get('attempts', 0)
        elapsed = message.get('elapsed', 0)
        
        # Check for desynchronization - reject if block number already mined
        if block.block_number != self.current_block_number:
            print(f"\n[BROKER] ❌ REJECTED block {block.block_number} from Node {node_id}")
            print(f"          Reason: Block {block.block_number} already mined (current: {self.current_block_number})")
            print(f"          Block hash: {block.block_hash.hex()[:16]}...")
            return
        
        # Accept the block
        print(f"\n{'='*80}")
        print(f"[BROKER] ✅ BLOCK ACCEPTED from Node {node_id}")
        print(f"{'='*80}")
        print(f"  Block Number:    {block.block_number}")
        print(f"  Block Hash:      {block.block_hash.hex()}")
        print(f"  Previous Hash:   {block.previous_hash.hex()}")
        print(f"  Merkle Root:     {block.merkle_root.hex()}")
        print(f"  Timestamp:       {datetime.fromtimestamp(block.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Nonce:           {block.nonce}")
        print(f"  Attempts:        {attempts:,}")
        print(f"  Time:            {elapsed:.2f}s")
        print(f"  Hash Rate:       {attempts/elapsed:.2f} H/s" if elapsed > 0 else "  Hash Rate:       N/A")
        print(f"{'='*80}\n")
        
        # Update blockchain state
        self.previous_hash = block.block_hash
        self.current_block_number += 1
        
        # Generate new transactions for next block
        self.current_transactions = self.generate_random_transactions()
        
        # Broadcast block acceptance and new mining task to all nodes
        acceptance_message = {
            'type': 'BLOCK_ACCEPTED',
            'block': block,
            'winning_node': node_id
        }
        self.broadcast_to_miners(acceptance_message)
        
        # Send new mining task
        new_task_message = {
            'type': 'NEW_TASK',
            'transactions': self.current_transactions,
            'previous_hash': self.previous_hash,
            'block_number': self.current_block_number,
            'difficulty': self.difficulty
        }
        self.broadcast_to_miners(new_task_message)
    
    def accept_connections(self):
        """Accept incoming connections from mining nodes"""
        print(f"[BROKER] Listening for mining nodes on {self.host}:{self.port}")
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                client_socket, address = self.server_socket.accept()
                print(f"[BROKER] New connection from {address}")
                
                # Handle each node in a separate thread
                thread = threading.Thread(
                    target=self.handle_mining_node,
                    args=(client_socket, address),
                    daemon=True
                )
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[BROKER] Error accepting connection: {e}")
    
    def transaction_generator(self):
        """Generate new transactions every second (not used in this implementation)"""
        # Note: We generate transactions only when a block is accepted
        # This thread is kept for potential future enhancements
        pass
    
    def start(self):
        """Start the broker node"""
        print("\n" + "="*80)
        print("BROKER NODE - Distributed PoW Simulation")
        print("="*80)
        print(f"Difficulty: {self.difficulty} leading zero bits")
        print(f"Listening on: {self.host}:{self.port}")
        print("="*80 + "\n")
        
        # Generate initial transactions
        self.current_transactions = self.generate_random_transactions()
        print(f"[BROKER] Initial transactions generated:")
        for tx in self.current_transactions:
            print(f"  - {tx}")
        print()
        
        # Create server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        
        self.running = True
        
        # Start accepting connections
        accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
        accept_thread.start()
        
        try:
            # Keep main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[BROKER] Shutting down...")
            self.running = False
            self.server_socket.close()


if __name__ == "__main__":
    broker = BrokerNode(host='localhost', port=5000, difficulty=20)
    broker.start()

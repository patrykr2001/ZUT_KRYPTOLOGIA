"""
Lab 07 - Blockchain Mining Component
Kryptologia - Patryk Rakowski 2025

Implementation of blockchain block mining with Merkle tree and proof-of-work.
"""

import hashlib
import time
from dataclasses import dataclass
from typing import List, Union


# ================================================================================
# MERKLE TREE IMPLEMENTATION
# ================================================================================

class MerkleTree:
    """
    Implementation of Merkle Tree for computing transaction root hash.
    """
    
    @staticmethod
    def compute_hash(data: Union[str, bytes]) -> bytes:
        """
        Compute SHA256 hash of data.
        
        Args:
            data: String or bytes to hash
            
        Returns:
            SHA256 hash as bytes
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).digest()
    
    @staticmethod
    def build_merkle_tree(transactions: List[Union[str, bytes]]) -> bytes:
        """
        Build Merkle tree from transaction hashes and return root hash.
        
        Args:
            transactions: List of transaction hashes (strings or bytes)
            
        Returns:
            Merkle root hash as bytes
        """
        if not transactions:
            return hashlib.sha256(b"").digest()
        
        # Convert all transactions to hashes if they aren't already
        current_level = [MerkleTree.compute_hash(tx) for tx in transactions]
        
        # Build tree level by level
        while len(current_level) > 1:
            next_level = []
            
            # Process pairs
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                
                # If odd number of elements, duplicate the last one
                if i + 1 < len(current_level):
                    right = current_level[i + 1]
                else:
                    right = current_level[i]
                
                # Hash the concatenation of left and right
                combined = left + right
                parent_hash = hashlib.sha256(combined).digest()
                next_level.append(parent_hash)
            
            current_level = next_level
        
        return current_level[0]


# ================================================================================
# BLOCK STRUCTURE
# ================================================================================

@dataclass
class Block:
    """
    Blockchain block structure.
    """
    merkle_root: bytes          # Merkle tree root hash of all transactions
    previous_hash: bytes        # Hash of previous block
    timestamp: int              # Unix timestamp
    block_number: int           # Block number in chain
    nonce: int                  # Proof-of-work nonce
    block_hash: bytes           # Hash of the entire block


# ================================================================================
# BLOCK MINER
# ================================================================================

class BlockMiner:
    """
    Component for mining blockchain blocks with proof-of-work.
    """
    
    def __init__(self, difficulty: int = 10):
        """
        Initialize block miner.
        
        Args:
            difficulty: Number of leading zero bits required (j parameter)
        """
        self.difficulty = difficulty
    
    @staticmethod
    def hash_has_leading_zero_bits(hash_bytes: bytes, num_bits: int) -> bool:
        """
        Check if hash has specified number of leading zero bits.
        
        Args:
            hash_bytes: Hash to check
            num_bits: Number of leading zero bits required
            
        Returns:
            True if hash has enough leading zero bits
        """
        for bit_index in range(num_bits):
            byte_index = bit_index // 8
            bit_position = 7 - (bit_index % 8)  # MSB first
            
            if byte_index >= len(hash_bytes):
                return False
            
            # Check if bit is set
            if (hash_bytes[byte_index] >> bit_position) & 1:
                return False
        
        return True
    
    def compute_block_hash(self, merkle_root: bytes, previous_hash: bytes,
                          timestamp: int, block_number: int, nonce: int) -> bytes:
        """
        Compute hash of block components.
        
        Args:
            merkle_root: Merkle tree root hash
            previous_hash: Previous block hash
            timestamp: Block timestamp
            block_number: Block number
            nonce: Nonce value
            
        Returns:
            SHA256 hash of all components
        """
        # Concatenate all block data
        block_data = (
            merkle_root +
            previous_hash +
            timestamp.to_bytes(8, byteorder='big') +
            block_number.to_bytes(8, byteorder='big') +
            nonce.to_bytes(8, byteorder='big')
        )
        
        return hashlib.sha256(block_data).digest()
    
    def mine_block(self, transactions: List[Union[str, bytes]], 
                   previous_hash: Union[str, bytes],
                   block_number: int = 0) -> tuple[Block, int, float]:
        """
        Mine a new block with proof-of-work.
        
        Args:
            transactions: List of transaction hashes
            previous_hash: Hash of previous block
            block_number: Block number in chain
            
        Returns:
            Tuple of (mined Block, attempts made, time taken in seconds)
        """
        print(f"\n{'='*80}")
        print(f"MINING BLOCK #{block_number}")
        print(f"{'='*80}")
        print(f"Difficulty: {self.difficulty} leading zero bits")
        print(f"Transactions: {len(transactions)}")
        
        # Convert previous_hash to bytes if needed
        if isinstance(previous_hash, str):
            previous_hash = previous_hash.encode('utf-8')
        
        # Compute Merkle root
        print("\nComputing Merkle tree root...")
        merkle_root = MerkleTree.build_merkle_tree(transactions)
        print(f"Merkle root: {merkle_root.hex()}")
        
        # Get current timestamp
        timestamp = int(time.time())
        print(f"Timestamp: {timestamp}")
        
        # Start mining
        print(f"\nSearching for valid nonce...")
        start_time = time.time()
        nonce = 0
        attempts = 0
        
        while True:
            block_hash = self.compute_block_hash(
                merkle_root, previous_hash, timestamp, block_number, nonce
            )
            attempts += 1
            
            # Check if hash meets difficulty requirement
            if self.hash_has_leading_zero_bits(block_hash, self.difficulty):
                end_time = time.time()
                elapsed = end_time - start_time
                
                print(f"\n{'='*80}")
                print(f"BLOCK MINED SUCCESSFULLY!")
                print(f"{'='*80}")
                print(f"Nonce found: {nonce}")
                print(f"Attempts: {attempts:,}")
                print(f"Time: {elapsed:.3f} seconds")
                print(f"Hash rate: {attempts/elapsed:.2f} hashes/second")
                print(f"Block hash: {block_hash.hex()}")
                
                # Verify leading zero bits
                zero_bits = self._count_leading_zero_bits(block_hash)
                print(f"Leading zero bits: {zero_bits}")
                
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
            
            # Progress indicator
            if attempts % 100000 == 0:
                print(f"  Attempts: {attempts:,} ({attempts/(time.time()-start_time):.0f} H/s)")
    
    @staticmethod
    def _count_leading_zero_bits(hash_bytes: bytes) -> int:
        """Count the number of leading zero bits in hash."""
        count = 0
        for byte in hash_bytes:
            if byte == 0:
                count += 8
            else:
                # Count leading zeros in this byte
                for i in range(7, -1, -1):
                    if (byte >> i) & 1:
                        return count
                    count += 1
        return count
    
    def verify_block(self, block: Block) -> bool:
        """
        Verify that a block is valid.
        
        Args:
            block: Block to verify
            
        Returns:
            True if block is valid
        """
        # Recompute block hash
        computed_hash = self.compute_block_hash(
            block.merkle_root,
            block.previous_hash,
            block.timestamp,
            block.block_number,
            block.nonce
        )
        
        # Check if hash matches
        if computed_hash != block.block_hash:
            return False
        
        # Check if hash meets difficulty requirement
        return self.hash_has_leading_zero_bits(block.block_hash, self.difficulty)

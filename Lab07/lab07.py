"""
Lab 07 - Blockchain and Cryptocurrency
Kryptologia - Patryk Rakowski 2025

Zadanie 11.1 - Implementation of blockchain block mining component
with Merkle tree and proof-of-work algorithm.
"""

import time
from blockchain_mining import BlockMiner, Block, MerkleTree


# ================================================================================
# ZADANIE 11.1 - BLOCKCHAIN BLOCK MINING
# ================================================================================

def zadanie_11_1_demo_basic():
    """
    Basic demonstration of block mining with low difficulty.
    """
    print("\n" + "="*80)
    print("ZADANIE 11.1 - BLOCKCHAIN BLOCK MINING - BASIC DEMO")
    print("="*80)
    
    # Sample transactions
    transactions = [
        "tx1: Alice -> Bob: 10 BTC",
        "tx2: Bob -> Charlie: 5 BTC",
        "tx3: Charlie -> David: 3 BTC",
        "tx4: David -> Eve: 2 BTC"
    ]
    
    print("\nTransactions to include in block:")
    for i, tx in enumerate(transactions, 1):
        print(f"  {i}. {tx}")
    
    # Previous block hash (genesis block)
    previous_hash = "0" * 64
    print(f"\nPrevious block hash: {previous_hash}")
    
    # Mine block with difficulty 10 (easy)
    print(f"\n{'='*80}")
    print("Mining block with difficulty = 10 bits")
    print(f"{'='*80}")
    
    miner = BlockMiner(difficulty=10)
    block, attempts, elapsed = miner.mine_block(transactions, previous_hash, block_number=1)
    
    print(f"\n{'='*80}")
    print("BLOCK DETAILS")
    print(f"{'='*80}")
    print(f"Block number: {block.block_number}")
    print(f"Merkle root: {block.merkle_root.hex()}")
    print(f"Previous hash: {block.previous_hash[:32].decode('utf-8', errors='ignore')}...")
    print(f"Timestamp: {block.timestamp}")
    print(f"Nonce: {block.nonce}")
    print(f"Block hash: {block.block_hash.hex()}")
    
    # Verify block
    print(f"\n{'='*80}")
    print("BLOCK VERIFICATION")
    print(f"{'='*80}")
    is_valid = miner.verify_block(block)
    print(f"Block is valid: {is_valid}")


def zadanie_11_1_demo_difficulty():
    """
    Demonstration of mining with different difficulty levels.
    """
    print("\n" + "="*80)
    print("ZADANIE 11.1 - MINING WITH DIFFERENT DIFFICULTY LEVELS")
    print("="*80)
    
    transactions = [
        "tx1: Payment 1",
        "tx2: Payment 2",
        "tx3: Payment 3"
    ]
    
    previous_hash = "genesis_block"
    
    difficulties = [18, 24, 27]
    results = []
    
    for difficulty in difficulties:
        print(f"\n{'#'*80}")
        print(f"TESTING DIFFICULTY: {difficulty} bits")
        print(f"{'#'*80}")
        print(f"Expected attempts: ~{2**difficulty:,}")
        
        miner = BlockMiner(difficulty=difficulty)
        block, attempts, elapsed = miner.mine_block(transactions, previous_hash, block_number=1)
        
        results.append({
            'difficulty': difficulty,
            'attempts': attempts,
            'time': elapsed,
            'hash_rate': attempts / elapsed
        })
    
    # Summary
    print(f"\n{'='*80}")
    print("DIFFICULTY COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(f"{'Difficulty':<12} {'Attempts':<15} {'Time (s)':<12} {'Hash Rate (H/s)':<20}")
    print("-" * 80)
    for r in results:
        print(f"{r['difficulty']:<12} {r['attempts']:<15,} {r['time']:<12.3f} {r['hash_rate']:<20,.0f}")


def zadanie_11_1_demo_merkle_tree():
    """
    Demonstration of Merkle tree computation.
    """
    print("\n" + "="*80)
    print("ZADANIE 11.1 - MERKLE TREE DEMONSTRATION")
    print("="*80)
    
    transactions = [
        "Transaction 1: Alice sends 50 BTC to Bob",
        "Transaction 2: Bob sends 30 BTC to Charlie",
        "Transaction 3: Charlie sends 20 BTC to David",
        "Transaction 4: David sends 10 BTC to Eve",
        "Transaction 5: Eve sends 5 BTC to Frank"
    ]
    
    print("\nTransactions:")
    for i, tx in enumerate(transactions, 1):
        print(f"  {i}. {tx}")
    
    print(f"\n{'='*80}")
    print("Building Merkle Tree...")
    print(f"{'='*80}")
    
    # Compute individual transaction hashes
    print("\nStep 1: Hash each transaction (Leaf nodes)")
    print("-" * 80)
    tx_hashes = []
    for i, tx in enumerate(transactions, 1):
        tx_hash = MerkleTree.compute_hash(tx)
        tx_hashes.append(tx_hash)
        print(f"TX{i} hash: {tx_hash.hex()}")
    
    # Build Merkle tree
    print("\nStep 2: Build Merkle tree from leaf hashes")
    print("-" * 80)
    merkle_root = MerkleTree.build_merkle_tree(transactions)
    print(f"\nMerkle Root: {merkle_root.hex()}")
    
    # Demonstrate that changing one transaction changes the root
    print(f"\n{'='*80}")
    print("Demonstrating Merkle Tree Property")
    print(f"{'='*80}")
    print("\nChanging Transaction 3...")
    modified_transactions = transactions.copy()
    modified_transactions[2] = "Transaction 3: Charlie sends 25 BTC to David"
    
    modified_merkle_root = MerkleTree.build_merkle_tree(modified_transactions)
    print(f"Original Merkle Root:  {merkle_root.hex()}")
    print(f"Modified Merkle Root:  {modified_merkle_root.hex()}")
    print(f"\nRoots are different: {merkle_root != modified_merkle_root}")


def zadanie_11_1_demo_blockchain():
    """
    Demonstration of mining multiple blocks to form a blockchain.
    """
    print("\n" + "="*80)
    print("ZADANIE 11.1 - BLOCKCHAIN DEMONSTRATION")
    print("="*80)
    
    # Create blockchain
    blockchain = []
    difficulty = 12
    miner = BlockMiner(difficulty=difficulty)
    
    # Genesis block
    print("\nCreating genesis block...")
    genesis_transactions = ["Genesis block - Initial distribution"]
    genesis_hash = "0" * 64
    
    block0, attempts0, time0 = miner.mine_block(
        genesis_transactions, 
        genesis_hash, 
        block_number=0
    )
    blockchain.append(block0)
    
    # Block 1
    block1_transactions = [
        "tx1: Alice -> Bob: 10 BTC",
        "tx2: Bob -> Charlie: 5 BTC"
    ]
    block1, attempts1, time1 = miner.mine_block(
        block1_transactions,
        block0.block_hash,
        block_number=1
    )
    blockchain.append(block1)
    
    # Block 2
    block2_transactions = [
        "tx3: Charlie -> David: 3 BTC",
        "tx4: David -> Eve: 2 BTC",
        "tx5: Eve -> Frank: 1 BTC"
    ]
    block2, attempts2, time2 = miner.mine_block(
        block2_transactions,
        block1.block_hash,
        block_number=2
    )
    blockchain.append(block2)
    
    # Display blockchain
    print(f"\n{'='*80}")
    print("BLOCKCHAIN SUMMARY")
    print(f"{'='*80}")
    print(f"Total blocks: {len(blockchain)}")
    print(f"Difficulty: {difficulty} bits")
    print(f"\n{'Block':<8} {'Hash':<66} {'Prev Hash':<20}")
    print("-" * 100)
    
    for block in blockchain:
        prev_hash_display = block.previous_hash.hex()[:16] + "..."
        print(f"{block.block_number:<8} {block.block_hash.hex():<66} {prev_hash_display:<20}")
    
    # Verify blockchain integrity
    print(f"\n{'='*80}")
    print("BLOCKCHAIN VERIFICATION")
    print(f"{'='*80}")
    
    all_valid = True
    for i, block in enumerate(blockchain):
        is_valid = miner.verify_block(block)
        print(f"Block {i}: {'VALID' if is_valid else 'INVALID'}")
        
        if i > 0:
            # Check if previous hash matches
            prev_block_hash = blockchain[i-1].block_hash
            matches = block.previous_hash == prev_block_hash
            print(f"  Previous hash link: {'OK' if matches else 'BROKEN'}")
            all_valid = all_valid and matches
        
        all_valid = all_valid and is_valid
    
    print(f"\nBlockchain integrity: {'VALID' if all_valid else 'INVALID'}")


def zadanie_11_1_interactive():
    """
    Interactive mode for custom block mining.
    """
    print("\n" + "="*80)
    print("ZADANIE 11.1 - INTERACTIVE BLOCK MINING")
    print("="*80)
    
    # Get difficulty
    print("\nDifficulty levels guide:")
    print("  10 bits: ~1,000 attempts (instant)")
    print("  15 bits: ~32,000 attempts (1-2 seconds)")
    print("  20 bits: ~1,000,000 attempts (20-30 seconds)")
    print("  25 bits: ~33,000,000 attempts (10-15 minutes)")
    print("  30 bits: ~1,000,000,000 attempts (several hours)")
    
    try:
        difficulty = int(input("\nEnter difficulty (number of leading zero bits): "))
        if difficulty < 1 or difficulty > 30:
            print("Warning: Difficulty should be between 1 and 30")
            return
    except ValueError:
        print("Invalid input")
        return
    
    # Get transactions
    print("\nEnter transactions (empty line to finish):")
    transactions = []
    i = 1
    while True:
        tx = input(f"Transaction {i}: ").strip()
        if not tx:
            break
        transactions.append(tx)
        i += 1
    
    if not transactions:
        print("No transactions entered. Using default transactions.")
        transactions = ["Default transaction 1", "Default transaction 2"]
    
    # Get previous hash
    previous_hash = input("\nEnter previous block hash (or press Enter for default): ").strip()
    if not previous_hash:
        previous_hash = "0" * 64
    
    # Mine block
    miner = BlockMiner(difficulty=difficulty)
    block, attempts, elapsed = miner.mine_block(transactions, previous_hash, block_number=1)
    
    print(f"\n{'='*80}")
    print("Mining completed successfully!")
    print(f"{'='*80}")


# ================================================================================
# MAIN MENU
# ================================================================================

def main():
    """Main menu for Lab 07."""
    while True:
        print("\n" + "="*80)
        print("LAB 07 - BLOCKCHAIN AND CRYPTOCURRENCY")
        print("="*80)
        print("\nZadanie 11.1 - Block Mining Component:")
        print("  1. Basic demo (difficulty 10)")
        print("  2. Difficulty comparison (10, 15, 20 bits)")
        print("  3. Merkle tree demonstration")
        print("  4. Blockchain demonstration (multiple blocks)")
        print("  5. Interactive mode")
        print("\n  0. Exit")
        
        choice = input("\nSelect option: ").strip()
        
        if choice == '1':
            zadanie_11_1_demo_basic()
        elif choice == '2':
            zadanie_11_1_demo_difficulty()
        elif choice == '3':
            zadanie_11_1_demo_merkle_tree()
        elif choice == '4':
            zadanie_11_1_demo_blockchain()
        elif choice == '5':
            zadanie_11_1_interactive()
        elif choice == '0':
            print("\nExiting...")
            break
        else:
            print("\nInvalid option!")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()

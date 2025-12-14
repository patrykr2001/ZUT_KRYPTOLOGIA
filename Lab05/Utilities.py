from typing import List

def display_binary_blocks(bits: List[int], label: str, block_size: int = 8):
    """
    Wyświetla strumień bitów w blokach o określonym rozmiarze.
    
    Args:
        bits: lista bitów do wyświetlenia
        label: etykieta opisu
        block_size: rozmiar bloku (domyślnie 8 bitów)
    """
    print(f"\n{label}:")
    print(f"Długość: {len(bits)} bitów")
    
    if len(bits) == 0:
        print("  (brak danych)")
        return
    
    # Dzielimy na bloki
    for i in range(0, len(bits), block_size * 8):  # 8 bloków na linię
        line_bits = bits[i:i + block_size * 8]
        line_blocks = []
        
        for j in range(0, len(line_bits), block_size):
            block = line_bits[j:j + block_size]
            block_str = ''.join(map(str, block))
            line_blocks.append(block_str)
        
        print(f"  {' '.join(line_blocks)}")


def bits_to_hex(bits: List[int]) -> str:
    """
    Konwertuje listę bitów na ciąg heksadecymalny.
    
    Args:
        bits: lista bitów
        
    Returns:
        Ciąg heksadecymalny
    """
    # Dopełniamy do wielokrotności 4 bitów
    padded_bits = bits + [0] * ((4 - len(bits) % 4) % 4)
    
    hex_str = ""
    for i in range(0, len(padded_bits), 4):
        nibble = padded_bits[i:i+4]
        value = sum(bit << (3-j) for j, bit in enumerate(nibble))
        hex_str += format(value, 'x')
    
    return hex_str


def parse_taps(tap_string: str) -> List[int]:
    """
    Parsuje string z pozycjami tapów oddzielonymi przecinkami.
    
    Args:
        tap_string: string z pozycjami, np. "16,14,13,11"
        
    Returns:
        Lista pozycji tapów
    """
    try:
        taps = [int(x.strip()) for x in tap_string.split(',')]
        return taps
    except ValueError:
        raise ValueError("Nieprawidłowy format tapów. Użyj liczb oddzielonych przecinkami.")


def parse_seed(seed_string: str, length: int) -> int:
    """
    Parsuje string z seedem (binarny lub dziesiętny).
    
    Args:
        seed_string: string z seedem (np. "1010" lub "10")
        length: długość rejestru
        
    Returns:
        Seed jako liczba całkowita
    """
    seed_string = seed_string.strip()
    
    # Próbujemy zinterpretować jako binarny (same 0 i 1)
    if all(c in '01' for c in seed_string):
        seed = int(seed_string, 2)
    else:
        # Interpretujemy jako dziesiętny
        seed = int(seed_string)
    
    if seed == 0:
        raise ValueError("Seed nie może być zerem")
    
    max_value = (1 << length) - 1
    if seed > max_value:
        raise ValueError(f"Seed przekracza maksymalną wartość dla {length}-bitowego rejestru ({max_value})")
    
    return seed

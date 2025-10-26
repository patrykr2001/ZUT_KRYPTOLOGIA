from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import binascii


class PaddingOracle:
    def __init__(self):
        self.key = get_random_bytes(16)  # Klucz AES-128
        self.iv = get_random_bytes(16)   # Wektor inicjalizacyjny
        self.oracle_queries = 0          # Licznik zapytań do wyrocznika
        
    def encrypt(self, plaintext: str) -> tuple[bytes, bytes]:
        cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
        padded_plaintext = pad(plaintext.encode('utf-8'), AES.block_size)
        ciphertext = cipher.encrypt(padded_plaintext)
        return ciphertext, self.iv
    
    def check_padding(self, ciphertext: bytes, iv: bytes) -> bool:
        self.oracle_queries += 1
        try:
            cipher = AES.new(self.key, AES.MODE_CBC, iv=iv)
            plaintext = cipher.decrypt(ciphertext)
            unpad(plaintext, AES.block_size)  # Sprawdza poprawność paddingu
            return True
        except ValueError:
            return False
    
    def get_oracle_queries(self) -> int:
        return self.oracle_queries


def display_hex_blocks(data: bytes, label: str, block_size: int = 16):
    print(f"\n{label}:")
    hex_str = binascii.hexlify(data).decode('utf-8')
    for i in range(0, len(hex_str), block_size * 2):
        block = hex_str[i:i + block_size * 2]
        print(f"  Blok {i // (block_size * 2) + 1}: {block}")


def zadanie1_attack_last_byte(ciphertext: bytes, iv: bytes, oracle: PaddingOracle) -> int:
    block_size = 16
    num_blocks = len(ciphertext) // block_size
    
    if num_blocks < 2:
        print("Atak wymaga co najmniej 2 bloków.")
        return None
    
    # Dla wielu bloków modyfikujemy przedostatni blok
    previous_block = bytearray(ciphertext[(num_blocks-2)*block_size:(num_blocks-1)*block_size])
    target_block = ciphertext[(num_blocks-1)*block_size:]
    
    # Atakujemy ostatni bajt (indeks 15)
    byte_position = block_size - 1
    original_byte = previous_block[byte_position]
    
    print(f"\nOryginalna wartość bajtu na pozycji {byte_position}: 0x{original_byte:02x}")
    
    # Najpierw sprawdzamy czy oryginalny padding już jest poprawny
    # To pozwoli nam określić rzeczywistą długość paddingu
    original_valid = oracle.check_padding(ciphertext, iv)
    print(f"\nOryginalny szyfrogram ma {'POPRAWNY' if original_valid else 'NIEPOPRAWNY'} padding")
    
    # Próbujemy wszystkie możliwe wartości bajtu (0-255)
    valid_guesses = []
    
    for guess in range(256):
        # Modyfikujemy bajt w poprzednim bloku
        previous_block[byte_position] = guess
        
        # Przygotowujemy zmodyfikowany szyfrogram
        modified_ciphertext = ciphertext[:(num_blocks-2)*block_size] + bytes(previous_block) + target_block
        
        # Sprawdzamy padding używając wyrocznika
        if oracle.check_padding(modified_ciphertext, iv):
            valid_guesses.append(guess)
    
    print(f"\nZnaleziono {len(valid_guesses)} wartości z poprawnym paddingiem:")
    for g in valid_guesses:
        print(f"  - 0x{g:02x}")
    
    # Wybieramy pierwszą wartość różną od oryginału (jeśli istnieje)
    # lub pierwszą znalezioną wartość
    guess = None
    for g in valid_guesses:
        if g != original_byte:
            guess = g
            break
    
    if guess is None and valid_guesses:
        guess = valid_guesses[0]
    
    if guess is not None:
        print(f"\nUżywam wartości: 0x{guess:02x} do obliczenia bajtu plaintextu")
        
        # Obliczamy wartość deszyfrowanego bajtu
        # P[i] = D(C[i]) XOR C[i-1]
        # Jeśli padding jest poprawny i wynosi 0x01, to:
        # D(C[last_block])[15] XOR modified_byte = 0x01
        # D(C[last_block])[15] = 0x01 XOR modified_byte
        decrypted_byte = 0x01 ^ guess
        
        # Teraz obliczamy oryginalny bajt plaintextu
        # P[15] = D(C[last_block])[15] XOR C[prev_block][15]
        plaintext_byte = decrypted_byte ^ original_byte
        
        print(f"\nWyliczenia:")
        print(f"  Zmodyfikowany bajt (C'[{byte_position}]): 0x{guess:02x}")
        print(f"  Oczekiwany padding: 0x01")
        print(f"  Wartość deszyfrowana (D[{byte_position}]): 0x{decrypted_byte:02x} = 0x01 XOR 0x{guess:02x}")
        print(f"  Oryginalny bajt bloku (C[{byte_position}]): 0x{original_byte:02x}")
        print(f"  Bajt plaintextu (P[{byte_position}]): 0x{plaintext_byte:02x} = 0x{decrypted_byte:02x} XOR 0x{original_byte:02x}")
        
        # Próbujemy zinterpretować jako znak ASCII
        if 32 <= plaintext_byte <= 126:
            print(f"  Interpretacja ASCII: '{chr(plaintext_byte)}'")
        else:
            print(f"  Interpretacja: bajt padding = {plaintext_byte}")
        
        return plaintext_byte
    
    print("\n  Nie znaleziono poprawnego paddingu!")
    return None


def zadanie2_attack_last_block(ciphertext: bytes, iv: bytes, oracle: PaddingOracle) -> bytes:
    block_size = 16
    num_blocks = len(ciphertext) // block_size
    
    if num_blocks < 2:
        print("Atak wymaga co najmniej 2 bloków (nie znamy IV).")
        return None
    
    # Pobieramy przedostatni blok (ten, który będziemy modyfikować)
    previous_block_original = bytearray(ciphertext[(num_blocks-2)*block_size:(num_blocks-1)*block_size])
    target_block = ciphertext[(num_blocks-1)*block_size:]
    
    # Tablica na wartości pośrednie (decrypt wartości)
    intermediate_values = bytearray(block_size)
    
    # Tablica na odczytany plaintext
    recovered_plaintext = bytearray(block_size)
    
    # Atakujemy każdy bajt od końca do początku
    for byte_position in range(block_size - 1, -1, -1):
        padding_value = block_size - byte_position  # 1, 2, 3, ..., 16
        
        print(f"{'─'*70}")
        print(f"Pozycja {byte_position}: Wymuszamy padding = 0x{padding_value:02x}")
        
        # Tworzymy zmodyfikowany blok
        modified_block = bytearray(previous_block_original)
        
        # Ustawiamy już znane bajty na końcu, aby uzyskać odpowiedni padding
        for i in range(byte_position + 1, block_size):
            # Dla padding = N, wszystkie ostatnie N bajtów muszą mieć wartość N
            # modified[i] XOR intermediate[i] = padding_value
            # modified[i] = intermediate[i] XOR padding_value
            modified_block[i] = intermediate_values[i] ^ padding_value
        
        # Szukamy wartości dla aktualnego bajtu
        found = False
        valid_guesses = []
        
        for guess in range(256):
            modified_block[byte_position] = guess
            
            # Tworzymy zmodyfikowany ciphertext
            modified_ciphertext = ciphertext[:(num_blocks-2)*block_size] + bytes(modified_block) + target_block
            
            # Sprawdzamy padding
            if oracle.check_padding(modified_ciphertext, iv):
                valid_guesses.append(guess)
        
        # Wybieramy odpowiednią wartość
        # Dla pierwszego bajtu (pozycja 15) może być wiele wartości (oryginalny padding)
        # Wybieramy wartość różną od oryginalnej (jeśli istnieje)
        selected_guess = None
        
        if byte_position == block_size - 1:
            # Pierwszy bajt - wybieramy wartość różną od oryginału
            for g in valid_guesses:
                if g != previous_block_original[byte_position]:
                    selected_guess = g
                    break
            # Jeśli nie znaleziono innej, użyj pierwszej
            if selected_guess is None and valid_guesses:
                selected_guess = valid_guesses[0]
        else:
            # Kolejne bajty - powinna być tylko jedna poprawna wartość
            if valid_guesses:
                selected_guess = valid_guesses[0]
        
        if selected_guess is not None:
            # Obliczamy wartość pośrednią
            intermediate_values[byte_position] = selected_guess ^ padding_value
            
            # Obliczamy oryginalny bajt plaintextu
            recovered_plaintext[byte_position] = intermediate_values[byte_position] ^ previous_block_original[byte_position]
            
            found = True
            
            # Wyświetlamy informacje
            print(f"   Znaleziono dla guess=0x{selected_guess:02x}")
            print(f"    Intermediate[{byte_position}] = 0x{intermediate_values[byte_position]:02x} = 0x{selected_guess:02x} XOR 0x{padding_value:02x}")
            print(f"    Plaintext[{byte_position}] = 0x{recovered_plaintext[byte_position]:02x} = 0x{intermediate_values[byte_position]:02x} XOR 0x{previous_block_original[byte_position]:02x}")
            
            if 32 <= recovered_plaintext[byte_position] <= 126:
                print(f"    ASCII: '{chr(recovered_plaintext[byte_position])}'")
            else:
                print(f"    Wartość: {recovered_plaintext[byte_position]} (padding lub znak specjalny)")
        
        if not found:
            print(f"   Nie znaleziono poprawnej wartości dla pozycji {byte_position}")
            print(f"    Znaleziono {len(valid_guesses)} poprawnych wartości: {[hex(g) for g in valid_guesses]}")
            return None
    
    print(f"\n{'='*70}")
    print("Cały blok został odczytany!")
    print(f"{'='*70}")
    
    return bytes(recovered_plaintext)


def zad1(ciphertext: bytes, iv: bytes, oracle: PaddingOracle, padded: bytes):
    # ZADANIE 1: Ostatni bajt
        recovered_byte = zadanie1_attack_last_byte(ciphertext, iv, oracle)
        
        if recovered_byte is not None:
            print(f"\n Atak zakończony sukcesem")
            print(f"  Odczytany ostatni bajt: 0x{recovered_byte:02x} ({recovered_byte})")
            
            if 32 <= recovered_byte <= 126:
                print(f"  Znak ASCII: '{chr(recovered_byte)}'")
            
            # Sprawdzamy poprawność
            actual_last_byte = padded[-1]
            print(f"\n  Rzeczywisty ostatni bajt: 0x{actual_last_byte:02x} ({actual_last_byte})")
            
            if recovered_byte == actual_last_byte:
                print(f"  Poprawnie odczytano ostatni bajt")
            else:
                print(f"   BŁĄD - wartości się nie zgadzają")
        else:
            print("\n Atak nie powiódł się")

        print(f"\nLiczba zapytań do wyrocznika: {oracle.get_oracle_queries()}")


def zad2(ciphertext: bytes, iv: bytes, oracle: PaddingOracle, padded: bytes):
    # ZADANIE 2: Cały blok
        recovered_block = zadanie2_attack_last_block(ciphertext, iv, oracle)
        
        if recovered_block is not None:
            print(f"\nAtak zakończony sukcesem!")
            print(f"\nOdczytany blok (hex): {binascii.hexlify(recovered_block).decode('utf-8')}")
            
            # Wyświetlamy bajt po bajcie
            print(f"\nOdczytany blok (bajty):")
            for i, b in enumerate(recovered_block):
                if 32 <= b <= 126:
                    char_repr = f"'{chr(b)}'"
                else:
                    char_repr = f"pad={b}"
                print(f"  [{i:2d}] 0x{b:02x} ({b:3d}) {char_repr}")
            
            # Próbujemy zdekodować jako tekst
            try:
                # Usuwamy padding
                recovered_text = unpad(recovered_block, AES.block_size).decode('utf-8')
                print(f"\nOdczytany tekst: '{recovered_text}'")
            except:
                # Jeśli to nie ostatni blok z paddingiem, wyświetlamy surowy tekst
                try:
                    recovered_text = recovered_block.decode('utf-8', errors='ignore')
                    print(f"\nOdczytany tekst (bez usuwania paddingu): '{recovered_text}'")
                except:
                    print(f"\nNie można zdekodować jako tekst")
            
            # Sprawdzamy poprawność
            actual_last_block = padded[-16:]
            print(f"\nRzeczywisty ostatni blok (hex): {binascii.hexlify(actual_last_block).decode('utf-8')}")
            
            if recovered_block == actual_last_block:
                print(f"Odczytano poprawnie cały blok")
            else:
                print(f"BŁĄD - bloki się nie zgadzają")
                # Pokazujemy różnice
                print("\nRóżnice:")
                for i in range(16):
                    if recovered_block[i] != actual_last_block[i]:
                        print(f"  Pozycja {i}: odczytano 0x{recovered_block[i]:02x}, powinno być 0x{actual_last_block[i]:02x}")
        else:
            print("\n Atak nie powiódł się")
        
        print(f"\nLiczba zapytań do wyrocznika: {oracle.get_oracle_queries()}")


def zad3(ciphertext: bytes, iv: bytes, oracle: PaddingOracle, padded: bytes):
    block_size = 16
    num_blocks = len(ciphertext) // block_size
    
    if num_blocks < 2:
        print("Potrzebne są co najmniej 2 bloki do przeprowadzenia ataku.")
        return
    
    recovered_blocks = []
    
    for block_idx in range(1, num_blocks):
        if block_idx == 0:
            continue
        else:
            previous_block_original = bytearray(ciphertext[(block_idx-1)*block_size:block_idx*block_size])
        
        target_block = ciphertext[block_idx*block_size:(block_idx+1)*block_size]
        
        intermediate_values = bytearray(block_size)
        recovered_plaintext = bytearray(block_size)
        
        for byte_position in range(block_size - 1, -1, -1):
            padding_value = block_size - byte_position
            
            modified_block = bytearray(previous_block_original)
            
            for i in range(byte_position + 1, block_size):
                modified_block[i] = intermediate_values[i] ^ padding_value
            
            valid_guesses = []
            
            for guess in range(256):
                modified_block[byte_position] = guess
                
                modified_ciphertext = ciphertext[:(block_idx-1)*block_size] + bytes(modified_block) + target_block
                modified_iv = iv
                
                if oracle.check_padding(modified_ciphertext, modified_iv):
                    valid_guesses.append(guess)
            
            selected_guess = None
            
            if byte_position == block_size - 1:
                for g in valid_guesses:
                    if g != previous_block_original[byte_position]:
                        selected_guess = g
                        break
                if selected_guess is None and valid_guesses:
                    selected_guess = valid_guesses[0]
            else:
                if valid_guesses:
                    selected_guess = valid_guesses[0]
            
            if selected_guess is not None:
                intermediate_values[byte_position] = selected_guess ^ padding_value
                recovered_plaintext[byte_position] = intermediate_values[byte_position] ^ previous_block_original[byte_position]
            else:
                print(f"   Nie znaleziono poprawnej wartości dla pozycji {byte_position}")
                return
        
        recovered_blocks.append(bytes(recovered_plaintext))
    
    for idx, block in enumerate(recovered_blocks):
        try:
            if idx == len(recovered_blocks) - 1:
                try:
                    text = unpad(block, AES.block_size).decode('utf-8', errors='ignore')
                except:
                    text = block.decode('utf-8', errors='ignore')
            else:
                text = block.decode('utf-8', errors='ignore')
            
            print(f"Blok {idx + 2}: {text}")
        except:
            print(f"Blok {idx + 2}: {binascii.hexlify(block).decode('utf-8')}")
    
    print(f"Liczba zapytań do wyrocznika: {oracle.get_oracle_queries()}")


def main():
    print("DEMONSTRACJA ATAKU PADDING ORACLE")
    print("Laboratorium 2 - Kryptologia")
    print("Patryk Rakowski 2025")
    
    plaintext = input("\nPodaj tekst do zaszyfrowania: ")
    
    oracle = PaddingOracle()
    ciphertext, iv = oracle.encrypt(plaintext)
    
    display_hex_blocks(ciphertext, "Szyfrogram")

    padded = pad(plaintext.encode('utf-8'), AES.block_size)
    
    # zad1(ciphertext, iv, oracle, padded)
    # zad2(ciphertext, iv, oracle, padded)
    zad3(ciphertext, iv, oracle, padded)


if __name__ == "__main__":
    main()

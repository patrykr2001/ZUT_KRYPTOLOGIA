from Crypto.Util.Padding import pad
import binascii

def encode_in_hex_with_padding(plaintext: str):
    # Zamieniamy tekst na bajty
    byte_data = plaintext.encode('utf-8')
    # Dodajemy padding PKCS7
    padded_data = pad(byte_data, 16) # 16 bajtów to blok AES
    # Kodujemy na hex
    hex_data = binascii.hexlify(padded_data).decode('utf-8')
    # Formatowanie: każda linia 16 bajtów
    formatted_hex = [hex_data[i:i + 32] for i in range(0,
    len(hex_data), 32)]
    # Wyświetlamy wynik
    for line in formatted_hex:
        print(line)


from Crypto.Hash import SHA256, SHA3_256, MD5, RIPEMD160
import json

def compute_hashes(plaintext: str):
    # Przekształcamy tekst na bajty
    byte_data = plaintext.encode('utf-8')
    # Obliczamy skrót SHA-256
    sha256_hash = SHA256.new(byte_data).hexdigest()
    # Obliczamy skrót SHA3-256
    sha3_256_hash = SHA3_256.new(byte_data).hexdigest()
    # Obliczamy skrót MD5
    md5_hash = MD5.new(byte_data).hexdigest()
    #Zapisujemy skróty do jednego json
    package = {
    "message": plaintext,
    "hash1": sha256_hash,
    "hash2": md5_hash,
    "hash3": sha3_256_hash
    }
    #Konwersja json do tablicy bajtów
    package_json = json.dumps(package).encode("utf-8")
    RIPEMD160_hash = RIPEMD160.new(package_json).hexdigest()
    # Wyświetlamy wyniki
    print("\nSkróty:")
    print(f"SHA-256: {sha256_hash}")
    print(f"SHA3-256: {sha3_256_hash}")
    print(f"MD5: {md5_hash}")
    print(f"RIPEMD-160: {RIPEMD160_hash}")


def zad1():
    encode_in_hex_with_padding("Kryptologia 2025 - Patryk Rakowski")
    compute_hashes("Kryptologia 2025 - Patryk Rakowski")

    byte_data = "Patryk Rakowski".encode('utf-8')
    import time
    start = time.perf_counter()
    for _ in range(1000000):
        SHA256.new(byte_data).hexdigest()
    end = time.perf_counter()
    print(f"Czas: {end - start:.6f} s")


from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
from Crypto.Hash import SHA3_512
import getpass

# 1. Generowanie klucza i IV z hasła przy użyciu SHA3
def derive_key_and_iv_from_password(password: str) -> tuple[bytes, bytes]:
    # Obliczamy skrót SHA3-512 z hasła (64 bajty)
    hash_object = SHA3_512.new(password.encode('utf-8'))
    hash_bytes = hash_object.digest()
    
    # Klucz AES-256: pierwsze 32 bajty
    key = hash_bytes[:32]
    # IV: kolejne 16 bajtów
    iv = hash_bytes[32:48]
    
    return key, iv

# 3. Funkcja szyfrująca z hasłem
def encrypt_aes_with_password(plaintext: str, password: str) -> str:
    key, iv = derive_key_and_iv_from_password(password)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode('utf-8'), AES.block_size))
    return ciphertext.hex()

# 4. Funkcja deszyfrująca z hasłem
def decrypt_aes_with_password(hex_ciphertext: str, password: str) -> str:
    key, iv = derive_key_and_iv_from_password(password)
    ciphertext = bytes.fromhex(hex_ciphertext)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    return plaintext.decode('utf-8')

def zad2():
    plaintext = "Kryptologia laboratorium 2025 - Patryk Rakowski"
    print(f"Tekst z padem i do hex: {pad(plaintext.encode('utf-8'), 32).hex()}")
    
    # Pobieramy hasło od użytkownika
    password = getpass.getpass("Podaj hasło: ")
    
    # Szyfrowanie z hasłem
    ciphertext_password = encrypt_aes_with_password(plaintext, password)
    print(f"Zaszyfrowane: {ciphertext_password}")
    
    # Deszyfrowanie z hasłem
    password_decrypt = getpass.getpass("Podaj hasło do odszyfrowania: ")
    try:
        decrypted_password = decrypt_aes_with_password(ciphertext_password, password_decrypt)
        print(f"Odszyfrowane: {decrypted_password}")
    except Exception as e:
        print(f"Błąd deszyfrowania: {e}")
        print("Prawdopodobnie podano błędne hasło!")

if __name__ == "__main__":
    # zad1()
    zad2()
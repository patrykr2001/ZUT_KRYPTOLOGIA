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

if __name__ == "__main__":
    zad1()
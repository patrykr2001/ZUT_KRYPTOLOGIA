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

from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Random import get_random_bytes

#Demo szyforwania asymetrycznego
def zad3_szyfr_asym():

    # Generowanie klucza RSA
    key = RSA.generate(2048)

    # Eksport klucza publicznego i prywatnego
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    print("Klucz publiczny:")
    print(public_key.decode())
    print("\nKlucz prywatny:")
    print(private_key.decode())

    # Tworzenie obiektu szyfrującego z klucza publicznego
    public_key_obj = RSA.import_key(public_key)
    cipher_rsa_encrypt = PKCS1_OAEP.new(public_key_obj)

    # Wiadomość do zaszyfrowania
    message = "Patryk Rakowski 2025".encode("utf-8")

    # Szyfrowanie
    encrypted_message = cipher_rsa_encrypt.encrypt(message)
    print("\nZaszyfrowana wiadomość (hex):")
    print(encrypted_message.hex())

    # Tworzenie obiektu deszyfrującego z klucza prywatnego
    private_key_obj = RSA.import_key(private_key)
    cipher_rsa_decrypt = PKCS1_OAEP.new(private_key_obj)

    # Deszyfrowanie
    decrypted_message = cipher_rsa_decrypt.decrypt(encrypted_message)
    print("\nOdszyfrowana wiadomość:")
    print(decrypted_message.decode())

from Crypto.PublicKey import RSA
from Crypto.Signature import pss
from Crypto.Hash import SHA256

def zad3_podpis():
    # 1. Generowanie klucza RSA
    key = RSA.generate(2048)

    # 2. Eksport kluczy (opcjonalnie - można zapisać do pliku)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    print("Klucz publiczny:")
    print(public_key.decode())

    # 3. Wiadomość do podpisania
    message = "Patryk Rakowski 2025".encode("utf-8")

    # 4. Tworzenie skrótu wiadomości
    h = SHA256.new(message)

    # 5. Podpisywanie wiadomości kluczem prywatnym przy użyciu RSA PSS
    signer = pss.new(key)
    signature = signer.sign(h)
    print("\nPodpis (hex):")
    print(signature.hex())
    # 6. Weryfikacja podpisu kluczem publicznym
    public_key_obj = RSA.import_key(public_key)
    verifier = pss.new(public_key_obj)
    h = SHA256.new(message)
    try:
        verifier.verify(h, signature)
        print("\nPodpis jest poprawny!")
    except (ValueError, TypeError):
        print("\nPodpis nie jest poprawny!")


def zad3():
    # i. Generowanie par kluczy asymetrycznych
    bob_keys = RSA.generate(2048)
    alice_keys = RSA.generate(2048)
    
    # ii. Alicja podpisuje wiadomość własnym kluczem prywatnym
    alice_message = "Alice do Boba 2025".encode("utf-8")
    alice_signer = pss.new(alice_keys)
    alice_message_sign = alice_signer.sign(SHA256.new(alice_message))

    # iii. Alicja szyfruje (wiadomość, podpis) losowym kluczem symetrycznym
    # Łączymy wiadomość i podpis w jedną paczkę
    random_symetric_key = get_random_bytes(32)
    random_iv = get_random_bytes(16)  # Generujemy IV
    
    # Łączymy wiadomość i podpis
    combined_data = alice_message + b"|SEPARATOR|" + alice_message_sign
    
    alice_aes_encrypter = AES.new(random_symetric_key, AES.MODE_CBC, iv=random_iv)
    combined_encrypted = alice_aes_encrypter.encrypt(pad(combined_data, AES.block_size))

    # iv. Alicja szyfruje klucz symetryczny kluczem publicznym Boba
    alice_bobs_rsa_encrypter = PKCS1_OAEP.new(RSA.import_key(bob_keys.publickey().export_key()))
    encrypted_symetric_key_for_bob = alice_bobs_rsa_encrypter.encrypt(random_symetric_key)
    
    # Alicja musi też przekazać IV (może być niezaszyfrowany)
    # W praktyce IV jest zwykle przesyłany razem z ciphertextem

    # v. Bob deszyfruje swoim kluczem prywatnym zaszyfrowany klucz symetryczny
    bobs_rsa_decrypter = PKCS1_OAEP.new(bob_keys)
    bobs_decrypted_symetric_key = bobs_rsa_decrypter.decrypt(encrypted_symetric_key_for_bob)

    # vi. Bob deszyfruje kluczem symetrycznym wiadomość/podpis
    bobs_aes_decrypter = AES.new(bobs_decrypted_symetric_key, AES.MODE_CBC, iv=random_iv)
    combined_decrypted = bobs_aes_decrypter.decrypt(combined_encrypted)
    combined_decrypted = unpad(combined_decrypted, AES.block_size)
    
    # Rozdzielamy wiadomość i podpis
    parts = combined_decrypted.split(b"|SEPARATOR|")
    alice_message_decrypted = parts[0]
    alice_sign_decrypted = parts[1]
    
    # vii. Bob sprawdza podpis
    bobs_alices_rsa_verifier = pss.new(RSA.import_key(alice_keys.publickey().export_key()))
    try:
        bobs_alices_rsa_verifier.verify(SHA256.new(alice_message_decrypted), alice_sign_decrypted)
        print("Podpis jest poprawny")
        print("Wiadomość od Alice do Boba:")
        print(alice_message_decrypted.decode())
    except (ValueError, TypeError):
        print("Podpis nie jest poprawny")

if __name__ == "__main__":
    # zad1()
    # zad2()
    # zad3_szyfr_asym()
    # zad3_podpis()
    zad3()
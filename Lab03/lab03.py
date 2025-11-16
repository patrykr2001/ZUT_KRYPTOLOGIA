import random
from math import gcd


def is_prime(n, k=5):
    """Miller-Rabin test pierwotności"""
    if n < 2:
        return False
    if n == 2 or n == 3:
        return True
    if n % 2 == 0:
        return False
    
    # Zapisz n-1 jako 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2
    
    # Test k razy
    for _ in range(k):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        
        if x == 1 or x == n - 1:
            continue
        
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    
    return True


def generate_prime(bits):
    """Generuj liczbę pierwszą o określonej liczbie bitów"""
    while True:
        p = random.getrandbits(bits)
        # Ustaw najstarszy i najmłodszy bit
        p |= (1 << bits - 1) | 1
        if is_prime(p):
            return p


def mod_inverse(a, m):
    """Algorytm rozszerzonego Euklidesa do znajdowania odwrotności modularnej"""
    if a < 0:
        a = a + m
    
    def extended_gcd(a, b):
        if a == 0:
            return b, 0, 1
        gcd_val, x1, y1 = extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd_val, x, y
    
    gcd_val, x, _ = extended_gcd(a % m, m)
    if gcd_val != 1:
        raise Exception("Odwrotność modularna nie istnieje")
    
    return (x % m + m) % m


def generate_rsa_keys(bits):
    """Generuj parę kluczy RSA"""
    # Generuj dwie różne liczby pierwsze p i q
    p = generate_prime(bits // 2)
    q = generate_prime(bits // 2)
    
    while p == q:
        q = generate_prime(bits // 2)
    
    # Oblicz n = p * q
    n = p * q
    
    # Oblicz funkcję Eulera phi(n) = (p-1)(q-1)
    phi = (p - 1) * (q - 1)
    
    # Wybierz e takie, że 1 < e < phi(n) i gcd(e, phi(n)) = 1
    e = 65537  # Powszechnie używana wartość
    while gcd(e, phi) != 1:
        e = random.randrange(3, phi, 2)
    
    # Oblicz d = e^(-1) mod phi(n)
    d = mod_inverse(e, phi)
    
    # Klucz publiczny: (e, n)
    # Klucz prywatny: (d, n)
    return (e, n), (d, n), p, q, phi


def sign_message(message, private_key):
    """Podpisz wiadomość używając klucza prywatnego"""
    d, n = private_key
    
    # Konwertuj wiadomość na liczbę
    if isinstance(message, str):
        message_bytes = message.encode('utf-8')
    else:
        message_bytes = message
    
    m = int.from_bytes(message_bytes, byteorder='big')
    
    # Sprawdź czy wiadomość jest mniejsza od n
    if m >= n:
        raise ValueError("Wiadomość jest za duża dla tego klucza")
    
    # Podpis: s = m^d mod n
    signature = pow(m, d, n)
    
    return signature, message_bytes


def verify_signature(message_bytes, signature, public_key):
    """Weryfikuj podpis używając klucza publicznego"""
    e, n = public_key
    
    # Konwertuj wiadomość na liczbę
    m = int.from_bytes(message_bytes, byteorder='big')
    
    # Weryfikacja: m' = s^e mod n
    m_prime = pow(signature, e, n)
    
    # Sprawdź czy m == m'
    return m == m_prime


def main():
    # Parametry
    bits = 2048
    
    print(f"Bezpieczeństwo {bits} bitów")
    print()
    
    # Generuj klucze
    public_key, private_key, p, q, phi = generate_rsa_keys(bits)
    e, n = public_key
    d, _ = private_key
    
    # Wyświetl klucz publiczny
    print("Klucz publiczny:")
    print(f"  e = {e}")
    print(f"  n = {n}")
    print()
    
    # Test e*d == 1 (mod phi)
    test_result = (e * d) % phi
    if test_result == 1:
        print("Test e*d ≡ 1 (mod phi(n)): OK")
    else:
        print(f"Test e*d ≡ 1 (mod phi(n)): NIE OK (wynik: {test_result})")
    print()
    
    # Wyświetl klucz prywatny
    print("Klucz prywatny:")
    print(f"  d = {d}")
    print(f"  n = {n}")
    print()
    
    # Wiadomość do podpisu
    message = "To jest testowa wiadomosc do podpisu"
    print("Wiadomość:")
    print(f"  {message}")
    print()
    
    # Podpisz wiadomość
    signature, message_bytes = sign_message(message, private_key)
    
    print("Wiadomość w bajtach:")
    print(f"  {message_bytes.hex()}")
    print()
    
    print("Podpis:")
    print(f"  {signature}")
    print()
    
    # Weryfikuj podpis
    is_valid = verify_signature(message_bytes, signature, public_key)
    
    print("Weryfikacja podpisu:")
    if is_valid:
        print("  Podpis jest POPRAWNY")
    else:
        print("  Podpis jest NIEPOPRAWNY")
    print()
    
    # Dodatkowy test z niepoprawną wiadomością
    print("Test z niepoprawną wiadomością:")
    fake_message = "Inna wiadomosc"
    _, fake_message_bytes = fake_message.encode('utf-8'), fake_message.encode('utf-8')
    is_valid_fake = verify_signature(fake_message_bytes, signature, public_key)
    if not is_valid_fake:
        print("  Weryfikacja poprawnie odrzuca niepoprawną wiadomość")
    else:
        print("  BŁĄD: Weryfikacja akceptuje niepoprawną wiadomość")


if __name__ == "__main__":
    main()

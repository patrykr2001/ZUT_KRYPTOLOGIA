import random
from math import gcd, lcm
import time


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
    
    # Oblicz lambda(n) = lcm(p-1, q-1) - Carmichael's totient function
    # Bezpieczniejsza alternatywa dla phi(n) = (p-1)(q-1)
    lambda_n = lcm(p - 1, q - 1)
    
    # Wybierz e takie, że 1 < e < lambda(n) i gcd(e, lambda(n)) = 1
    e = 65537  # Powszechnie używana wartość
    while gcd(e, lambda_n) != 1:
        e = random.randrange(3, lambda_n, 2)
    
    # Oblicz d = e^(-1) mod lambda(n)
    d = mod_inverse(e, lambda_n)
    
    # Klucz publiczny: (e, n)
    # Klucz prywatny: (d, n)
    return (e, n), (d, n), p, q, lambda_n


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
    public_key, private_key, p, q, lambda_n = generate_rsa_keys(bits)
    e, n = public_key
    d, _ = private_key
    
    # Wyświetl klucz publiczny
    print("Klucz publiczny:")
    print(f"  e = {e}")
    print(f"  n = {n}")
    print()
    
    # Test e*d == 1 (mod lambda(n))
    test_result = (e * d) % lambda_n
    if test_result == 1:
        print("Test e*d ≡ 1 (mod lambda(n)): OK")
    else:
        print(f"Test e*d ≡ 1 (mod lambda(n)): NIE OK (wynik: {test_result})")
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
    fake_message_bytes = fake_message.encode('utf-8')
    is_valid_fake = verify_signature(fake_message_bytes, signature, public_key)
    if not is_valid_fake:
        print("  Weryfikacja poprawnie odrzuca niepoprawną wiadomość")
    else:
        print("  BŁĄD: Weryfikacja akceptuje niepoprawną wiadomość")
    
    
    # ZADANIE 2
    print("\n" + "="*80)
    print("ZADANIE 2 - Analiza algorytmu Plain RSA")
    print("="*80)
    
    # a) Maksymalna długość wiadomości
    print("\na) Maksymalna długość wiadomości:")
    print("-" * 60)
    
    for key_bits in [2048, 3072, 4096, 7680]:
        # Liczba bitów w module n
        n_bits = key_bits
        # Liczba bajtów: (bity - 1) / 8, zaokrąglone w dół
        # Używamy bits-1 bo wiadomość musi być m < n
        max_bytes = (n_bits - 1) // 8
        max_bits = n_bits - 1
        
        print(f"Klucz {key_bits} bitów:")
        print(f"  Maksymalnie {max_bytes} bajtów ({max_bits} bitów)")
        print(f"  To około {max_bytes} znaków ASCII")
        print()
    
    
    # b) Pomiar czasu dla różnych rozmiarów kluczy
    print("\nb) Pomiar czasu operacji dla różnych rozmiarów kluczy:")
    print("-" * 60)
    
    test_message = "Testowa wiadomosc do pomiaru czasu"
    
    # for key_bits in [2048, 3072, 4096, 7680]:
    for key_bits in [2048, 3072]:
        print(f"\nKlucz {key_bits} bitów:")
        
        # Generowanie kluczy
        start_gen = time.time()
        pub_key, priv_key, _, _, _ = generate_rsa_keys(key_bits)
        time_gen = time.time() - start_gen
        
        # Podpisywanie
        start_sign = time.time()
        sig, msg_bytes = sign_message(test_message, priv_key)
        time_sign = time.time() - start_sign
        
        # Weryfikacja
        start_verify = time.time()
        verify_signature(msg_bytes, sig, pub_key)
        time_verify = time.time() - start_verify
        
        print(f"  Generowanie kluczy: {time_gen:.4f} s")
        print(f"  Podpisywanie:        {time_sign:.6f} s ({time_sign*1000:.3f} ms)")
        print(f"  Weryfikacja:         {time_verify:.6f} s ({time_verify*1000:.3f} ms)")
        print(f"  Stosunek sign/verify: {time_sign/time_verify:.2f}x")
    
    
    # c) Przykładowa liczba 4096-bitowa
    print("\n\nc) Przykładowa liczba składająca się z 4096 bitów:")
    print("-" * 60)
    
    # Wygeneruj liczbę pierwszą 4096-bitową
    # example_4096 = generate_prime(4096)
    
    # print(f"Liczba (hex):")
    # print(f"{hex(example_4096)}\n")
    
    # print(f"Liczba (dziesiętnie):")
    # print(f"{example_4096}\n")
    
    # # Ile to cyfr dziesiętnych?
    # num_decimal_digits = len(str(example_4096))
    # print(f"Liczba cyfr dziesiętnych: {num_decimal_digits}")
    
    # # Porównanie z wielkościami
    # print(f"\nDla porównania:")
    # print(f"  - Liczba atomów we wszechświecie: ~10^80 (80 cyfr)")
    # print(f"  - Liczba 4096-bitowa:             ~10^{num_decimal_digits} ({num_decimal_digits} cyfr)")
    # print(f"  - To liczba {num_decimal_digits//80}x większa od liczby atomów we wszechświecie")
    
    # Ile bitów ma różne wielkości
    print(f"\nPorównanie rozmiarów:")
    print(f"  - 2^32 (4 bajty):     {2**32:,}")
    print(f"  - 2^64 (8 bajtów):    {2**64:,}")
    print(f"  - 2^128:              {2**128:,}")
    print(f"  - 2^256:              {2**256}")
    print(f"  - 2^4096:             ~10^{int(4096 * 0.301)} (ma {len(str(2**4096))} cyfr dziesiętnych)")
    
    
    # ZADANIE 3
    print("\n" + "="*80)
    print("ZADANIE 3 - Ataki na Plain RSA")
    print("="*80)
    
    # Użyjemy wcześniej wygenerowanych kluczy
    print("\nUżywamy klucza publicznego z początku programu:")
    print(f"  e = {e}")
    print(f"  n = {n}")
    
    # a) Eksperyment 1 - No-message attack
    print("\n" + "-"*80)
    print("a) Eksperyment 1 - No-message attack")
    print("-"*80)
    print("\nAtak polega na wygenerowaniu losowego podpisu s,")
    print("a następnie obliczeniu wiadomości m = s^e mod n.")
    print("Otrzymujemy parę (s, m) bez znajomości klucza prywatnego\n")
    
    # Wygeneruj losowy podpis s (liczba mniejsza od n)
    s_fake = random.randrange(2, n)
    
    print(f"1. Wygenerowany losowy 'podpis' s:")
    print(f"   s = {s_fake}")
    print()
    
    # Oblicz odpowiadającą wiadomość m = s^e mod n
    m_fake = pow(s_fake, e, n)
    
    print(f"2. Obliczona wiadomość m = s^e mod n:")
    print(f"   m = {m_fake}")
    print()
    
    # Weryfikacja - czy taki podpis jest poprawny dla tej wiadomości?
    # Konwertujemy m na bajty
    m_fake_bytes = m_fake.to_bytes((m_fake.bit_length() + 7) // 8, byteorder='big')
    
    print(f"3. Weryfikacja czy para (s, m) jest poprawna:")
    is_valid_fake_attack = verify_signature(m_fake_bytes, s_fake, public_key)
    
    if is_valid_fake_attack:
        print(f"    TAK Para (s, m) przechodzi weryfikację")
        print(f"   Wygenerowaliśmy 'podpis' bez użycia klucza prywatnego.")
    else:
        print(f"    NIE - coś poszło nie tak")
    
    print(f"\n4. Wiadomość jako tekst (jeśli da się zinterpretować):")
    try:
        decoded = m_fake_bytes.decode('utf-8', errors='ignore')
        print(f"   {repr(decoded)}")
        print(f"   (losowa nieczytelna wiadomość, ale matematycznie poprawna para)")
    except:
        print(f"   (nie da się zinterpretować jako UTF-8, to tylko losowe bajty)")
    
    print(f"\n5. Wniosek:")
    print(f"   Plain RSA jest podatny na no-message attack.")
    print(f"   Atakujący może wygenerować 'poprawne' pary (podpis, wiadomość)")
    print(f"   bez znajomości klucza prywatnego, choć nie kontroluje treści wiadomości.")
    
    
    # b) Eksperyment 2 - Multiplicative property attack
    print("\n" + "-"*80)
    print("b) Eksperyment 2 - Multiplicative property attack")
    print("-"*80)
    print("\nAtak wykorzystuje własność multiplikatywną RSA:")
    print("Jeśli m = m1 * m2 mod n, to s = s1 * s2 mod n")
    print("Atakujący może sfałszować podpis dla m, mając podpisy dla m1 i m2\n")
    
    # Wybierz dwie małe liczby jako m1 i m2
    # Muszą być wystarczająco małe, aby m1 * m2 < n
    m1 = 12345
    m2 = 67890
    
    print(f"1. Wybieramy dwie wiadomości:")
    print(f"   m1 = {m1}")
    print(f"   m2 = {m2}")
    print()
    
    # Oblicz m = m1 * m2 mod n
    m_target = (m1 * m2) % n
    print(f"2. Wiadomość docelowa m = m1 * m2 mod n:")
    print(f"   m = {m_target}")
    print()
    
    # Uzyskaj podpisy dla m1 i m2 (normalnie)
    # Konwertuj na bajty
    m1_bytes = m1.to_bytes((m1.bit_length() + 7) // 8, byteorder='big')
    m2_bytes = m2.to_bytes((m2.bit_length() + 7) // 8, byteorder='big')
    
    s1, _ = sign_message(m1_bytes, private_key)
    s2, _ = sign_message(m2_bytes, private_key)
    
    print(f"3. Uzyskujemy legalne podpisy dla m1 i m2:")
    print(f"   s1 = {s1}")
    print(f"   s2 = {s2}")
    print()
    
    # Atakujący oblicza podpis dla m jako s = s1 * s2 mod n
    s_forged = (s1 * s2) % n
    
    print(f"4. Atakujący oblicza sfałszowany podpis s = s1 * s2 mod n:")
    print(f"   s = {s_forged}")
    print()
    
    # Weryfikacja - czy sfałszowany podpis jest poprawny?
    m_target_bytes = m_target.to_bytes((m_target.bit_length() + 7) // 8, byteorder='big')
    is_valid_forged = verify_signature(m_target_bytes, s_forged, public_key)
    
    print(f"5. Weryfikacja sfałszowanego podpisu:")
    if is_valid_forged:
        print(f"    TAK Sfałszowany podpis przechodzi weryfikację")
        print(f"   Atakujący sfałszował podpis dla m bez użycia klucza prywatnego.")
    else:
        print(f"    NIE - coś poszło nie tak")
    
    # Dodatkowa weryfikacja matematyczna
    print(f"\n6. Weryfikacja matematyczna:")
    print(f"   s^e mod n = {pow(s_forged, e, n)}")
    print(f"   m        = {m_target}")
    print(f"   Równe? {pow(s_forged, e, n) == m_target}")
    
    # Sprawdź też własność multiplikatywną bezpośrednio
    print(f"\n7. Sprawdzenie własności multiplikatywnej:")
    print(f"   s1^e mod n = {pow(s1, e, n)} (powinno być {m1})")
    print(f"   s2^e mod n = {pow(s2, e, n)} (powinno być {m2})")
    print(f"   (s1*s2)^e mod n = {pow((s1 * s2) % n, e, n)} (powinno być {m_target})")
    print(f"   (s1^e * s2^e) mod n = {(pow(s1, e, n) * pow(s2, e, n)) % n} (powinno być {m_target})")
    
    print(f"\n8. Wniosek:")
    print(f"   Plain RSA ma własność multiplikatywną:")
    print(f"   sign(m1*m2) = sign(m1) * sign(m2) mod n")
    print(f"   To pozwala atakującemu sfałszować podpis dla m = m1*m2,")
    print(f"   jeśli zna podpisy dla m1 i m2.")
    print(f"   Dlatego w praktyce używa się padding (np. PSS), który")
    print(f"   niszczy tę własność multiplikatywną")



if __name__ == "__main__":
    main()

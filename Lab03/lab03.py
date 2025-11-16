import random
from math import gcd, lcm
import time
import hashlib


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


def hash_message(message, n):
    """
    Funkcja skrótu dla RSA-FDH (Full Domain Hash).
    Haszuje wiadomość do wartości w zakresie [0, n-1].
    
    Używamy SHA-256 i rozszerzamy wynik do odpowiedniej długości.
    """
    # Oblicz ile bajtów potrzebujemy dla n
    n_bytes = (n.bit_length() + 7) // 8
    
    # Użyj SHA-256 jako bazy
    hash_obj = hashlib.sha256()
    
    if isinstance(message, str):
        hash_obj.update(message.encode('utf-8'))
    else:
        hash_obj.update(message)
    
    # Dla małych modułów (testowych) po prostu obetnij hash
    # W prawdziwym RSA-FDH używa się bardziej skomplikowanych metod (np. MGF1)
    hash_digest = hash_obj.digest()
    
    # Rozszerz hash jeśli potrzeba (w uproszczeniu - iteracyjne hashowanie)
    extended_hash = hash_digest
    counter = 0
    while len(extended_hash) < n_bytes:
        hash_obj = hashlib.sha256()
        hash_obj.update(hash_digest + counter.to_bytes(4, 'big'))
        extended_hash += hash_obj.digest()
        counter += 1
    
    # Przetnij do odpowiedniej długości
    extended_hash = extended_hash[:n_bytes]
    
    # Konwertuj na liczbę
    h = int.from_bytes(extended_hash, byteorder='big')
    
    # Upewnij się że h < n
    h = h % n
    
    return h


def sign_message_fdh(message, private_key):
    """
    Podpisz wiadomość używając RSA-FDH (Full Domain Hash).
    Najpierw hashujemy wiadomość, potem podpisujemy hash.
    """
    d, n = private_key
    
    # Konwertuj wiadomość na bajty jeśli to string
    if isinstance(message, str):
        message_bytes = message.encode('utf-8')
    else:
        message_bytes = message
    
    # Zahashuj wiadomość do wartości w zakresie [0, n-1]
    h = hash_message(message_bytes, n)
    
    # Podpis: s = h^d mod n
    signature = pow(h, d, n)
    
    return signature, message_bytes


def verify_signature_fdh(message_bytes, signature, public_key):
    """
    Weryfikuj podpis RSA-FDH używając klucza publicznego.
    """
    e, n = public_key
    
    # Zahashuj wiadomość
    h = hash_message(message_bytes, n)
    
    # Weryfikacja: h' = s^e mod n
    h_prime = pow(signature, e, n)
    
    # Sprawdź czy h == h'
    return h == h_prime


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
    # print("\n\nc) Przykładowa liczba składająca się z 4096 bitów:")
    # print("-" * 60)
    
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
    
    # print(f"\n5. Wniosek:")
    # print(f"   Plain RSA jest podatny na no-message attack.")
    # print(f"   Atakujący może wygenerować 'poprawne' pary (podpis, wiadomość)")
    # print(f"   bez znajomości klucza prywatnego, choć nie kontroluje treści wiadomości.")
    
    
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
    # print(f"\n6. Weryfikacja matematyczna:")
    # print(f"   s^e mod n = {pow(s_forged, e, n)}")
    # print(f"   m        = {m_target}")
    # print(f"   Równe? {pow(s_forged, e, n) == m_target}")
    
    # # Sprawdź też własność multiplikatywną bezpośrednio
    # print(f"\n7. Sprawdzenie własności multiplikatywnej:")
    # print(f"   s1^e mod n = {pow(s1, e, n)} (powinno być {m1})")
    # print(f"   s2^e mod n = {pow(s2, e, n)} (powinno być {m2})")
    # print(f"   (s1*s2)^e mod n = {pow((s1 * s2) % n, e, n)} (powinno być {m_target})")
    # print(f"   (s1^e * s2^e) mod n = {(pow(s1, e, n) * pow(s2, e, n)) % n} (powinno być {m_target})")
    
    # print(f"\n8. Wniosek:")
    # print(f"   Plain RSA ma własność multiplikatywną:")
    # print(f"   sign(m1*m2) = sign(m1) * sign(m2) mod n")
    # print(f"   To pozwala atakującemu sfałszować podpis dla m = m1*m2,")
    # print(f"   jeśli zna podpisy dla m1 i m2.")
    # print(f"   Dlatego w praktyce używa się padding (np. PSS), który")
    # print(f"   niszczy tę własność multiplikatywną")
    
    
    # c) Eksperyment 3 - Atak na szyfrowanie RSA z małym wykładnikiem
    print("\n" + "-"*80)
    print("c) Eksperyment 3 - Atak na szyfrowanie RSA z małym wykładnikiem e=3")
    print("-"*80)
    print("\nGdy wykładnik publiczny e jest mały (np. e=3) i wiadomość m jest")
    print("wystarczająco mała, że m^e < N, wtedy m^e mod N = m^e (bez modulo).")
    print("Atakujący może po prostu obliczyć pierwiastek e-tego stopnia z szyfrogramu!\n")
    
    # Dane z zadania
    ciphertext = 2829246759667430901779973875
    e_attack = 3
    N_attack = int(
        "7486374846663627918089811394557316880016731434900733973466"
        "4557033677222985045895878321130196223760783214379338040678"
        "2339080107477732640032376205901411740283301540121395970682"
        "3612154294544242607436701783834990586691512046997836198600"
        "2240362282392181726265023378796284600697013635003150020012"
        "763665368297013349"
    )
    
    print(f"Dane:")
    print(f"  Szyfrogram c = {ciphertext}")
    print(f"  Wykładnik e = {e_attack}")
    print(f"  Moduł N = {N_attack}")
    print()
    
    # Sprawdź czy c^(1/3) < N (czyli czy m^3 < N, co oznacza że nie było redukcji modulo)
    print(f"1. Sprawdzenie czy m^3 < N (nie było redukcji modulo):")
    
    # Oblicz przybliżony pierwiastek sześcienny
    def nth_root(x, n):
        """Oblicz pierwiastek n-tego stopnia z x (całkowity)"""
        # Używamy metody bisekcji dla dużych liczb
        if x == 0:
            return 0
        if x == 1:
            return 1
        
        # Początkowe oszacowanie
        low = 0
        high = x
        
        # Optymalizacja dla dużych liczb
        if x > 2**64:
            # Lepsze początkowe oszacowanie
            high = 2 ** ((x.bit_length() + n - 1) // n + 1)
        
        while low < high:
            mid = (low + high) // 2
            mid_pow = mid ** n
            
            if mid_pow == x:
                return mid
            elif mid_pow < x:
                low = mid + 1
            else:
                high = mid
        
        # Sprawdź czy low jest dokładnym pierwiastkiem
        if low ** n == x:
            return low
        else:
            return low - 1  # Zwróć największą liczbę całkowitą <= x^(1/n)
    
    # Oblicz m = c^(1/3)
    print(f"   Obliczanie m = c^(1/3)...")
    m_decrypted = nth_root(ciphertext, e_attack)
    
    print(f"   m = {m_decrypted}")
    print()
    
    # Weryfikacja - czy m^3 = c?
    print(f"2. Weryfikacja: m^3 = c?")
    m_cubed = m_decrypted ** 3
    print(f"   m^3 = {m_cubed}")
    print(f"   c   = {ciphertext}")
    
    if m_cubed == ciphertext:
        print(f"    TAK m^3 = c, deszyfrowanie poprawne")
    else:
        print(f"    Nie zgadza się, spróbujmy m+1...")
        m_decrypted += 1
        m_cubed = m_decrypted ** 3
        if m_cubed == ciphertext:
            print(f"    TAK (m+1)^3 = c")
        else:
            print(f"    Nadal się nie zgadza")
    print()
    
    # Zamień liczbę dziesiętną na szesnastkową
    print(f"3. Konwersja m na format szesnastkowy:")
    m_hex = hex(m_decrypted)[2:]  # Usuń prefix '0x'
    print(f"   m (hex) = {m_hex}")
    print()
    
    # Konwersja na bajty i odczyt ASCII
    print(f"4. Dekodowanie jako ASCII:")
    
    # Upewnij się, że hex ma parzystą liczbę znaków
    if len(m_hex) % 2 == 1:
        m_hex = '0' + m_hex
    
    # Konwertuj hex na bajty
    m_bytes_decrypted = bytes.fromhex(m_hex)
    
    print(f"   Bajty (hex): {m_bytes_decrypted.hex()}")
    
    # Dekoduj jako ASCII/UTF-8
    try:
        m_text = m_bytes_decrypted.decode('ascii')
        print(f"   Wiadomość:   '{m_text}'")
    except:
        try:
            m_text = m_bytes_decrypted.decode('utf-8')
            print(f"   Wiadomość (UTF-8): '{m_text}'")
        except:
            print(f"   Nie można zdekodować jako tekst")
            print(f"   Surowe bajty: {m_bytes_decrypted}")
    
    # print()
    # print(f"5. Wniosek:")
    # print(f"   Gdy e jest małe (e=3) i wiadomość m jest wystarczająco mała,")
    # print(f"   że m^e < N, atakujący może łatwo odszyfrować wiadomość")
    # print(f"   obliczając po prostu e-ty pierwiastek z szyfrogramu.")
    # print(f"   Dlatego w praktyce:")
    # print(f"   - Używa się większego e (np. e=65537)")
    # print(f"   - Zawsze stosuje się padding (OAEP), który zwiększa rozmiar")
    # print(f"     wiadomości, zapewniając że m^e > N")
    
    
    # ZADANIE 4
    print("\n" + "="*80)
    print("ZADANIE 4 - RSA-FDH (Full Domain Hash)")
    print("="*80)
    
    print("\nRSA-FDH to ulepszony schemat Plain RSA, który:")
    print("- Podpisuje HASH wiadomości, a nie samą wiadomość")
    print("- Używa funkcji skrótu (np. SHA-256) przed operacją RSA")
    print("- Eliminuje wiele ataków na Plain RSA\n")
    
    # Wiadomość testowa
    test_msg = "To jest testowa wiadomosc dla RSA-FDH"
    print(f"Wiadomość testowa:")
    print(f"  '{test_msg}'")
    print()
    
    # Generuj nową parę kluczy dla testów
    print("Generowanie kluczy RSA 2048-bitowych...")
    pub_fdh, priv_fdh, _, _, _ = generate_rsa_keys(2048)
    e_fdh, n_fdh = pub_fdh
    d_fdh, _ = priv_fdh
    print(f"  e = {e_fdh}")
    print(f"  n = {n_fdh}")
    print()
    
    # Test Plain RSA vs RSA-FDH
    print("-" * 80)
    print("Porównanie Plain RSA vs RSA-FDH")
    print("-" * 80)
    
    # Plain RSA
    print("\n1. Plain RSA:")
    sig_plain, msg_bytes = sign_message(test_msg, priv_fdh)
    is_valid_plain = verify_signature(msg_bytes, sig_plain, pub_fdh)
    print(f"   Podpis (Plain):  {sig_plain}")
    print(f"   Weryfikacja:     {'POPRAWNA' if is_valid_plain else 'NIEPOPRAWNA'}")
    
    # RSA-FDH
    print("\n2. RSA-FDH:")
    sig_fdh, msg_bytes_fdh = sign_message_fdh(test_msg, priv_fdh)
    is_valid_fdh = verify_signature_fdh(msg_bytes_fdh, sig_fdh, pub_fdh)
    
    # Pokaż hash
    h = hash_message(msg_bytes_fdh, n_fdh)
    print(f"   Hash wiadomości: {h}")
    print(f"   Podpis (FDH):    {sig_fdh}")
    print(f"   Weryfikacja:     {'POPRAWNA' if is_valid_fdh else 'NIEPOPRAWNA'}")
    
    
    # a) Analiza czasu wykonania
    print("\n" + "-" * 80)
    print("a) Analiza czasu wykonania - Plain RSA vs RSA-FDH")
    print("-" * 80)
    
    # Przygotuj wiadomości różnej długości
    messages = {
        "Krótka (10B)": "a" * 10,
        "Średnia (100B)": "a" * 100,
        "Długa (200B)": "a" * 200,
    }
    
    num_iterations = 10
    
    for msg_name, msg in messages.items():
        print(f"\n{msg_name}:")
        
        # Plain RSA - pomiar
        times_plain_sign = []
        times_plain_verify = []
        
        for _ in range(num_iterations):
            # Podpisywanie
            start = time.time()
            sig_p, msg_b = sign_message(msg, priv_fdh)
            times_plain_sign.append(time.time() - start)
            
            # Weryfikacja
            start = time.time()
            verify_signature(msg_b, sig_p, pub_fdh)
            times_plain_verify.append(time.time() - start)
        
        avg_plain_sign = sum(times_plain_sign) / num_iterations
        avg_plain_verify = sum(times_plain_verify) / num_iterations
        
        # RSA-FDH - pomiar
        times_fdh_sign = []
        times_fdh_verify = []
        
        for _ in range(num_iterations):
            # Podpisywanie
            start = time.time()
            sig_f, msg_b_f = sign_message_fdh(msg, priv_fdh)
            times_fdh_sign.append(time.time() - start)
            
            # Weryfikacja
            start = time.time()
            verify_signature_fdh(msg_b_f, sig_f, pub_fdh)
            times_fdh_verify.append(time.time() - start)
        
        avg_fdh_sign = sum(times_fdh_sign) / num_iterations
        avg_fdh_verify = sum(times_fdh_verify) / num_iterations
        
        print(f"  Plain RSA:")
        print(f"    Podpisywanie: {avg_plain_sign*1000:.4f} ms")
        print(f"    Weryfikacja:  {avg_plain_verify*1000:.4f} ms")
        
        print(f"  RSA-FDH:")
        print(f"    Podpisywanie: {avg_fdh_sign*1000:.4f} ms")
        print(f"    Weryfikacja:  {avg_fdh_verify*1000:.4f} ms")
        
        print(f"  Różnica:")
        print(f"    Podpisywanie: {((avg_fdh_sign - avg_plain_sign) / avg_plain_sign * 100):+.2f}%")
        print(f"    Weryfikacja:  {((avg_fdh_verify - avg_plain_verify) / avg_plain_verify * 100):+.2f}%")
    

if __name__ == "__main__":
    main()


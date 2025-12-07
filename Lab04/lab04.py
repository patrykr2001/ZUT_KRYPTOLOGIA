"""
Lab 04 - Generatory strumieni kluczy (LFSR)
Kryptologia - Patryk Rakowski 2025

Implementacja liniowych rejestrów przesuwających i generatorów strumieni kluczy:
1. LFSR (Linear Feedback Shift Register)
2. Generator Geffe'go
3. Generator Stop-and-Go
4. Shrinking Generator
"""

import time
from LFSR import LFSR
from Utilities import display_binary_blocks, bits_to_hex, parse_taps, parse_seed
from Generators import geffe_generator, stop_and_go_generator, shrinking_generator

def zad1():
    """Zadanie 1: Podstawowa implementacja LFSR"""
    print("=" * 80)
    print("ZADANIE 1 - IMPLEMENTACJA LINIOWEGO REJESTRU PRZESUWAJĄCEGO (LFSR)")
    print("=" * 80)
    
    print("\nPrzykład 1: 4-bitowy LFSR")
    print("Wielomian: x^4 + x^3 + 1 (taps=[4,3])")
    print("Stan początkowy: 1011 (11 dziesiętnie)")
    
    lfsr = LFSR(length=4, taps=[4, 3], seed=0b1011)
    
    print(f"\nKonfiguracja rejestru:")
    print(f"  Długość: {lfsr.length} bitów")
    print(f"  Pozycje tapów: {lfsr.taps}")
    print(f"  Stan początkowy: {lfsr.get_state_binary()} ({lfsr.initial_state})")
    
    print(f"\nPierwsze 10 kroków działania rejestru:")
    lfsr.reset()
    for i in range(10):
        state_before = lfsr.get_state_binary()
        output = lfsr.step()
        state_after = lfsr.get_state_binary()
        print(f"  Krok {i+1:2d}: [{state_before}] -> bit={output} -> [{state_after}]")
    
    # Generowanie dłuższego strumienia
    print(f"\nGenerowanie strumienia 64 bitów:")
    lfsr.reset()
    keystream = lfsr.generate_keystream(64)
    display_binary_blocks(keystream, "Strumień kluczy")
    print(f"Hex: {bits_to_hex(keystream)}")
    
    # Przykład 2: 8-bitowy LFSR
    print("\n" + "-" * 80)
    print("\nPrzykład 2: 8-bitowy LFSR")
    print("Wielomian: x^8 + x^6 + x^5 + x^4 + 1 (taps=[8,6,5,4])")
    print("Stan początkowy: 10110101 (181 dziesiętnie)")
    
    lfsr2 = LFSR(length=8, taps=[8, 6, 5, 4], seed=0b10110101)
    
    print(f"\nKonfiguracja rejestru:")
    print(f"  Długość: {lfsr2.length} bitów")
    print(f"  Pozycje tapów: {lfsr2.taps}")
    print(f"  Stan początkowy: {lfsr2.get_state_binary()} ({lfsr2.initial_state})")
    
    print(f"\nGenerowanie strumienia 128 bitów:")
    start_time = time.time()
    keystream2 = lfsr2.generate_keystream(128)
    elapsed = time.time() - start_time
    
    display_binary_blocks(keystream2, "Strumień kluczy")
    print(f"Hex: {bits_to_hex(keystream2)}")
    print(f"Czas generowania: {elapsed*1000:.4f} ms")


def zad2():
    """Zadanie 2: Generatory strumieni kluczy"""
    print("\n" + "=" * 80)
    print("ZADANIE 2 - GENERATORY STRUMIENI KLUCZY")
    print("=" * 80)
    
    # Generator Geffe'go
    print("\n1. GENERATOR GEFFE'GO")
    print("-" * 80)
    print("Kombinuje 3 LFSR: output = (L1 AND L2) XOR ((NOT L1) AND L3)")
    
    lfsr1 = LFSR(length=5, taps=[5, 2], seed=0b10110)
    lfsr2 = LFSR(length=6, taps=[6, 5], seed=0b110101)
    lfsr3 = LFSR(length=7, taps=[7, 6], seed=0b1011010)
    
    print(f"\nKonfiguracja:")
    print(f"  LFSR1 (selektor): length={lfsr1.length}, taps={lfsr1.taps}, seed={lfsr1.get_state_binary()}")
    print(f"  LFSR2:            length={lfsr2.length}, taps={lfsr2.taps}, seed={lfsr2.get_state_binary()}")
    print(f"  LFSR3:            length={lfsr3.length}, taps={lfsr3.taps}, seed={lfsr3.get_state_binary()}")
    
    start_time = time.time()
    keystream_geffe = geffe_generator(lfsr1, lfsr2, lfsr3, 128)
    elapsed = time.time() - start_time
    
    display_binary_blocks(keystream_geffe, "Strumień kluczy Geffe'go")
    print(f"Hex: {bits_to_hex(keystream_geffe)}")
    print(f"Czas generowania: {elapsed*1000:.4f} ms")
    
    # Generator Stop-and-Go
    print("\n2. GENERATOR STOP-AND-GO")
    print("-" * 80)
    print("Rejestr kontrolny decyduje, który rejestr danych się przesuwa")
    
    lfsr_ctrl = LFSR(length=5, taps=[5, 3], seed=0b11010)
    lfsr_r2 = LFSR(length=6, taps=[6, 5, 3, 2], seed=0b101101)
    lfsr_r3 = LFSR(length=7, taps=[7, 6, 5, 4], seed=0b1101010)
    
    print(f"\nKonfiguracja:")
    print(f"  LFSR Control: length={lfsr_ctrl.length}, taps={lfsr_ctrl.taps}, seed={lfsr_ctrl.get_state_binary()}")
    print(f"  LFSR R2:      length={lfsr_r2.length}, taps={lfsr_r2.taps}, seed={lfsr_r2.get_state_binary()}")
    print(f"  LFSR R3:      length={lfsr_r3.length}, taps={lfsr_r3.taps}, seed={lfsr_r3.get_state_binary()}")
    
    start_time = time.time()
    keystream_sag = stop_and_go_generator(lfsr_ctrl, lfsr_r2, lfsr_r3, 128)
    elapsed = time.time() - start_time
    
    display_binary_blocks(keystream_sag, "Strumień kluczy Stop-and-Go")
    print(f"Hex: {bits_to_hex(keystream_sag)}")
    print(f"Czas generowania: {elapsed*1000:.4f} ms")
    
    # Shrinking Generator
    print("\n3. SHRINKING GENERATOR")
    print("-" * 80)
    print("Rejestr selekcji filtruje wyjście rejestru danych")
    
    lfsr_a = LFSR(length=7, taps=[7, 6], seed=0b1010110)
    lfsr_s = LFSR(length=5, taps=[5, 4, 3, 2], seed=0b11011)
    
    print(f"\nKonfiguracja:")
    print(f"  LFSR A (dane):    length={lfsr_a.length}, taps={lfsr_a.taps}, seed={lfsr_a.get_state_binary()}")
    print(f"  LFSR S (selekcja): length={lfsr_s.length}, taps={lfsr_s.taps}, seed={lfsr_s.get_state_binary()}")
    
    start_time = time.time()
    keystream_shrink = shrinking_generator(lfsr_a, lfsr_s, 128)
    elapsed = time.time() - start_time
    
    display_binary_blocks(keystream_shrink, "Strumień kluczy Shrinking Generator")
    print(f"Hex: {bits_to_hex(keystream_shrink)}")
    print(f"Czas generowania: {elapsed*1000:.4f} ms")


def interactive_lfsr():
    """Interaktywny tryb konfiguracji pojedynczego LFSR."""
    print("\n" + "=" * 80)
    print("TRYB INTERAKTYWNY - KONFIGURACJA LFSR")
    print("=" * 80)
    
    try:
        # Długość rejestru
        length = int(input("\nPodaj długość rejestru (w bitach): "))
        if length <= 0:
            print("Błąd: Długość musi być dodatnia")
            return
        
        # Pytamy o tryb inicjalizacji
        auto_init = input("\nUżyć automatycznej inicjalizacji tapów i seeda? (t/n): ").strip().lower()
        
        if auto_init in ['t', 'tak', 'y', 'yes']:
            # Automatyczna inicjalizacja
            taps = None
            seed = None
            print("Używam automatycznej inicjalizacji...")
        else:
            # Ręczna inicjalizacja
            taps_str = input(f"Podaj pozycje tapów (1-{length}), oddzielone przecinkami: ")
            taps = parse_taps(taps_str)
            
            max_value = (1 << length) - 1
            seed_str = input(f"Podaj stan początkowy (binarnie lub dziesiętnie, max {max_value}): ")
            seed = parse_seed(seed_str, length)
        
        # Liczba bitów do wygenerowania
        num_bits = int(input("Podaj liczbę bitów do wygenerowania: "))
        if num_bits <= 0:
            print("Błąd: Liczba bitów musi być dodatnia")
            return
        
        # Tworzenie i testowanie LFSR
        lfsr = LFSR(length=length, taps=taps, seed=seed)
        
        print(f"\n--- Konfiguracja LFSR ---")
        print(f"Długość: {lfsr.length} bitów")
        print(f"Pozycje tapów: {lfsr.taps}")
        print(f"Stan początkowy: {lfsr.get_state_binary()} ({lfsr.initial_state})")
        
        # Generowanie strumienia
        print(f"\nGenerowanie strumienia {num_bits} bitów...")
        start_time = time.time()
        keystream = lfsr.generate_keystream(num_bits)
        elapsed = time.time() - start_time
        
        display_binary_blocks(keystream, "Wygenerowany strumień kluczy")
        print(f"\nHex: {bits_to_hex(keystream)}")
        print(f"Czas generowania: {elapsed*1000:.4f} ms")
        
    except ValueError as e:
        print(f"Błąd: {e}")
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")


def interactive_geffe():
    """Interaktywny tryb konfiguracji generatora Geffe'go."""
    print("\n" + "=" * 80)
    print("TRYB INTERAKTYWNY - GENERATOR GEFFE'GO")
    print("=" * 80)
    
    try:
        # Pytamy o tryb inicjalizacji
        auto_init = input("\nUżyć automatycznej inicjalizacji wszystkich LFSR? (t/n): ").strip().lower()
        
        if auto_init in ['t', 'tak', 'y', 'yes']:
            # Automatyczna inicjalizacja - pytamy tylko o długości
            print("\n--- Konfiguracja LFSR1 (selektor) ---")
            len1 = int(input("Długość: "))
            taps1, seed1 = None, None
            
            print("\n--- Konfiguracja LFSR2 ---")
            len2 = int(input("Długość: "))
            taps2, seed2 = None, None
            
            print("\n--- Konfiguracja LFSR3 ---")
            len3 = int(input("Długość: "))
            taps3, seed3 = None, None
            
            print("\nUżywam automatycznej inicjalizacji tapów i seedów...")
        else:
            # Ręczna inicjalizacja
            print("\n--- Konfiguracja LFSR1 (selektor) ---")
            len1 = int(input("Długość: "))
            taps1 = parse_taps(input(f"Pozycje tapów (1-{len1}): "))
            seed1 = parse_seed(input("Stan początkowy: "), len1)
            
            print("\n--- Konfiguracja LFSR2 ---")
            len2 = int(input("Długość: "))
            taps2 = parse_taps(input(f"Pozycje tapów (1-{len2}): "))
            seed2 = parse_seed(input("Stan początkowy: "), len2)
            
            print("\n--- Konfiguracja LFSR3 ---")
            len3 = int(input("Długość: "))
            taps3 = parse_taps(input(f"Pozycje tapów (1-{len3}): "))
            seed3 = parse_seed(input("Stan początkowy: "), len3)
        
        # Liczba bitów
        num_bits = int(input("\nLiczba bitów do wygenerowania: "))
        
        # Tworzenie LFSR
        lfsr1 = LFSR(len1, taps1, seed1)
        lfsr2 = LFSR(len2, taps2, seed2)
        lfsr3 = LFSR(len3, taps3, seed3)
        
        print(f"\n--- Podsumowanie konfiguracji ---")
        print(f"LFSR1: length={len1}, taps={lfsr1.taps}, seed={lfsr1.get_state_binary()}")
        print(f"LFSR2: length={len2}, taps={lfsr2.taps}, seed={lfsr2.get_state_binary()}")
        print(f"LFSR3: length={len3}, taps={lfsr3.taps}, seed={lfsr3.get_state_binary()}")
        
        # Generowanie
        print(f"\nGenerowanie strumienia kluczy...")
        start_time = time.time()
        keystream = geffe_generator(lfsr1, lfsr2, lfsr3, num_bits)
        elapsed = time.time() - start_time
        
        display_binary_blocks(keystream, "Strumień kluczy Geffe'go")
        print(f"\nHex: {bits_to_hex(keystream)}")
        print(f"Czas generowania: {elapsed*1000:.4f} ms")
        
    except ValueError as e:
        print(f"Błąd: {e}")
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")


def interactive_stop_and_go():
    """Interaktywny tryb konfiguracji generatora Stop-and-Go."""
    print("\n" + "=" * 80)
    print("TRYB INTERAKTYWNY - GENERATOR STOP-AND-GO")
    print("=" * 80)
    
    try:
        # Pytamy o tryb inicjalizacji
        auto_init = input("\nUżyć automatycznej inicjalizacji wszystkich LFSR? (t/n): ").strip().lower()
        
        if auto_init in ['t', 'tak', 'y', 'yes']:
            # Automatyczna inicjalizacja - pytamy tylko o długości
            print("\n--- Konfiguracja LFSR Control ---")
            len_ctrl = int(input("Długość: "))
            taps_ctrl, seed_ctrl = None, None
            
            print("\n--- Konfiguracja LFSR R2 ---")
            len_r2 = int(input("Długość: "))
            taps_r2, seed_r2 = None, None
            
            print("\n--- Konfiguracja LFSR R3 ---")
            len_r3 = int(input("Długość: "))
            taps_r3, seed_r3 = None, None
            
            print("\nUżywam automatycznej inicjalizacji tapów i seedów...")
        else:
            # Ręczna inicjalizacja
            print("\n--- Konfiguracja LFSR Control ---")
            len_ctrl = int(input("Długość: "))
            taps_ctrl = parse_taps(input(f"Pozycje tapów (1-{len_ctrl}): "))
            seed_ctrl = parse_seed(input("Stan początkowy: "), len_ctrl)
            
            print("\n--- Konfiguracja LFSR R2 ---")
            len_r2 = int(input("Długość: "))
            taps_r2 = parse_taps(input(f"Pozycje tapów (1-{len_r2}): "))
            seed_r2 = parse_seed(input("Stan początkowy: "), len_r2)
            
            print("\n--- Konfiguracja LFSR R3 ---")
            len_r3 = int(input("Długość: "))
            taps_r3 = parse_taps(input(f"Pozycje tapów (1-{len_r3}): "))
            seed_r3 = parse_seed(input("Stan początkowy: "), len_r3)
        
        # Liczba bitów
        num_bits = int(input("\nLiczba bitów do wygenerowania: "))
        
        # Tworzenie LFSR
        lfsr_ctrl = LFSR(len_ctrl, taps_ctrl, seed_ctrl)
        lfsr_r2 = LFSR(len_r2, taps_r2, seed_r2)
        lfsr_r3 = LFSR(len_r3, taps_r3, seed_r3)
        
        print(f"\n--- Podsumowanie konfiguracji ---")
        print(f"LFSR Control: length={len_ctrl}, taps={lfsr_ctrl.taps}, seed={lfsr_ctrl.get_state_binary()}")
        print(f"LFSR R2:      length={len_r2}, taps={lfsr_r2.taps}, seed={lfsr_r2.get_state_binary()}")
        print(f"LFSR R3:      length={len_r3}, taps={lfsr_r3.taps}, seed={lfsr_r3.get_state_binary()}")
        
        # Generowanie
        print(f"\nGenerowanie strumienia kluczy...")
        start_time = time.time()
        keystream = stop_and_go_generator(lfsr_ctrl, lfsr_r2, lfsr_r3, num_bits)
        elapsed = time.time() - start_time
        
        display_binary_blocks(keystream, "Strumień kluczy Stop-and-Go")
        print(f"\nHex: {bits_to_hex(keystream)}")
        print(f"Czas generowania: {elapsed*1000:.4f} ms")
        
    except ValueError as e:
        print(f"Błąd: {e}")
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")


def interactive_shrinking():
    """Interaktywny tryb konfiguracji Shrinking Generator."""
    print("\n" + "=" * 80)
    print("TRYB INTERAKTYWNY - SHRINKING GENERATOR")
    print("=" * 80)
    
    try:
        # Pytamy o tryb inicjalizacji
        auto_init = input("\nUżyć automatycznej inicjalizacji wszystkich LFSR? (t/n): ").strip().lower()
        
        if auto_init in ['t', 'tak', 'y', 'yes']:
            # Automatyczna inicjalizacja - pytamy tylko o długości
            print("\n--- Konfiguracja LFSR A (dane) ---")
            len_a = int(input("Długość: "))
            taps_a, seed_a = None, None
            
            print("\n--- Konfiguracja LFSR S (selekcja) ---")
            len_s = int(input("Długość: "))
            taps_s, seed_s = None, None
            
            print("\nUżywam automatycznej inicjalizacji tapów i seedów...")
        else:
            # Ręczna inicjalizacja
            print("\n--- Konfiguracja LFSR A (dane) ---")
            len_a = int(input("Długość: "))
            taps_a = parse_taps(input(f"Pozycje tapów (1-{len_a}): "))
            seed_a = parse_seed(input("Stan początkowy: "), len_a)
            
            print("\n--- Konfiguracja LFSR S (selekcja) ---")
            len_s = int(input("Długość: "))
            taps_s = parse_taps(input(f"Pozycje tapów (1-{len_s}): "))
            seed_s = parse_seed(input("Stan początkowy: "), len_s)
        
        # Liczba bitów
        num_bits = int(input("\nLiczba bitów do wygenerowania: "))
        
        # Tworzenie LFSR
        lfsr_a = LFSR(len_a, taps_a, seed_a)
        lfsr_s = LFSR(len_s, taps_s, seed_s)
        
        print(f"\n--- Podsumowanie konfiguracji ---")
        print(f"LFSR A (dane):     length={len_a}, taps={lfsr_a.taps}, seed={lfsr_a.get_state_binary()}")
        print(f"LFSR S (selekcja): length={len_s}, taps={lfsr_s.taps}, seed={lfsr_s.get_state_binary()}")
        
        # Generowanie
        print(f"\nGenerowanie strumienia kluczy...")
        start_time = time.time()
        keystream = shrinking_generator(lfsr_a, lfsr_s, num_bits)
        elapsed = time.time() - start_time
        
        display_binary_blocks(keystream, "Strumień kluczy Shrinking Generator")
        print(f"\nHex: {bits_to_hex(keystream)}")
        print(f"Czas generowania: {elapsed*1000:.4f} ms")
        
    except ValueError as e:
        print(f"Błąd: {e}")
    except Exception as e:
        print(f"Nieoczekiwany błąd: {e}")


def main():
    """Główna funkcja programu z menu interaktywnym."""
    print("=" * 80)
    print("LABORATORIUM 4 - GENERATORY STRUMIENI KLUCZY (LFSR)")
    print("Kryptologia - Patryk Rakowski 2025")
    print("=" * 80)
    
    while True:
        print("\n" + "=" * 80)
        print("MENU GŁÓWNE")
        print("=" * 80)
        print("1. Demonstracja podstawowego LFSR (Zadanie 1)")
        print("2. Demonstracja generatorów strumieni kluczy (Zadanie 2)")
        print("3. Demonstracja automatycznej inicjalizacji LFSR")
        print("4. Tryb interaktywny - LFSR")
        print("5. Tryb interaktywny - Generator Geffe'go")
        print("6. Tryb interaktywny - Generator Stop-and-Go")
        print("7. Tryb interaktywny - Shrinking Generator")
        print("0. Wyjście")
        
        try:
            choice = input("\nWybierz opcję: ").strip()
            
            if choice == '1':
                zad1()
            elif choice == '2':
                zad2()
            elif choice == '3':
                demo_auto_lfsr()
            elif choice == '4':
                interactive_lfsr()
            elif choice == '5':
                interactive_geffe()
            elif choice == '6':
                interactive_stop_and_go()
            elif choice == '7':
                interactive_shrinking()
            elif choice == '0':
                print("\nDo widzenia!")
                break
            else:
                print("\nNieprawidłowy wybór. Spróbuj ponownie.")
        
        except KeyboardInterrupt:
            print("\n\nPrzerwano przez użytkownika. Do widzenia!")
            break
        except Exception as e:
            print(f"\nWystąpił błąd: {e}")


if __name__ == "__main__":
    main()

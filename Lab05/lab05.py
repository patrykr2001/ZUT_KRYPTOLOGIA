"""
Lab 05 - Testowanie generatorów pseudolosowych
Kryptologia - Patryk Rakowski 2025

Implementacja testów losowości dla generatorów z Lab04:
1. Testy FIPS 140-2:
   - Test pokerowy (Poker test)
   - Test długich podciągów (Long runs test)
   - Test podciągów (Runs test)
2. Test NIST SP 800-22 (opcjonalny):
   - Frequency Test within a Block
3. Testowanie generatorów: Geffe'go, Stop-and-Go, Shrinking Generator
"""

import sys
import os

# Dodaj ścieżkę do Lab04 aby zaimportować moduły
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Lab04'))

from LFSR import LFSR
from Generators import geffe_generator, stop_and_go_generator, shrinking_generator
from typing import List, Dict, Tuple
import time
from scipy.special import gammaincc

# ============================================================================
# TESTY FIPS 140-2
# ============================================================================

def monobit_test(bits: List[int]) -> Tuple[bool, Dict]:
    """
    Test monobitowy (nie jest w FIPS 140-2 dla 20000 bitów, ale pomocny).
    Sprawdza czy liczba jedynek jest bliska liczbie zer.
    
    Dla 20000 bitów: 9725 < ones < 10275
    """
    n = len(bits)
    ones = sum(bits)
    zeros = n - ones
    
    # Zakres akceptacji dla 20000 bitów zgodnie z FIPS 140-2
    passed = 9725 < ones < 10275
    
    return passed, {
        'ones': ones,
        'zeros': zeros,
        'threshold': '9725 < ones < 10275',
        'passed': passed
    }


def poker_test(bits: List[int], m: int = 4) -> Tuple[bool, Dict]:
    """
    Test pokerowy FIPS 140-2.
    
    Dzieli ciąg 20000 bitów na segmenty po m bitów (m=4) i oblicza
    statystykę chi-kwadrat dla rozkładu segmentów.
    
    Dla m=4 i n=20000:
    - Liczba segmentów: k = 5000
    - Liczba możliwych wartości: 2^m = 16
    - Próg akceptacji: 2.16 < X < 46.17
    
    Args:
        bits: lista 20000 bitów
        m: długość segmentu (domyślnie 4)
    
    Returns:
        (passed, stats_dict)
    """
    n = len(bits)
    k = n // m  # liczba segmentów
    num_sequences = 2 ** m  # liczba możliwych wartości m-bitowych
    
    # Zlicz wystąpienia każdego segmentu
    counts = [0] * num_sequences
    
    for i in range(k):
        # Pobierz m-bitowy segment
        segment = bits[i*m:(i+1)*m]
        # Konwertuj na liczbę
        value = sum(bit << (m - 1 - j) for j, bit in enumerate(segment))
        counts[value] += 1
    
    # Oblicz statystykę X (chi-kwadrat)
    X = (num_sequences / k) * sum(count ** 2 for count in counts) - k
    
    # Progi dla m=4, k=5000 (FIPS 140-2)
    lower_threshold = 2.16
    upper_threshold = 46.17
    
    passed = lower_threshold < X < upper_threshold
    
    return passed, {
        'X': X,
        'lower_threshold': lower_threshold,
        'upper_threshold': upper_threshold,
        'segments': k,
        'm': m,
        'passed': passed
    }


def runs_test(bits: List[int]) -> Tuple[bool, Dict]:
    """
    Test podciągów (Runs test) FIPS 140-2.
    
    Podciąg (run) to maksymalna sekwencja identycznych kolejnych bitów.
    Test sprawdza czy liczba podciągów różnych długości jest w akceptowalnym zakresie.
    
    Dla 20000 bitów, progi akceptacji:
    - Długość 1: 2315 - 2685
    - Długość 2: 1114 - 1386
    - Długość 3: 527 - 723
    - Długość 4: 240 - 384
    - Długość 5: 103 - 209
    - Długość 6+: 103 - 209
    
    Args:
        bits: lista 20000 bitów
    
    Returns:
        (passed, stats_dict)
    """
    n = len(bits)
    
    # Zlicz podciągi
    runs = []
    current_bit = bits[0]
    current_length = 1
    
    for i in range(1, n):
        if bits[i] == current_bit:
            current_length += 1
        else:
            runs.append(current_length)
            current_bit = bits[i]
            current_length = 1
    
    # Dodaj ostatni podciąg
    runs.append(current_length)
    
    # Zlicz podciągi według długości
    run_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
    
    for run_length in runs:
        if run_length >= 6:
            run_counts[6] += 1
        else:
            run_counts[run_length] += 1
    
    # Progi dla 20000 bitów (FIPS 140-2)
    thresholds = {
        1: (2315, 2685),
        2: (1114, 1386),
        3: (527, 723),
        4: (240, 384),
        5: (103, 209),
        6: (103, 209)
    }
    
    # Sprawdź czy wszystkie liczby są w zakresie
    passed = True
    details = {}
    
    for length, (lower, upper) in thresholds.items():
        count = run_counts[length]
        length_passed = lower <= count <= upper
        passed = passed and length_passed
        
        details[f'length_{length}{"+" if length == 6 else ""}'] = {
            'count': count,
            'range': f'{lower}-{upper}',
            'passed': length_passed
        }
    
    return passed, {
        'total_runs': len(runs),
        'details': details,
        'passed': passed
    }


def long_runs_test(bits: List[int]) -> Tuple[bool, Dict]:
    """
    Test długich podciągów (Long runs test) FIPS 140-2.
    
    Sprawdza czy w ciągu 20000 bitów występuje podciąg
    (run) 26 lub więcej identycznych kolejnych bitów.
    
    Test przechodzi (PASS) jeśli NIE ma podciągu długości >= 26.
    
    Args:
        bits: lista 20000 bitów
    
    Returns:
        (passed, stats_dict)
    """
    n = len(bits)
    max_run_length = 0
    current_length = 1
    
    for i in range(1, n):
        if bits[i] == bits[i-1]:
            current_length += 1
            max_run_length = max(max_run_length, current_length)
        else:
            current_length = 1
    
    # Test przechodzi jeśli najdłuższy podciąg < 26
    passed = max_run_length < 26
    
    return passed, {
        'max_run_length': max_run_length,
        'threshold': 26,
        'passed': passed
    }


def frequency_test_within_block(bits: List[int], M: int = 128) -> Tuple[bool, Dict]:
    """
    Frequency Test within a Block - NIST SP 800-22.
    
    Dzieli ciąg bitów na N bloków po M bitów i sprawdza
    czy proporcja jedynek w każdym bloku jest bliska 1/2.
    
    Args:
        bits: lista bitów
        M: rozmiar bloku (domyślnie 128)
    
    Returns:
        (passed, stats_dict)
    """
    n = len(bits)
    N = n // M  # liczba bloków
    
    if N == 0:
        return False, {
            'error': f'Za mało bitów dla rozmiaru bloku {M}',
            'passed': False
        }
    
    # Oblicz proporcję jedynek w każdym bloku
    chi_squared = 0.0
    
    for i in range(N):
        block = bits[i*M:(i+1)*M]
        ones = sum(block)
        pi = ones / M
        
        # Suma dla chi-kwadrat
        chi_squared += (pi - 0.5) ** 2
    
    chi_squared *= 4 * M
    
    # Oblicz P-value używając incomplete gamma function
    # P-value = igamc(N/2, chi_squared/2)
    p_value = gammaincc(N / 2.0, chi_squared / 2.0)
    
    # Test przechodzi jeśli P-value >= 0.01
    passed = p_value >= 0.01
    
    return passed, {
        'N': N,
        'M': M,
        'chi_squared': chi_squared,
        'p_value': p_value,
        'threshold': 0.01,
        'passed': passed
    }


# ============================================================================
# GENERATORY - FUNKCJE POMOCNICZE
# ============================================================================

def generate_geffe(lfsr_length: int, num_bits: int = 20000) -> List[int]:
    """
    Generuje ciąg bitów używając generatora Geffe'go.
    
    Args:
        lfsr_length: długość każdego z 3 LFSR
        num_bits: liczba bitów do wygenerowania
    
    Returns:
        lista bitów
    """
    lfsr1 = LFSR.create_random(lfsr_length, secure=False)
    lfsr2 = LFSR.create_random(lfsr_length, secure=False)
    lfsr3 = LFSR.create_random(lfsr_length, secure=False)
    
    return geffe_generator(lfsr1, lfsr2, lfsr3, num_bits)


def generate_stop_and_go(lfsr_length: int, num_bits: int = 20000) -> List[int]:
    """
    Generuje ciąg bitów używając generatora Stop-and-Go.
    
    Args:
        lfsr_length: długość każdego z 3 LFSR
        num_bits: liczba bitów do wygenerowania
    
    Returns:
        lista bitów
    """
    lfsr_ctrl = LFSR.create_random(lfsr_length, secure=False)
    lfsr_r2 = LFSR.create_random(lfsr_length, secure=False)
    lfsr_r3 = LFSR.create_random(lfsr_length, secure=False)
    
    return stop_and_go_generator(lfsr_ctrl, lfsr_r2, lfsr_r3, num_bits)


def generate_shrinking(lfsr_length: int, num_bits: int = 20000) -> List[int]:
    """
    Generuje ciąg bitów używając Shrinking Generator.
    
    Args:
        lfsr_length: długość każdego z 2 LFSR
        num_bits: liczba bitów do wygenerowania
    
    Returns:
        lista bitów
    """
    lfsr_a = LFSR.create_random(lfsr_length, secure=False)
    lfsr_s = LFSR.create_random(lfsr_length, secure=False)
    
    return shrinking_generator(lfsr_a, lfsr_s, num_bits)


# ============================================================================
# TESTOWANIE GENERATORÓW
# ============================================================================

def test_generator(generator_name: str, lfsr_length: int, num_bits: int = 20000, 
                   include_nist: bool = False) -> Dict:
    """
    Testuje generator wszystkimi dostępnymi testami.
    
    Args:
        generator_name: nazwa generatora ('geffe', 'stop_and_go', 'shrinking')
        lfsr_length: długość LFSR
        num_bits: liczba bitów do wygenerowania
        include_nist: czy włączyć test NIST
    
    Returns:
        słownik z wynikami testów
    """
    # Generuj ciąg bitów
    print(f"\nGenerowanie {num_bits} bitów dla {generator_name} (LFSR: {lfsr_length} bitów)...")
    start_time = time.time()
    
    if generator_name == 'geffe':
        bits = generate_geffe(lfsr_length, num_bits)
    elif generator_name == 'stop_and_go':
        bits = generate_stop_and_go(lfsr_length, num_bits)
    elif generator_name == 'shrinking':
        bits = generate_shrinking(lfsr_length, num_bits)
    else:
        raise ValueError(f"Nieznany generator: {generator_name}")
    
    generation_time = time.time() - start_time
    print(f"Wygenerowano w {generation_time:.4f} s")
    
    # Uruchom testy
    results = {
        'generator': generator_name,
        'lfsr_length': lfsr_length,
        'num_bits': num_bits,
        'generation_time': generation_time
    }
    
    print("\nUruchamianie testów...")
    
    # Test monobitowy (pomocniczy)
    passed, stats = monobit_test(bits)
    results['monobit'] = stats
    print(f"  Monobit test: {'PASS' if passed else 'FAIL'}")
    
    # Test pokerowy
    passed, stats = poker_test(bits)
    results['poker'] = stats
    print(f"  Poker test: {'PASS' if passed else 'FAIL'}")
    
    # Test podciągów
    passed, stats = runs_test(bits)
    results['runs'] = stats
    print(f"  Runs test: {'PASS' if passed else 'FAIL'}")
    
    # Test długich podciągów
    passed, stats = long_runs_test(bits)
    results['long_runs'] = stats
    print(f"  Long runs test: {'PASS' if passed else 'FAIL'}")
    
    # Test NIST (opcjonalny)
    if include_nist:
        passed, stats = frequency_test_within_block(bits)
        results['nist_frequency'] = stats
        print(f"  NIST Frequency test: {'PASS' if passed else 'FAIL'}")
    
    return results


def display_single_test_results(results: Dict):
    """
    Wyświetla szczegółowe wyniki testów dla jednego generatora.
    """
    print("\n" + "=" * 80)
    print("WYNIKI TESTÓW")
    print("=" * 80)
    
    print(f"\nGenerator: {results['generator']}")
    print(f"Długość LFSR: {results['lfsr_length']} bitów")
    print(f"Liczba wygenerowanych bitów: {results['num_bits']}")
    print(f"Czas generowania: {results['generation_time']:.4f} s")
    
    # Monobit test
    print("\n" + "-" * 80)
    print("1. MONOBIT TEST (pomocniczy)")
    print("-" * 80)
    mono = results['monobit']
    print(f"Liczba jedynek: {mono['ones']}")
    print(f"Liczba zer: {mono['zeros']}")
    print(f"Próg akceptacji: {mono['threshold']}")
    print(f"Wynik: {'✓ PASS' if mono['passed'] else '✗ FAIL'}")
    
    # Poker test
    print("\n" + "-" * 80)
    print("2. POKER TEST (FIPS 140-2)")
    print("-" * 80)
    poker = results['poker']
    print(f"Statystyka X: {poker['X']:.4f}")
    print(f"Próg dolny: {poker['lower_threshold']}")
    print(f"Próg górny: {poker['upper_threshold']}")
    print(f"Liczba segmentów: {poker['segments']} (po {poker['m']} bitów)")
    print(f"Wynik: {'✓ PASS' if poker['passed'] else '✗ FAIL'}")
    
    # Runs test
    print("\n" + "-" * 80)
    print("3. RUNS TEST (FIPS 140-2)")
    print("-" * 80)
    runs = results['runs']
    print(f"Całkowita liczba podciągów: {runs['total_runs']}")
    print("\nRozkład podciągów według długości:")
    print(f"{'Długość':<15} {'Liczba':<10} {'Zakres':<15} {'Status':<10}")
    print("-" * 50)
    
    for key, value in runs['details'].items():
        length_label = key.replace('length_', '')
        print(f"{length_label:<15} {value['count']:<10} {value['range']:<15} "
              f"{'✓ PASS' if value['passed'] else '✗ FAIL':<10}")
    
    print(f"\nWynik ogólny: {'✓ PASS' if runs['passed'] else '✗ FAIL'}")
    
    # Long runs test
    print("\n" + "-" * 80)
    print("4. LONG RUNS TEST (FIPS 140-2)")
    print("-" * 80)
    long_runs = results['long_runs']
    print(f"Najdłuższy podciąg: {long_runs['max_run_length']} bitów")
    print(f"Próg: < {long_runs['threshold']} bitów")
    print(f"Wynik: {'✓ PASS' if long_runs['passed'] else '✗ FAIL'}")
    
    # NIST test (jeśli dostępny)
    if 'nist_frequency' in results:
        print("\n" + "-" * 80)
        print("5. NIST FREQUENCY TEST WITHIN A BLOCK (NIST SP 800-22)")
        print("-" * 80)
        nist = results['nist_frequency']
        
        if 'error' in nist:
            print(f"BŁĄD: {nist['error']}")
        else:
            print(f"Liczba bloków: {nist['N']} (po {nist['M']} bitów)")
            print(f"Statystyka chi-kwadrat: {nist['chi_squared']:.4f}")
            print(f"P-value: {nist['p_value']:.6f}")
            print(f"Próg: P-value >= {nist['threshold']}")
            print(f"Wynik: {'✓ PASS' if nist['passed'] else '✗ FAIL'}")
    
    # Podsumowanie
    print("\n" + "=" * 80)
    print("PODSUMOWANIE")
    print("=" * 80)
    
    tests_passed = sum([
        results['monobit']['passed'],
        results['poker']['passed'],
        results['runs']['passed'],
        results['long_runs']['passed']
    ])
    
    total_tests = 4
    
    if 'nist_frequency' in results and 'passed' in results['nist_frequency']:
        tests_passed += results['nist_frequency']['passed']
        total_tests += 1
    
    print(f"\nTestów zaliczonych: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✓ Generator spełnia wszystkie wymagania testów losowości")
    else:
        print("✗ Generator NIE spełnia wszystkich wymagań testów losowości")


def test_all_generators(lfsr_lengths: List[int] = [4, 16, 24], 
                        num_bits: int = 20000,
                        include_nist: bool = False) -> Dict:
    """
    Testuje wszystkie generatory dla różnych długości LFSR.
    
    Args:
        lfsr_lengths: lista długości LFSR do przetestowania
        num_bits: liczba bitów do wygenerowania
        include_nist: czy włączyć test NIST
    
    Returns:
        słownik z wynikami dla wszystkich kombinacji
    """
    generators = ['geffe', 'stop_and_go', 'shrinking']
    all_results = {}
    
    print(f"\nGeneratory: {', '.join(generators)}")
    print(f"Długości LFSR: {', '.join(map(str, lfsr_lengths))} bitów")
    print(f"Liczba bitów na test: {num_bits}")
    print(f"Testy NIST: {'TAK' if include_nist else 'NIE'}")
    
    total_tests = len(generators) * len(lfsr_lengths)
    current_test = 0
    
    for generator in generators:
        all_results[generator] = {}
        
        for lfsr_length in lfsr_lengths:
            current_test += 1
            print(f"\n{'─' * 80}")
            print(f"Test {current_test}/{total_tests}: {generator} + LFSR {lfsr_length} bitów")
            print(f"{'─' * 80}")
            
            results = test_generator(generator, lfsr_length, num_bits, include_nist)
            all_results[generator][lfsr_length] = results
    
    return all_results


def display_comparison_table(all_results: Dict):
    """
    Wyświetla tabelę porównawczą wyników dla wszystkich generatorów.
    """
    print("\n" + "=" * 80)
    print("TABELA PORÓWNAWCZA WYNIKÓW")
    print("=" * 80)
    
    generators = list(all_results.keys())
    lfsr_lengths = list(all_results[generators[0]].keys())
    
    # Nagłówek tabeli
    print("\nTest: MONOBIT (pomocniczy)")
    print("-" * 80)
    print(f"{'Generator':<20} " + " ".join(f"LFSR {l:>2}b" for l in lfsr_lengths))
    print("-" * 80)
    
    for gen in generators:
        line = f"{gen:<20} "
        for length in lfsr_lengths:
            passed = all_results[gen][length]['monobit']['passed']
            line += f"{'✓ PASS' if passed else '✗ FAIL':>9} "
        print(line)
    
    # Poker test
    print("\nTest: POKER (FIPS 140-2)")
    print("-" * 80)
    print(f"{'Generator':<20} " + " ".join(f"LFSR {l:>2}b" for l in lfsr_lengths))
    print("-" * 80)
    
    for gen in generators:
        line = f"{gen:<20} "
        for length in lfsr_lengths:
            passed = all_results[gen][length]['poker']['passed']
            X = all_results[gen][length]['poker']['X']
            line += f"{'✓' if passed else '✗'} {X:6.2f}  "
        print(line)
    
    # Runs test
    print("\nTest: RUNS (FIPS 140-2)")
    print("-" * 80)
    print(f"{'Generator':<20} " + " ".join(f"LFSR {l:>2}b" for l in lfsr_lengths))
    print("-" * 80)
    
    for gen in generators:
        line = f"{gen:<20} "
        for length in lfsr_lengths:
            passed = all_results[gen][length]['runs']['passed']
            line += f"{'✓ PASS' if passed else '✗ FAIL':>9} "
        print(line)
    
    # Long runs test
    print("\nTest: LONG RUNS (FIPS 140-2)")
    print("-" * 80)
    print(f"{'Generator':<20} " + " ".join(f"LFSR {l:>2}b" for l in lfsr_lengths))
    print("-" * 80)
    
    for gen in generators:
        line = f"{gen:<20} "
        for length in lfsr_lengths:
            passed = all_results[gen][length]['long_runs']['passed']
            max_run = all_results[gen][length]['long_runs']['max_run_length']
            line += f"{'✓' if passed else '✗'} {max_run:3d}    "
        print(line)
    
    if 'nist_frequency' in all_results[generators[0]][lfsr_lengths[0]]:
        print("\nTest: NIST FREQUENCY WITHIN A BLOCK (NIST SP 800-22)")
        print("-" * 80)
        print(f"{'Generator':<20} " + " ".join(f"LFSR {l:>2}b" for l in lfsr_lengths))
        print("-" * 80)
        
        for gen in generators:
            line = f"{gen:<20} "
            for length in lfsr_lengths:
                nist = all_results[gen][length]['nist_frequency']
                if 'error' in nist:
                    line += "  ERROR   "
                else:
                    passed = nist['passed']
                    p_val = nist['p_value']
                    line += f"{'✓' if passed else '✗'} {p_val:.4f} "
            print(line)
    
    # Podsumowanie
    print("\n" + "=" * 80)
    print("PODSUMOWANIE")
    print("=" * 80)
    
    print(f"\n{'Generator':<20} " + " ".join(f"LFSR {l:>2}b" for l in lfsr_lengths))
    print("-" * 80)
    
    for gen in generators:
        line = f"{gen:<20} "
        for length in lfsr_lengths:
            results = all_results[gen][length]
            
            # Zlicz zaliczone testy
            tests_passed = sum([
                results['monobit']['passed'],
                results['poker']['passed'],
                results['runs']['passed'],
                results['long_runs']['passed']
            ])
            
            total_tests = 4
            
            if 'nist_frequency' in results and 'passed' in results['nist_frequency']:
                tests_passed += results['nist_frequency']['passed']
                total_tests += 1
            
            line += f"{tests_passed}/{total_tests}     "
        print(line)
    

def display_menu():
    """Wyświetla menu główne."""
    print("=" * 80)
    print("\n1. Test pojedynczego generatora")
    print("2. Test wszystkich generatorów (pełna analiza)")
    print("3. Informacje o testach")
    print("0. Wyjście")
    print("\n" + "-" * 80)


def test_single_generator_menu():
    """Menu dla testowania pojedynczego generatora."""
    
    # Wybór generatora
    print("\nWybierz generator:")
    print("1. Generator Geffe'go")
    print("2. Generator Stop-and-Go")
    print("3. Shrinking Generator")
    
    try:
        gen_choice = input("\nWybór (1-3): ").strip()
        
        generator_map = {
            '1': 'geffe',
            '2': 'stop_and_go',
            '3': 'shrinking'
        }
        
        if gen_choice not in generator_map:
            print("Nieprawidłowy wybór")
            return
        
        generator = generator_map[gen_choice]
        
        # Wybór długości LFSR
        print("\nWybierz długość LFSR:")
        print("1. 4 bity")
        print("2. 16 bitów")
        print("3. 24 bity")
        print("4. Własna długość")
        
        length_choice = input("\nWybór (1-4): ").strip()
        
        if length_choice == '1':
            lfsr_length = 4
        elif length_choice == '2':
            lfsr_length = 16
        elif length_choice == '3':
            lfsr_length = 24
        elif length_choice == '4':
            lfsr_length = int(input("Podaj długość LFSR (3-32): ").strip())
            if lfsr_length < 3 or lfsr_length > 32:
                print("Długość poza zakresem")
                return
        else:
            print("Nieprawidłowy wybór")
            return
        
        # Liczba bitów
        num_bits_input = input("\nLiczba bitów do wygenerowania (domyślnie 20000): ").strip()
        num_bits = int(num_bits_input) if num_bits_input else 20000
        
        # Test NIST
        include_nist = False
        nist_choice = input("\nWłączyć test NIST? (t/n, domyślnie n): ").strip().lower()
        include_nist = nist_choice in ['t', 'tak', 'y', 'yes']
        
        # Uruchom test
        results = test_generator(generator, lfsr_length, num_bits, include_nist)
        display_single_test_results(results)
        
    except ValueError as e:
        print(f"Błąd: {e}")
    except KeyboardInterrupt:
        print("\n\nPrzerwano przez użytkownika")


def test_all_generators_menu():
    """Menu dla testowania wszystkich generatorów."""
    
    try:
        # Długości LFSR
        print("\nUżyć domyślnych długości LFSR (4, 16, 24 bity)?")
        use_default = input("(t/n, domyślnie t): ").strip().lower()
        
        if use_default in ['n', 'nie', 'no']:
            lengths_input = input("Podaj długości oddzielone spacją (np. 4 8 16 24): ").strip()
            lfsr_lengths = [int(x) for x in lengths_input.split()]
        else:
            lfsr_lengths = [4, 16, 24]
        
        # Liczba bitów
        num_bits_input = input("\nLiczba bitów do wygenerowania (domyślnie 20000): ").strip()
        num_bits = int(num_bits_input) if num_bits_input else 20000
        
        # Test NIST
        include_nist = False
        nist_choice = input("\nWłączyć test NIST? (t/n, domyślnie n): ").strip().lower()
        include_nist = nist_choice in ['t', 'tak', 'y', 'yes']
        
        # Uruchom testy
        all_results = test_all_generators(lfsr_lengths, num_bits, include_nist)
        display_comparison_table(all_results)
        
    except ValueError as e:
        print(f"Błąd: {e}")
    except KeyboardInterrupt:
        print("\n\nPrzerwano przez użytkownika")


def main():
    """Główna funkcja programu."""
    print("=" * 80)
    print("LABORATORIUM 5 - TESTOWANIE GENERATORÓW PSEUDOLOSOWYCH")
    print("Kryptologia - Patryk Rakowski 2025")
    print("=" * 80)
    
    while True:
        try:
            display_menu()
            choice = input("Wybór: ").strip()
            
            if choice == '1':
                test_single_generator_menu()
            elif choice == '2':
                test_all_generators_menu()
            elif choice == '0':
                break
            else:
                print("\nNieprawidłowy wybór. Spróbuj ponownie.")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nWystąpił błąd: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

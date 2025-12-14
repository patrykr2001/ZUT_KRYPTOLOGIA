# Plan: Randomness Testing Application for PRNG Generators

Implementacja aplikacji testującej losowość generatorów pseudolosowych z Lab04 (Geffe, Stop-and-Go, Shrinking) przy użyciu testów FIPS 140-2 i opcjonalnie NIST SP 800-22. Aplikacja w trybie tekstowym z menu interaktywnym i tabelarycznymi wynikami.

## Steps

1. **Zaimplementować testy FIPS 140-2** w `lab05.py` jako funkcje przyjmujące listę bitów (20000 bitów): `poker_test()`, `long_runs_test()`, `runs_test()`, oraz opcjonalnie `frequency_test_within_block()` używając `scipy.special.gammaincc` dla funkcji igamc.

2. **Utworzyć funkcje pomocnicze** generujące ciągi binarne z każdego generatora: `generate_geffe()`, `generate_stop_and_go()`, `generate_shrinking()` dla różnych długości LFSR (4, 16, 24 bity) importując z `Lab04/Generators.py`, `Lab04/LFSR.py`.

3. **Zaimplementować funkcję testującą** `test_generator()` która dla danego generatora i długości LFSR uruchamia wszystkie 3-4 testy i zwraca wyniki (pass/fail) oraz wartości statystyczne w strukturze danych.

4. **Utworzyć menu interaktywne** z opcjami: (1) test pojedynczego generatora z wyborem długości LFSR, (2) test wszystkich generatorów dla wszystkich długości LFSR z wyświetleniem tabeli wyników, (3) wyjście.

5. **Zaimplementować wyświetlanie wyników** w formie tabelarycznej (tabela 3 generatory × 3 długości LFSR) pokazującej pass/fail dla każdego testu oraz statystyki, wraz z analizą wpływu długości LFSR na wyniki testów.

## Further Considerations

1. **Specyfikacja testów FIPS 140-2** - czy masz dostęp do dokumentacji FIPS 140-2 z dokładnymi progami akceptacji dla testów, czy implementować według standardowych wartości (np. poker test: X² < 2.16 dla α=0.05)?

2. **Funkcja igamc** - użyć `scipy.special.gammaincc(a, x)` dla opcjonalnego testu NIST, czy alternatywnej implementacji?

3. **Format wyników** - czy tabela ma być zapisywana do pliku (np. CSV lub TXT) oprócz wyświetlania na ekranie?

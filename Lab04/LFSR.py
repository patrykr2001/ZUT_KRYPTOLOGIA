from typing import List, Optional
import secrets
import random

class LFSR:
    """
    Liniowy rejestr przesuwający z konfigurowalnymi pozycjami tapów.
    
    Parametry:
        length: długość rejestru w bitach
        taps: lista pozycji tapów (indeksowanie od 1), None dla automatycznej inicjalizacji
        seed: stan początkowy rejestru (klucz kryptograficzny), None dla automatycznej inicjalizacji
    """
    
    # Baza wielomianów maksymalnej długości dla popularnych rozmiarów rejestrów
    # Źródło: standardowe wielomiany prymitywne używane w kryptografii
    MAXIMAL_LENGTH_TAPS = {
        3: [3, 2],
        4: [4, 3],
        5: [5, 3],
        6: [6, 5],
        7: [7, 6],
        8: [8, 6, 5, 4],
        9: [9, 5],
        10: [10, 7],
        11: [11, 9],
        12: [12, 11, 10, 4],
        13: [13, 12, 11, 8],
        14: [14, 13, 12, 2],
        15: [15, 14],
        16: [16, 15, 13, 4],
        17: [17, 14],
        18: [18, 11],
        19: [19, 18, 17, 14],
        20: [20, 17],
        21: [21, 19],
        22: [22, 21],
        23: [23, 18],
        24: [24, 23, 22, 17],
        25: [25, 22],
        28: [28, 25],
        29: [29, 27],
        31: [31, 28],
        32: [32, 31, 30, 10],
        33: [33, 20],
        35: [35, 33],
        36: [36, 25],
        39: [39, 35],
        41: [41, 38],
        47: [47, 42],
        49: [49, 40],
        52: [52, 49],
        55: [55, 31],
        57: [57, 50],
        58: [58, 39],
        60: [60, 59],
        63: [63, 62],
        64: [64, 63, 61, 60],
        71: [71, 67],
        79: [79, 70],
        89: [89, 51],
        95: [95, 84],
        96: [96, 94, 49, 47],
        97: [97, 91],
        127: [127, 126],
        128: [128, 126, 101, 99],
    }
    
    @staticmethod
    def generate_random_seed(length: int, secure: bool = True) -> int:
        """
        Generuje losowy stan początkowy dla rejestru o danej długości.
        
        Args:
            length: długość rejestru w bitach
            secure: czy użyć kryptograficznie bezpiecznego generatora (secrets)
        
        Returns:
            Losowa liczba całkowita w zakresie [1, 2^length - 1]
        """
        if secure:
            # Używamy secrets dla kryptograficznej jakości
            seed = secrets.randbits(length)
        else:
            # Używamy random dla szybszej generacji (testy, demonstracje)
            seed = random.getrandbits(length)
        
        # Upewniamy się, że seed != 0
        if seed == 0:
            seed = 1
        
        return seed
    
    @staticmethod
    def get_random_taps(length: int) -> List[int]:
        """
        Zwraca pozycje tapów dla rejestru o danej długości.
        Najpierw sprawdza bazę znanych wielomianów maksymalnej długości,
        jeśli nie znaleziono - generuje losowe taps.
        
        Args:
            length: długość rejestru w bitach
        
        Returns:
            Lista pozycji tapów (1-indeksowane)
        """
        # Sprawdzamy czy mamy predefiniowane taps dla tej długości
        if length in LFSR.MAXIMAL_LENGTH_TAPS:
            return LFSR.MAXIMAL_LENGTH_TAPS[length].copy()
        
        # Jeśli nie ma w bazie, generujemy losowe
        # Zawsze zawieramy pozycję length (największy bit) i losujemy 2-3 inne
        num_taps = random.randint(2, min(4, length))
        taps = [length]  # Zawsze zawieramy najwyższą pozycję
        
        # Losujemy pozostałe pozycje
        available_positions = list(range(1, length))
        random.shuffle(available_positions)
        taps.extend(available_positions[:num_taps-1])
        
        return sorted(taps, reverse=True)
    
    @classmethod
    def create_random(cls, length: int, secure: bool = True):
        """
        Tworzy LFSR z automatycznie wygenerowanymi tapami i seedem.
        
        Args:
            length: długość rejestru w bitach
            secure: czy użyć kryptograficznie bezpiecznego generatora dla seeda
        
        Returns:
            Nowa instancja LFSR z losowymi parametrami
        
        Example:
            >>> lfsr = LFSR.create_random(16)
            >>> print(lfsr)
        """
        taps = cls.get_random_taps(length)
        seed = cls.generate_random_seed(length, secure)
        return cls(length, taps, seed)
    
    def __init__(self, length: int, taps: Optional[List[int]] = None, seed: Optional[int] = None):
        """
        Inicjalizacja LFSR.
        
        Args:
            length: długość rejestru w bitach
            taps: pozycje tapów (1-indeksowane), np. [16,14,13,11] dla x^16+x^14+x^13+x^11+1
                  Jeśli None, automatycznie wybiera optymalne taps
            seed: stan początkowy jako liczba całkowita (musi być != 0)
                  Jeśli None, generuje losowy seed
        """
        if length <= 0:
            raise ValueError("Długość rejestru musi być dodatnia")
        
        # Automatyczna inicjalizacja taps jeśli nie podano
        if taps is None:
            taps = self.get_random_taps(length)
        
        # Automatyczna inicjalizacja seed jeśli nie podano
        if seed is None:
            seed = self.generate_random_seed(length, secure=True)
        
        if seed == 0:
            raise ValueError("Stan początkowy nie może być zerem (rejestr zdegenerowany)")
        if not taps:
            raise ValueError("Lista tapów nie może być pusta")
        
        self.length = length
        self.taps = sorted(taps, reverse=True)  # Sortujemy malejąco dla wygody
        self.state = seed & ((1 << length) - 1)  # Maskujemy do długości rejestru
        self.initial_state = self.state
        
        # Walidacja tapów
        for tap in self.taps:
            if tap < 1 or tap > length:
                raise ValueError(f"Pozycja tapa {tap} poza zakresem [1, {length}]")
    
    def step(self) -> int:
        """
        Wykonuje jeden krok rejestru i zwraca wyjściowy bit.
        
        Returns:
            Bit wyjściowy (0 lub 1)
        """
        # Obliczamy bit sprzężenia zwrotnego (XOR bitów na pozycjach tapów)
        feedback = 0
        for tap in self.taps:
            # Pozycje tapów są 1-indeksowane, więc tap=1 to najbardziej znaczący bit
            bit_position = self.length - tap
            feedback ^= (self.state >> bit_position) & 1
        
        # Bit wyjściowy to najmniej znaczący bit
        output_bit = self.state & 1
        
        # Przesuwamy rejestr w prawo i wstawiamy feedback na pozycję MSB
        self.state = (self.state >> 1) | (feedback << (self.length - 1))
        
        return output_bit
    
    def generate_keystream(self, num_bits: int) -> List[int]:
        """
        Generuje strumień kluczy o określonej długości.
        
        Args:
            num_bits: liczba bitów do wygenerowania
            
        Returns:
            Lista bitów (0 i 1)
        """
        return [self.step() for _ in range(num_bits)]
    
    def reset(self):
        """Resetuje rejestr do stanu początkowego."""
        self.state = self.initial_state
    
    def get_state_binary(self) -> str:
        """Zwraca aktualny stan rejestru jako ciąg binarny."""
        return format(self.state, f'0{self.length}b')
    
    def __repr__(self):
        return f"LFSR(length={self.length}, taps={self.taps}, state={self.get_state_binary()})"


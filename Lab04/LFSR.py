from typing import List

class LFSR:
    """
    Liniowy rejestr przesuwający z konfigurowalnymi pozycjami tapów.
    
    Parametry:
        length: długość rejestru w bitach
        taps: lista pozycji tapów (indeksowanie od 1)
        seed: stan początkowy rejestru (klucz kryptograficzny)
    """
    
    def __init__(self, length: int, taps: List[int], seed: int):
        """
        Inicjalizacja LFSR.
        
        Args:
            length: długość rejestru w bitach
            taps: pozycje tapów (1-indeksowane), np. [16,14,13,11] dla x^16+x^14+x^13+x^11+1
            seed: stan początkowy jako liczba całkowita (musi być != 0)
        """
        if seed == 0:
            raise ValueError("Stan początkowy nie może być zerem (rejestr zdegenerowany)")
        if length <= 0:
            raise ValueError("Długość rejestru musi być dodatnia")
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


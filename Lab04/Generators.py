from LFSR import LFSR
from typing import List

def geffe_generator(lfsr1: LFSR, lfsr2: LFSR, lfsr3: LFSR, num_bits: int) -> List[int]:
    """
    Generator Geffe'go - kombinuje 3 LFSR.
    
    Formuła: output = (L1 AND L2) XOR ((NOT L1) AND L3)
    L1 działa jako selektor między L2 i L3.
    
    Args:
        lfsr1: pierwszy LFSR (selektor)
        lfsr2: drugi LFSR
        lfsr3: trzeci LFSR
        num_bits: liczba bitów do wygenerowania
        
    Returns:
        Lista bitów strumienia kluczy
    """
    keystream = []
    
    for _ in range(num_bits):
        bit1 = lfsr1.step()
        bit2 = lfsr2.step()
        bit3 = lfsr3.step()
        
        # output = (L1 AND L2) XOR ((NOT L1) AND L3)
        output = (bit1 & bit2) ^ ((1 ^ bit1) & bit3)
        keystream.append(output)
    
    return keystream


def stop_and_go_generator(lfsr_control: LFSR, lfsr_r2: LFSR, lfsr_r3: LFSR, num_bits: int) -> List[int]:
    """
    Generator Stop-and-Go - używa rejestru kontrolnego do sterowania dwoma rejestrami danych.
    
    Mechanizm:
    - Rejestr kontrolny zawsze się przesuwa
    - Jeśli control = 0: przesuwa się R2, output = R2 XOR R3
    - Jeśli control = 1: przesuwa się R3, output = R2 XOR R3
    
    Args:
        lfsr_control: rejestr kontrolny
        lfsr_r2: rejestr danych R2
        lfsr_r3: rejestr danych R3
        num_bits: liczba bitów do wygenerowania
        
    Returns:
        Lista bitów strumienia kluczy
    """
    keystream = []
    
    # Pobieramy początkowe wartości R2 i R3
    bit_r2 = lfsr_r2.step()
    bit_r3 = lfsr_r3.step()
    
    for _ in range(num_bits):
        control_bit = lfsr_control.step()
        
        if control_bit == 0:
            # Przesuwamy R2
            bit_r2 = lfsr_r2.step()
        else:
            # Przesuwamy R3
            bit_r3 = lfsr_r3.step()
        
        # Wyjście to XOR aktualnych wartości R2 i R3
        output = bit_r2 ^ bit_r3
        keystream.append(output)
    
    return keystream


def shrinking_generator(lfsr_a: LFSR, lfsr_s: LFSR, num_bits: int) -> List[int]:
    """
    Shrinking Generator - używa rejestru selekcji do filtrowania wyjścia rejestru A.
    
    Mechanizm:
    - Oba rejestry zawsze się przesuwają
    - Jeśli S = 1: output = A (emitujemy bit z A)
    - Jeśli S = 0: pomijamy bit z A (nie emitujemy nic)
    
    Args:
        lfsr_a: rejestr danych A
        lfsr_s: rejestr selekcji S
        num_bits: liczba bitów do wygenerowania
        
    Returns:
        Lista bitów strumienia kluczy
    """
    keystream = []
    
    while len(keystream) < num_bits:
        bit_a = lfsr_a.step()
        bit_s = lfsr_s.step()
        
        # Jeśli S = 1, emitujemy bit z A
        if bit_s == 1:
            keystream.append(bit_a)
    
    return keystream[:num_bits]  # Obcinamy do dokładnie num_bits

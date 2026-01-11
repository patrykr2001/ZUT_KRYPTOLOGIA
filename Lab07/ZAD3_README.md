# Zadanie 11.3 - Distributed Proof-of-Work Simulation

Symulacja mechanizmu Proof-of-Work dla 4 węzłów kopiących z wykorzystaniem protokołu TCP/IP.

## Architektura

System składa się z:
- **1 węzeł pośrednik (broker)** - koordynuje wykopywanie bloków
- **4 węzły kopiące (miners)** - konkurują o wykopanie bloków

## Komponenty

### 1. `zad3_broker.py` - Węzeł Pośrednika
Odpowiedzialności:
- Nasłuchuje połączeń od węzłów kopiących na porcie 5000
- Generuje losowe transakcje dla każdego nowego bloku
- Odbiera wykopane bloki od węzłów
- Weryfikuje numery bloków (odrzuca duplikaty - desynchronizacja)
- Broadcastuje akceptowane bloki do wszystkich węzłów
- Wyświetla szczegółowe informacje o każdym zaakceptowanym bloku

### 2. `zad3_miner.py` - Węzeł Kopiący
Odpowiedzialności:
- Łączy się z brokerem przez TCP
- Rejestruje się z unikalnym ID węzła
- Odbiera zadania kopania (transakcje, previous_hash, block_number)
- Wykonuje Proof-of-Work używając `BlockMiner.mine_block()` z [blockchain_mining.py](blockchain_mining.py)
- Wysyła wykopane bloki do brokera
- Przerywa aktualne kopanie po otrzymaniu informacji o nowo wykopanym bloku
- Rozpoczyna kopanie kolejnego bloku

### 3. `zad3_launcher.py` - Skrypt Uruchomieniowy
- Uruchamia brokera i 4 węzły kopiące jako osobne procesy
- Każdy proces w osobnym oknie konsoli (Windows)
- Łatwe zarządzanie wszystkimi procesami (Ctrl+C kończy wszystkie)

## Protokół Komunikacji

Wszystkie wiadomości są serializowane przez `pickle` z prefiksem długości (4 bajty).

### Typy wiadomości:

#### 1. REGISTER (Miner → Broker)
```python
{
    'type': 'REGISTER',
    'node_id': int
}
```

#### 2. NEW_TASK (Broker → Miner)
```python
{
    'type': 'NEW_TASK',
    'transactions': [str, ...],
    'previous_hash': bytes,
    'block_number': int,
    'difficulty': int
}
```

#### 3. BLOCK_MINED (Miner → Broker)
```python
{
    'type': 'BLOCK_MINED',
    'block': Block,
    'attempts': int,
    'elapsed': float
}
```

#### 4. BLOCK_ACCEPTED (Broker → All Miners)
```python
{
    'type': 'BLOCK_ACCEPTED',
    'block': Block,
    'winning_node': int
}
```

## Uruchomienie

### Metoda 1: Launcher (zalecane)
```bash
python zad3_launcher.py [difficulty]
```

Przykłady:
```bash
python zad3_launcher.py          # Domyślna trudność: 20 bitów
python zad3_launcher.py 18       # Łatwiejsze (szybsze)
python zad3_launcher.py 22       # Trudniejsze (wolniejsze)
```

### Metoda 2: Ręczne uruchomienie

**Terminal 1 - Broker:**
```bash
python zad3_broker.py
```

**Terminal 2-5 - Węzły kopiące:**
```bash
python zad3_miner.py 1
python zad3_miner.py 2
python zad3_miner.py 3
python zad3_miner.py 4
```

## Mechanizm Działania

1. **Inicjalizacja:**
   - Broker startuje i nasłuchuje na porcie 5000
   - Generuje początkowe transakcje
   - Węzły kopiące łączą się i rejestrują

2. **Kopanie:**
   - Broker wysyła zadanie NEW_TASK do wszystkich węzłów
   - Każdy węzeł rozpoczyna kopanie w osobnym wątku
   - Węzły wykonują Proof-of-Work (szukają nonce spełniającego trudność)
   - Co 10,000 prób węzły sprawdzają flagę przerwania

3. **Znalezienie bloku:**
   - Węzeł znajdujący poprawny nonce wysyła BLOCK_MINED do brokera
   - Broker weryfikuje block_number:
     - ✅ Akceptuje jeśli poprawny
     - ❌ Odrzuca jeśli blok już wykopany (desynchronizacja)

4. **Akceptacja i synchronizacja:**
   - Broker wyświetla szczegóły zaakceptowanego bloku
   - Wysyła BLOCK_ACCEPTED do wszystkich węzłów
   - Wszystkie węzły przerywają aktualne kopanie
   - Broker generuje nowe transakcje i wysyła NEW_TASK
   - Cykl się powtarza

## Obsługa Desynchronizacji

System uwzględnia możliwość desynchronizacji zgodnie z wymaganiami:

- Broker sprawdza `block.block_number` przy każdym odebranym bloku
- Jeśli blok z numerem X został już wykopany, broker odrzuca kolejne bloki X
- Komunikat odrzucenia jest wyświetlany na konsoli brokera
- Węzeł wysyłający odrzucony blok kontynuuje kopanie następnego bloku

## Przykładowy Output

### Broker:
```
================================================================================
[BROKER] ✅ BLOCK ACCEPTED from Node 2
================================================================================
  Block Number:    5
  Block Hash:      000001a4c8f2b3e5d9a1c4f8e2b7d3a9c5f1e8d4a0b6c2f9e5d1a7c3f8e4d0a6
  Previous Hash:   00000823b5c1e9f3d7a2c8f4e0b6d2a8c4f0e7d3a9b5c1f8e4d0a6c2f9e5d1a7
  Merkle Root:     a3b5c7d9e1f3a5b7c9d1e3f5a7b9c1d3e5f7a9b1c3d5e7f9a1b3c5d7e9f1a3b5
  Timestamp:       2026-01-10 14:23:45
  Nonce:           1,247,893
  Attempts:        1,247,894
  Time:            3.45s
  Hash Rate:       361,709.28 H/s
================================================================================
```

### Miner:
```
[Node 2] 🔨 Starting mining for block 5
[Node 2]    Difficulty: 20 bits
[Node 2]    Transactions: 5
[Node 2] Mining... 10,000 attempts, 342,857.14 H/s
[Node 2] Mining... 20,000 attempts, 348,432.81 H/s

[Node 2] ✅ Block 5 MINED!
[Node 2]    Hash: 000001a4c8f2b3e5d9a1c4f8e2b7...
[Node 2]    Nonce: 1247893
[Node 2]    Attempts: 1,247,894
[Node 2]    Time: 3.45s

[Node 2] 🎉 MY BLOCK WAS ACCEPTED! Block #5
```

## Parametry Wydajności

Zalecane trudności dla różnych celów testowych:

| Difficulty | Średni czas | Przypadek użycia |
|------------|-------------|------------------|
| 16 bits    | ~0.02s      | Szybkie testy |
| 18 bits    | ~0.1s       | Demo |
| 20 bits    | ~0.5s       | Standardowe (default) |
| 22 bits    | ~2s         | Realistyczne |
| 24 bits    | ~8s         | Konkurencyjne |

**Uwaga:** Czasy są szacunkowe i zależą od mocy obliczeniowej komputera.

## Wymagania

- Python 3.7+
- Moduł `blockchain_mining.py` z Lab07 (zawiera BlockMiner, Block, MerkleTree)
- System operacyjny: Windows (nowe okna konsoli) lub Linux/Mac (procesy w tle)

## Szczegóły Implementacyjne

### Threading Model
- **Broker:** Wątek główny + wątek akceptujący połączenia + wątek per węzeł
- **Miner:** Wątek główny (nasłuchiwanie) + wątek kopania

### Synchronizacja
- Flagi `threading.Event` do przerwania kopania
- Blokady `threading.Lock` dla współdzielonej listy węzłów
- Sprawdzanie flagi co 10,000 prób (balans responsywność/wydajność)

### Bezpieczeństwo Sieci
- Prefiksy długości zapobiegają problemom z granicami wiadomości TCP
- Obsługa błędów połączenia i automatyczne usuwanie martwych węzłów
- Socket timeout dla graceful shutdown

## Ograniczenia (zgodnie z zadaniem)

Zgodnie z treścią zadania, system pomija:
- ✗ Sprawdzanie poprawności transakcji
- ✗ Przechowywanie pełnego blockchain
- ✗ Rozgałęzianie się blockchain
- ✓ Zakłada, że wszystkie węzły zawsze otrzymują bloki na czas

## Autor

Implementacja zadania 11.3 z kursu Kryptologii (Lab 07)

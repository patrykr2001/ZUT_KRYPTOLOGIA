using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;

namespace Lab08;

/// <summary>
/// Deterministyczny generator liczb pseudolosowych oparty na HMAC-SHA256
/// Używany do bezpiecznego generowania klucza prywatnego z ziarna
/// </summary>
class DeterministicRng
{
    private readonly byte[] _seed;
    private ulong _counter;

    public DeterministicRng(byte[] seed)
    {
        if (seed.Length != 32)
            throw new ArgumentException("Ziarno musi mieć dokładnie 32 bajty");

        _seed = new byte[32];
        Array.Copy(seed, _seed, 32);
        _counter = 0;
    }

    /// <summary>
    /// Generuje kolejne pseudolosowe bajty deterministycznie z ziarna
    /// </summary>
    public void GetBytes(byte[] buffer)
    {
        using var hmac = new HMACSHA256(_seed);

        int offset = 0;
        while (offset < buffer.Length)
        {
            // Konwertuj licznik na bajty
            byte[] counterBytes = BitConverter.GetBytes(_counter);
            byte[] hash = hmac.ComputeHash(counterBytes);

            int bytesToCopy = Math.Min(hash.Length, buffer.Length - offset);
            Array.Copy(hash, 0, buffer, offset, bytesToCopy);

            offset += bytesToCopy;
            _counter++;
        }
    }
}

/// <summary>
/// Implementacja podpisu jednorazowego Lamporta (Lamport One-Time Signature)
/// </summary>
class LamportSignature
{
    private readonly HashAlgorithmName _hashAlgorithm;
    private readonly int _hashSize; // w bajtach

    public LamportSignature(HashAlgorithmName hashAlgorithm)
    {
        _hashAlgorithm = hashAlgorithm;
        _hashSize = hashAlgorithm.Name switch
        {
            "SHA256" => 32,
            "SHA384" => 48,
            "SHA512" => 64,
            _ => throw new ArgumentException("Nieobsługiwany algorytm hash")
        };
    }

    /// <summary>
    /// Generuje parę kluczy (prywatny, publiczny) - WERSJA LEGACY do porównania
    /// Klucz prywatny: 256 par losowych wartości (po 2 na każdy bit)
    /// Klucz publiczny: hashe kluczy prywatnych
    /// </summary>
    public (byte[][][] privateKey, byte[][][] publicKey) GenerateKeys()
    {
        int bits = _hashSize * 8; // liczba bitów w hashu
        var privateKey = new byte[bits][][];
        var publicKey = new byte[bits][][];

        using var rng = RandomNumberGenerator.Create();

        for (int i = 0; i < bits; i++)
        {
            privateKey[i] = new byte[2][];
            publicKey[i] = new byte[2][];

            for (int j = 0; j < 2; j++)
            {
                // Generuj losową wartość dla klucza prywatnego
                privateKey[i][j] = new byte[_hashSize];
                rng.GetBytes(privateKey[i][j]);

                // Klucz publiczny to hash klucza prywatnego
                publicKey[i][j] = ComputeHash(privateKey[i][j]);
            }
        }

        return (privateKey, publicKey);
    }

    /// <summary>
    /// Generuje parę kluczy z ziarnem (seed, publiczny) - OPTYMALIZOWANA WERSJA
    /// Zamiast przechowywać pełny klucz prywatny, przechowujemy tylko ziarno (32 bajty)
    /// Klucz prywatny można odtworzyć deterministycznie z ziarna gdy jest potrzebny
    /// </summary>
    public (byte[] seed, byte[][][] publicKey) GenerateKeysWithSeed()
    {
        // Wygeneruj losowe ziarno (32 bajty)
        byte[] seed = new byte[32];
        using var rng = RandomNumberGenerator.Create();
        rng.GetBytes(seed);

        // Wygeneruj klucz publiczny z klucza prywatnego odtworzonego z ziarna
        var privateKey = RegeneratePrivateKeyFromSeed(seed);

        int bits = _hashSize * 8;
        var publicKey = new byte[bits][][];

        for (int i = 0; i < bits; i++)
        {
            publicKey[i] = new byte[2][];
            for (int j = 0; j < 2; j++)
            {
                // Klucz publiczny to hash klucza prywatnego
                publicKey[i][j] = ComputeHash(privateKey[i][j]);
            }
        }

        return (seed, publicKey);
    }

    /// <summary>
    /// Odtwarza klucz prywatny deterministycznie z ziarna
    /// </summary>
    public byte[][][] RegeneratePrivateKeyFromSeed(byte[] seed)
    {
        int bits = _hashSize * 8;
        var privateKey = new byte[bits][][];

        var rng = new DeterministicRng(seed);

        for (int i = 0; i < bits; i++)
        {
            privateKey[i] = new byte[2][];
            for (int j = 0; j < 2; j++)
            {
                privateKey[i][j] = new byte[_hashSize];
                rng.GetBytes(privateKey[i][j]);
            }
        }

        return privateKey;
    }

    /// <summary>
    /// Podpisuje wiadomość przy użyciu klucza prywatnego - WERSJA LEGACY
    /// </summary>
    public byte[][] Sign(string message, byte[][][] privateKey)
    {
        // Oblicz hash wiadomości
        byte[] messageHash = ComputeHash(Encoding.UTF8.GetBytes(message));
        int bits = _hashSize * 8;
        var signature = new byte[bits][];

        // Dla każdego bitu w hashu, wybierz odpowiednią wartość z klucza prywatnego
        for (int i = 0; i < bits; i++)
        {
            int byteIndex = i / 8;
            int bitIndex = i % 8;
            int bit = (messageHash[byteIndex] >> (7 - bitIndex)) & 1;

            signature[i] = privateKey[i][bit];
        }

        return signature;
    }

    /// <summary>
    /// Podpisuje wiadomość przy użyciu ziarna - OPTYMALIZOWANA WERSJA
    /// Odtwarza klucz prywatny z ziarna w locie i podpisuje wiadomość
    /// </summary>
    public byte[][] SignWithSeed(string message, byte[] seed)
    {
        // Odtwórz klucz prywatny z ziarna
        var privateKey = RegeneratePrivateKeyFromSeed(seed);

        // Podpisz używając odtworzonego klucza
        return Sign(message, privateKey);
    }

    /// <summary>
    /// Weryfikuje podpis wiadomości przy użyciu klucza publicznego
    /// </summary>
    public bool Verify(string message, byte[][] signature, byte[][][] publicKey)
    {
        // Oblicz hash wiadomości
        byte[] messageHash = ComputeHash(Encoding.UTF8.GetBytes(message));
        int bits = _hashSize * 8;

        if (signature.Length != bits)
            return false;

        // Dla każdego bitu w hashu, sprawdź czy hash podpisu pasuje do klucza publicznego
        for (int i = 0; i < bits; i++)
        {
            int byteIndex = i / 8;
            int bitIndex = i % 8;
            int bit = (messageHash[byteIndex] >> (7 - bitIndex)) & 1;

            byte[] signatureHash = ComputeHash(signature[i]);

            // Porównaj hash podpisu z odpowiednim kluczem publicznym
            if (!signatureHash.SequenceEqual(publicKey[i][bit]))
                return false;
        }

        return true;
    }

    /// <summary>
    /// Oblicza hash dla danych
    /// </summary>
    private byte[] ComputeHash(byte[] data)
    {
        using HashAlgorithm hash = _hashAlgorithm.Name switch
        {
            "SHA256" => SHA256.Create(),
            "SHA384" => SHA384.Create(),
            "SHA512" => SHA512.Create(),
            _ => throw new ArgumentException("Nieobsługiwany algorytm hash")
        };

        return hash.ComputeHash(data);
    }

    /// <summary>
    /// Oblicza rozmiar klucza prywatnego w bajtach - WERSJA LEGACY
    /// </summary>
    public int GetPrivateKeySize()
    {
        int bits = _hashSize * 8;
        return bits * 2 * _hashSize; // bits par × 2 wartości × rozmiar hashu
    }

    /// <summary>
    /// Oblicza rozmiar ziarna klucza prywatnego w bajtach - OPTYMALIZOWANA WERSJA
    /// </summary>
    public int GetPrivateKeySeedSize()
    {
        return 32; // Ziarno zawsze ma 32 bajty
    }

    /// <summary>
    /// Oblicza rozmiar klucza publicznego w bajtach
    /// </summary>
    public int GetPublicKeySize()
    {
        int bits = _hashSize * 8;
        return bits * 2 * _hashSize; // bits par × 2 wartości × rozmiar hashu
    }

    /// <summary>
    /// Oblicza rozmiar podpisu w bajtach
    /// </summary>
    public int GetSignatureSize()
    {
        int bits = _hashSize * 8;
        return bits * _hashSize; // bits × rozmiar hashu
    }
}

/// <summary>
/// Klasa przechowująca wyniki pomiarów dla jednego algorytmu
/// </summary>
class BenchmarkResult
{
    public string AlgorithmName { get; set; } = string.Empty;
    public bool IsValidSignature { get; set; }
    public bool IsInvalidRejected { get; set; }

    // Wersja LEGACY (pełny klucz prywatny)
    public double KeyGenTime { get; set; }
    public double SignTime { get; set; }
    public double VerifyTime { get; set; }
    public int PrivateKeySize { get; set; }
    public int PublicKeySize { get; set; }
    public int SignatureSize { get; set; }

    // Wersja OPTYMALIZOWANA (ziarno)
    public double KeyGenWithSeedTime { get; set; }
    public double SignWithSeedTime { get; set; }
    public int PrivateKeySeedSize { get; set; }
}

class Program
{
    static void Main(string[] args)
    {
        Console.WriteLine("  PODPIS JEDNORAZOWY LAMPORTA (Lamport One-Time Signature)");
        Console.WriteLine();

        // Algorytmy do przetestowania
        var algorithms = new[]
        {
            HashAlgorithmName.SHA256,
            HashAlgorithmName.SHA384,
            HashAlgorithmName.SHA512
        };

        var results = new List<BenchmarkResult>();
        string message = "Kryptografia post-kwantowa 2026";
        int iterations = 100;

        // Zbieranie wyników dla wszystkich algorytmów
        foreach (var algorithm in algorithms)
        {
            Console.WriteLine($"Przetwarzanie {algorithm.Name}...");

            var lamport = new LamportSignature(algorithm);
            var result = new BenchmarkResult { AlgorithmName = algorithm.Name ?? "Unknown" };

            // a) Demonstracja działania - testujemy obie wersje

            // Wersja LEGACY
            var (privateKey, publicKey) = lamport.GenerateKeys();
            var signature = lamport.Sign(message, privateKey);
            result.IsValidSignature = lamport.Verify(message, signature, publicKey);
            result.IsInvalidRejected = !lamport.Verify(message + "!", signature, publicKey);

            // Wersja z ziarnem - sprawdzenie czy działa tak samo
            var (seed, publicKeySeed) = lamport.GenerateKeysWithSeed();
            var signatureSeed = lamport.SignWithSeed(message, seed);
            bool seedValid = lamport.Verify(message, signatureSeed, publicKeySeed);
            bool seedInvalidRejected = !lamport.Verify(message + "!", signatureSeed, publicKeySeed);

            if (seedValid != result.IsValidSignature || seedInvalidRejected != result.IsInvalidRejected)
            {
                Console.WriteLine($"OSTRZEŻENIE: Wersja z ziarnem daje inne wyniki dla {algorithm.Name}!");
            }

            // b) Pomiar czasu
            var sw = Stopwatch.StartNew();

            // WERSJA LEGACY - Generowanie kluczy
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.GenerateKeys();
            }
            sw.Stop();
            result.KeyGenTime = sw.Elapsed.TotalMilliseconds / iterations;

            // WERSJA LEGACY - Podpisywanie
            var (privKey, pubKey) = lamport.GenerateKeys();
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.Sign(message, privKey);
            }
            sw.Stop();
            result.SignTime = sw.Elapsed.TotalMilliseconds / iterations;

            // WERSJA LEGACY - Weryfikacja
            var sig = lamport.Sign(message, privKey);
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.Verify(message, sig, pubKey);
            }
            sw.Stop();
            result.VerifyTime = sw.Elapsed.TotalMilliseconds / iterations;

            // WERSJA Z ZIARNEM - Generowanie kluczy
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.GenerateKeysWithSeed();
            }
            sw.Stop();
            result.KeyGenWithSeedTime = sw.Elapsed.TotalMilliseconds / iterations;

            // WERSJA Z ZIARNEM - Podpisywanie
            var (seedKey, pubKeySeed2) = lamport.GenerateKeysWithSeed();
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.SignWithSeed(message, seedKey);
            }
            sw.Stop();
            result.SignWithSeedTime = sw.Elapsed.TotalMilliseconds / iterations;

            // c) Rozmiary
            result.PrivateKeySize = lamport.GetPrivateKeySize();
            result.PublicKeySize = lamport.GetPublicKeySize();
            result.SignatureSize = lamport.GetSignatureSize();
            result.PrivateKeySeedSize = lamport.GetPrivateKeySeedSize();

            results.Add(result);
        }

        // Wyświetlenie podsumowania
        DisplaySummary(results, message, iterations);
    }

    static void DisplaySummary(List<BenchmarkResult> results, string message, int iterations)
    {
        Console.WriteLine();
        Console.WriteLine(new string('=', 80));
        Console.WriteLine("  PODSUMOWANIE WYNIKÓW");
        Console.WriteLine(new string('=', 80));
        Console.WriteLine();

        // a) Demonstracja działania
        Console.WriteLine("a) DEMONSTRACJA DZIAŁANIA:");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"Wiadomość: \"{message}\"");
        Console.WriteLine();

        Console.WriteLine($"{"Algorytm",-15} {"Weryfikacja",-20} {"Odrzucenie fałszu",-20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            string validStatus = result.IsValidSignature ? "POPRAWNY" : "NIEPOPRAWNY";
            string invalidStatus = result.IsInvalidRejected ? "ODRZUCONY" : "BŁĄD";
            Console.WriteLine($"{result.AlgorithmName,-15} {validStatus,-20} {invalidStatus,-20}");
        }

        // b) Pomiar wydajności
        Console.WriteLine();
        Console.WriteLine("b) POMIAR WYDAJNOŚCI:");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"Liczba iteracji: {iterations}");
        Console.WriteLine();

        Console.WriteLine("WERSJA LEGACY (pełny klucz prywatny):");
        Console.WriteLine($"{"Algorytm",-15} {"Generowanie [ms]",20} {"Podpisywanie [ms]",20} {"Weryfikacja [ms]",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            Console.WriteLine($"{result.AlgorithmName,-15} {result.KeyGenTime,20:F4} {result.SignTime,20:F4} {result.VerifyTime,20:F4}");
        }

        Console.WriteLine();
        Console.WriteLine("WERSJA OPTYMALIZOWANA (ziarno):");
        Console.WriteLine($"{"Algorytm",-15} {"Generowanie [ms]",20} {"Podpisywanie [ms]",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            Console.WriteLine($"{result.AlgorithmName,-15} {result.KeyGenWithSeedTime,20:F4} {result.SignWithSeedTime,20:F4}");
        }

        // Porównanie względne
        Console.WriteLine();
        Console.WriteLine("Porównanie względne (SHA256 = 1.00x):");
        Console.WriteLine(new string('-', 80));
        var baseline = results[0];
        Console.WriteLine($"{"Algorytm",-15} {"Generowanie",20} {"Podpisywanie",20} {"Weryfikacja",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            double keyGenRatio = result.KeyGenTime / baseline.KeyGenTime;
            double signRatio = result.SignTime / baseline.SignTime;
            double verifyRatio = result.VerifyTime / baseline.VerifyTime;
            Console.WriteLine($"{result.AlgorithmName,-15} {keyGenRatio,19:F2}x {signRatio,19:F2}x {verifyRatio,19:F2}x");
        }

        // c) Rozmiary
        Console.WriteLine();
        Console.WriteLine("c) ROZMIARY:");
        Console.WriteLine(new string('-', 80));

        Console.WriteLine("WERSJA LEGACY (pełny klucz prywatny):");
        Console.WriteLine($"{"Algorytm",-15} {"Klucz prywatny",25} {"Klucz publiczny",25} {"Podpis",25}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            string privKey = $"{result.PrivateKeySize,7} B ({result.PrivateKeySize / 1024.0,6:F2} KB)";
            string pubKey = $"{result.PublicKeySize,7} B ({result.PublicKeySize / 1024.0,6:F2} KB)";
            string sig = $"{result.SignatureSize,7} B ({result.SignatureSize / 1024.0,6:F2} KB)";
            Console.WriteLine($"{result.AlgorithmName,-15} {privKey,-25} {pubKey,-25} {sig,-25}");
        }

        Console.WriteLine();
        Console.WriteLine("WERSJA OPTYMALIZOWANA (ziarno):");
        Console.WriteLine($"{"Algorytm",-15} {"Klucz (ziarno)",25} {"Klucz publiczny",25} {"Podpis",25}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            string seedKey = $"{result.PrivateKeySeedSize,7} B ({result.PrivateKeySeedSize / 1024.0,6:F2} KB)";
            string pubKey = $"{result.PublicKeySize,7} B ({result.PublicKeySize / 1024.0,6:F2} KB)";
            string sig = $"{result.SignatureSize,7} B ({result.SignatureSize / 1024.0,6:F2} KB)";
            Console.WriteLine($"{result.AlgorithmName,-15} {seedKey,-25} {pubKey,-25} {sig,-25}");
        }

        // Porównanie rozmiarów
        Console.WriteLine();
        Console.WriteLine("Porównanie rozmiarów (SHA256 = 1.00x):");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Algorytm",-15} {"Klucz prywatny",20} {"Klucz publiczny",20} {"Podpis",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            double privKeyRatio = (double)result.PrivateKeySize / baseline.PrivateKeySize;
            double pubKeyRatio = (double)result.PublicKeySize / baseline.PublicKeySize;
            double sigRatio = (double)result.SignatureSize / baseline.SignatureSize;
            Console.WriteLine($"{result.AlgorithmName,-15} {privKeyRatio,19:F2}x {pubKeyRatio,19:F2}x {sigRatio,19:F2}x");
        }

        // PORÓWNANIE: PEŁNY KLUCZ vs ZIARNO
        Console.WriteLine();
        Console.WriteLine(new string('=', 80));
        Console.WriteLine("  PORÓWNANIE: PEŁNY KLUCZ PRYWATNY vs ZIARNO");
        Console.WriteLine(new string('=', 80));
        Console.WriteLine();
        Console.WriteLine($"{"Algorytm",-15} {"Pełny klucz",20} {"Ziarno",20} {"Redukcja",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            double reductionPercent = (1.0 - (double)result.PrivateKeySeedSize / result.PrivateKeySize) * 100;
            string fullKey = $"{result.PrivateKeySize / 1024.0,6:F2} KB";
            string seedKey = $"{result.PrivateKeySeedSize,6} B";
            string reduction = $"{reductionPercent,6:F2}%";
            Console.WriteLine($"{result.AlgorithmName,-15} {fullKey,20} {seedKey,20} {reduction,20}");
        }

        Console.WriteLine();
        Console.WriteLine("WYDAJNOŚĆ: Generowanie kluczy (Legacy vs Ziarno):");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Algorytm",-15} {"Legacy [ms]",20} {"Ziarno [ms]",20} {"Zmiana",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            double changePercent = ((result.KeyGenWithSeedTime / result.KeyGenTime) - 1.0) * 100;
            string changeStr = changePercent >= 0 ? $"+{changePercent:F2}%" : $"{changePercent:F2}%";
            Console.WriteLine($"{result.AlgorithmName,-15} {result.KeyGenTime,20:F4} {result.KeyGenWithSeedTime,20:F4} {changeStr,20}");
        }

        Console.WriteLine();
        Console.WriteLine("WYDAJNOŚĆ: Podpisywanie (Legacy vs Ziarno):");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"{"Algorytm",-15} {"Legacy [ms]",20} {"Ziarno [ms]",20} {"Zmiana",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            double changePercent = ((result.SignWithSeedTime / result.SignTime) - 1.0) * 100;
            string changeStr = changePercent >= 0 ? $"+{changePercent:F2}%" : $"{changePercent:F2}%";
            Console.WriteLine($"{result.AlgorithmName,-15} {result.SignTime,20:F4} {result.SignWithSeedTime,20:F4} {changeStr,20}");
        }

        Console.WriteLine();
        Console.WriteLine(new string('=', 80));
    }
}

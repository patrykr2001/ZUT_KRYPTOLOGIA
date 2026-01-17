using System.Diagnostics;
using System.Security.Cryptography;
using System.Text;

namespace Lab08;

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
    /// Generuje parę kluczy (prywatny, publiczny)
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
    /// Podpisuje wiadomość przy użyciu klucza prywatnego
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
    /// Oblicza rozmiar klucza prywatnego w bajtach
    /// </summary>
    public int GetPrivateKeySize()
    {
        int bits = _hashSize * 8;
        return bits * 2 * _hashSize; // bits par × 2 wartości × rozmiar hashu
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
    public double KeyGenTime { get; set; }
    public double SignTime { get; set; }
    public double VerifyTime { get; set; }
    public int PrivateKeySize { get; set; }
    public int PublicKeySize { get; set; }
    public int SignatureSize { get; set; }
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

            // a) Demonstracja działania
            var (privateKey, publicKey) = lamport.GenerateKeys();
            var signature = lamport.Sign(message, privateKey);
            result.IsValidSignature = lamport.Verify(message, signature, publicKey);
            result.IsInvalidRejected = !lamport.Verify(message + "!", signature, publicKey);

            // b) Pomiar czasu
            var sw = Stopwatch.StartNew();

            // Generowanie kluczy
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.GenerateKeys();
            }
            sw.Stop();
            result.KeyGenTime = sw.Elapsed.TotalMilliseconds / iterations;

            // Podpisywanie
            var (privKey, pubKey) = lamport.GenerateKeys();
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.Sign(message, privKey);
            }
            sw.Stop();
            result.SignTime = sw.Elapsed.TotalMilliseconds / iterations;

            // Weryfikacja
            var sig = lamport.Sign(message, privKey);
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.Verify(message, sig, pubKey);
            }
            sw.Stop();
            result.VerifyTime = sw.Elapsed.TotalMilliseconds / iterations;

            // c) Rozmiary
            result.PrivateKeySize = lamport.GetPrivateKeySize();
            result.PublicKeySize = lamport.GetPublicKeySize();
            result.SignatureSize = lamport.GetSignatureSize();

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
            string validStatus = result.IsValidSignature ? "✓ POPRAWNY" : "✗ NIEPOPRAWNY";
            string invalidStatus = result.IsInvalidRejected ? "✓ ODRZUCONY" : "✗ BŁĄD";
            Console.WriteLine($"{result.AlgorithmName,-15} {validStatus,-20} {invalidStatus,-20}");
        }

        // b) Pomiar wydajności
        Console.WriteLine();
        Console.WriteLine("b) POMIAR WYDAJNOŚCI:");
        Console.WriteLine(new string('-', 80));
        Console.WriteLine($"Liczba iteracji: {iterations}");
        Console.WriteLine();

        Console.WriteLine($"{"Algorytm",-15} {"Generowanie [ms]",20} {"Podpisywanie [ms]",20} {"Weryfikacja [ms]",20}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            Console.WriteLine($"{result.AlgorithmName,-15} {result.KeyGenTime,20:F4} {result.SignTime,20:F4} {result.VerifyTime,20:F4}");
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

        Console.WriteLine($"{"Algorytm",-15} {"Klucz prywatny",25} {"Klucz publiczny",25} {"Podpis",25}");
        Console.WriteLine(new string('-', 80));
        foreach (var result in results)
        {
            string privKey = $"{result.PrivateKeySize,7} B ({result.PrivateKeySize / 1024.0,6:F2} KB)";
            string pubKey = $"{result.PublicKeySize,7} B ({result.PublicKeySize / 1024.0,6:F2} KB)";
            string sig = $"{result.SignatureSize,7} B ({result.SignatureSize / 1024.0,6:F2} KB)";
            Console.WriteLine($"{result.AlgorithmName,-15} {privKey,-25} {pubKey,-25} {sig,-25}");
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

        Console.WriteLine();
        Console.WriteLine(new string('=', 80));
    }
}

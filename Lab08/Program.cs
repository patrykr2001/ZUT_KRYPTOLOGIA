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

class Program
{
    static void Main(string[] args)
    {
        Console.WriteLine("  PODPIS JEDNORAZOWY LAMPORTA (Lamport One-Time Signature)");

        // Algorytmy do przetestowania
        var algorithms = new[]
        {
            HashAlgorithmName.SHA256,
            HashAlgorithmName.SHA384,
            HashAlgorithmName.SHA512
        };

        foreach (var algorithm in algorithms)
        {
            Console.WriteLine($"  Algorytm: {algorithm.Name}");

            var lamport = new LamportSignature(algorithm);

            // a) Demonstracja działania
            Console.WriteLine("a) DEMONSTRACJA DZIAŁANIA:");
            Console.WriteLine(new string('-', 65));

            string message = "Kryptografia post-kwantowa 2026";
            Console.WriteLine($"Wiadomość: \"{message}\"\n");

            Console.Write("Generowanie kluczy... ");
            var (privateKey, publicKey) = lamport.GenerateKeys();
            Console.WriteLine("Gotowe");

            Console.Write("Podpisywanie wiadomości... ");
            var signature = lamport.Sign(message, privateKey);
            Console.WriteLine("Gotowe");

            Console.Write("Weryfikacja podpisu... ");
            bool isValid = lamport.Verify(message, signature, publicKey);
            Console.WriteLine($"{(isValid ? "POPRAWNY" : "NIEPOPRAWNY")}");

            // Test z niepoprawną wiadomością
            Console.Write("Weryfikacja dla zmienionej wiadomości... ");
            bool isInvalid = lamport.Verify(message + "!", signature, publicKey);
            Console.WriteLine($"{(!isInvalid ? "ODRZUCONY (jak powinno być)" : "BŁĄD!")}");

            // b) Pomiar czasu
            Console.WriteLine("\nb) POMIAR WYDAJNOŚCI:");
            Console.WriteLine(new string('-', 65));

            int iterations = 100;
            var sw = Stopwatch.StartNew();

            // Generowanie kluczy
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.GenerateKeys();
            }
            sw.Stop();
            double keyGenTime = sw.Elapsed.TotalMilliseconds / iterations;

            // Podpisywanie
            var (privKey, pubKey) = lamport.GenerateKeys();
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.Sign(message, privKey);
            }
            sw.Stop();
            double signTime = sw.Elapsed.TotalMilliseconds / iterations;

            // Weryfikacja
            var sig = lamport.Sign(message, privKey);
            sw.Restart();
            for (int i = 0; i < iterations; i++)
            {
                lamport.Verify(message, sig, pubKey);
            }
            sw.Stop();
            double verifyTime = sw.Elapsed.TotalMilliseconds / iterations;

            Console.WriteLine($"Generowanie kluczy: {keyGenTime,10:F4} ms");
            Console.WriteLine($"Podpisywanie:       {signTime,10:F4} ms");
            Console.WriteLine($"Weryfikacja:        {verifyTime,10:F4} ms");

            // c) Rozmiar kluczy i podpisu
            Console.WriteLine("\nc) ROZMIARY:");
            Console.WriteLine(new string('-', 65));

            int privateKeySize = lamport.GetPrivateKeySize();
            int publicKeySize = lamport.GetPublicKeySize();
            int signatureSize = lamport.GetSignatureSize();

            Console.WriteLine($"Klucz prywatny:  {privateKeySize,7} B  ({privateKeySize / 1024.0,7:F2} KB)");
            Console.WriteLine($"Klucz publiczny: {publicKeySize,7} B  ({publicKeySize / 1024.0,7:F2} KB)");
            Console.WriteLine($"Podpis:          {signatureSize,7} B  ({signatureSize / 1024.0,7:F2} KB)");

            Console.WriteLine();
        }
    }
}

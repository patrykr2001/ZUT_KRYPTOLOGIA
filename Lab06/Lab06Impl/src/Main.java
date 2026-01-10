import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.spec.ECPoint;
import iaik.security.ec.common.ECParameterSpec;
import iaik.security.ec.common.ECStandardizedParameterFactory;
import iaik.security.ec.common.SecurityStrength;

public class Main {
    public static void main(String[] args) {
        System.out.println("---- Demo implementacji ECDSA: Tomasz Hyla 2022");
        System.out.println();

        // ZADANIE 1 - Podstawowa implementacja ECDSA
        demonstrateBasicECDSA();

        System.out.println("\n" + "=".repeat(80));
        System.out.println("ZADANIE 2 - Atak na ECDSA przy ponownym użyciu k");
        System.out.println("=".repeat(80) + "\n");

        // ZADANIE 2 - Atak przy ponownym użyciu k
        demonstrateNonceReuseAttack();
    }

    /**
     * ZADANIE 1: Podstawowa demonstracja ECDSA
     */
    private static void demonstrateBasicECDSA() {
        System.out.println("ZADANIE 1 - Podstawowa implementacja ECDSA");
        System.out.println("-".repeat(80));
        //---Parametry systemowe
        //-krzywa eliptyczna ustandaryzowana
        ECParameterSpec ec_params =
                ECStandardizedParameterFactory.getParametersByName("secp521r1");
        iaik.security.ec.common.EllipticCurve ec = ec_params.getCurve(); //tej używamy dalej
        iaik.security.ec.math.curve.EllipticCurve ec2 = ec.getIAIKCurve(); //klasa EC w innej bibliotece...
        System.out.println(ec2.toString());
        BigInteger n = ec2.getOrder();
        int size = ec2.getField().getFieldSize();
        System.out.println("Rozmiar w bitach: " + size + " liczba elementów (n)= " + n);
//-generator liczb losowych
        final SecureRandom random =
                SecurityStrength.getSecureRandom(SecurityStrength.getSecurityStrength(size));
//---Generowanie kluczy
//prywatny
        BigInteger dA = new BigInteger(size - 1, random);
//publiczny
        ECPoint QA = ec.multiplyGenerator(dA); // Q_A=d_A*G
//---Podpisywanie
//1-2.
        BigInteger z = BigInteger.ZERO;
        try {
            String m = "Kryptologia 2024";
            MessageDigest sha = MessageDigest.getInstance("SHA-512");
            byte[] messageDigest = sha.digest(m.getBytes());
            z = new BigInteger(1, messageDigest);
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
//3.
        BigInteger r = BigInteger.ZERO;
        BigInteger s = BigInteger.ZERO;
        do
        {
            BigInteger k = new BigInteger(size - 1, random);
//4.
            var kG = ec.multiplyGenerator(k);
//5.
            r = kG.getAffineX().mod(n);
            System.out.println(r.toString());
            s = k.modInverse(n).multiply(z.add(r.multiply(dA))).mod(n);
        }
        while (r.equals(BigInteger.ZERO) || s.equals(BigInteger.ZERO));
// podpis to para (r,s)
//Weryfikacja
//2.
        BigInteger z2 = BigInteger.ZERO;
        try {
            String m = "Kryptologia 2022";
            MessageDigest sha = MessageDigest.getInstance("SHA-512");
            byte[] messageDigest = sha.digest(m.getBytes());
            z2 = new BigInteger(1, messageDigest);
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }
//4.
        BigInteger s1 = s.modInverse(n);
        BigInteger u1 = z2.multiply(s1).mod(n);
        BigInteger u2 = r.multiply(s1).mod(n);
        ECPoint tmp1 = ec.multiplyGenerator(u1);
        ECPoint tmp2 = ec.multiplyPoint(QA, u2);
        ECPoint C = ec.addPoint(tmp1, tmp2);
        if (C.getAffineX().equals(BigInteger.ZERO) == false ||
                C.getAffineX().mod(n).equals(r))
        {
            System.out.println("Podpis poprawny");
        }
        else { System.out.println("Podpis niepoprawny");
        }
    }

    /**
     * ZADANIE 2: Demonstracja ataku na ECDSA przy ponownym użyciu tej samej wartości k
     *
     * Atak polega na:
     * 1. Uzyskaniu dwóch podpisów (r1, s1) i (r2, s2) dla różnych wiadomości
     * 2. Oba podpisy używają tej samej wartości k, więc r1 = r2
     * 3. Z równań ECDSA: s = k^(-1)(z + r*dA) mod n można wyprowadzić:
     *    k = (z1 - z2) * (s1 - s2)^(-1) mod n
     * 4. Następnie odzyskać klucz prywatny:
     *    dA = (s*k - z) * r^(-1) mod n
     */
    private static void demonstrateNonceReuseAttack() {
        System.out.println("Scenariusz ataku:");
        System.out.println("- Atakujący przechwytuje dwa podpisy dla różnych wiadomości");
        System.out.println("- Odkrywa, że oba podpisy używają tej samej wartości k (nonce reuse)");
        System.out.println("- Wykorzystuje matematyczne właściwości ECDSA do odzyskania klucza prywatnego");
        System.out.println();

        // ---Parametry systemowe (te same co w zadaniu 1)
        ECParameterSpec ec_params =
                ECStandardizedParameterFactory.getParametersByName("secp521r1");
        iaik.security.ec.common.EllipticCurve ec = ec_params.getCurve();
        iaik.security.ec.math.curve.EllipticCurve ec2 = ec.getIAIKCurve();
        BigInteger n = ec2.getOrder();
        int size = ec2.getField().getFieldSize();

        System.out.println("Parametry krzywej: secp521r1");
        System.out.println("Rozmiar: " + size + " bitów");
        System.out.println();

        // Generator liczb losowych
        final SecureRandom random =
                SecurityStrength.getSecureRandom(SecurityStrength.getSecurityStrength(size));

        // ---Generowanie kluczy ofiary
        System.out.println("1. Generowanie kluczy ofiary");
        System.out.println("-".repeat(80));
        BigInteger dA = new BigInteger(size - 1, random);
        ECPoint QA = ec.multiplyGenerator(dA);

        System.out.println("Klucz prywatny dA (ofiary - normalnie nieznany atakującemu):");
        System.out.println("  dA = " + dA.toString().substring(0, 60) + "...");
        System.out.println("Klucz publiczny QA (znany publicznie):");
        System.out.println("  QA.x = " + QA.getAffineX().toString().substring(0, 60) + "...");
        System.out.println();

        // ---Tworzenie dwóch podpisów z TĄ SAMĄ wartością k
        System.out.println("2. Ofiara tworzy dwa podpisy używając TEJ SAMEJ wartości k (błąd!)");
        System.out.println("-".repeat(80));

        // Generujemy k RAZ i używamy go dwukrotnie (symulacja błędu implementacji)
        BigInteger k = new BigInteger(size - 1, random);
        System.out.println("Wartość k (nonce - powinna być losowa dla każdego podpisu):");
        System.out.println("  k = " + k.toString().substring(0, 60) + "...");
        System.out.println();

        // PIERWSZY PODPIS - dla wiadomości "Kryptologia 2024"
        String m1 = "Kryptologia 2024";
        BigInteger z1 = BigInteger.ZERO;
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-512");
            byte[] messageDigest = sha.digest(m1.getBytes());
            z1 = new BigInteger(1, messageDigest);
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }

        var kG = ec.multiplyGenerator(k);
        BigInteger r1 = kG.getAffineX().mod(n);
        BigInteger s1 = k.modInverse(n).multiply(z1.add(r1.multiply(dA))).mod(n);

        System.out.println("Pierwszy podpis dla wiadomości: \"" + m1 + "\"");
        System.out.println("  z1 (hash) = " + z1.toString().substring(0, 60) + "...");
        System.out.println("  r1 = " + r1.toString().substring(0, 60) + "...");
        System.out.println("  s1 = " + s1.toString().substring(0, 60) + "...");
        System.out.println();

        // DRUGI PODPIS - dla wiadomości "Kryptologia 2022" z TYM SAMYM k
        String m2 = "Kryptologia 2022";
        BigInteger z2 = BigInteger.ZERO;
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-512");
            byte[] messageDigest = sha.digest(m2.getBytes());
            z2 = new BigInteger(1, messageDigest);
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }

        // Używamy tego samego k, więc r2 będzie takie samo jak r1
        BigInteger r2 = r1; // bo k*G da ten sam punkt
        BigInteger s2 = k.modInverse(n).multiply(z2.add(r2.multiply(dA))).mod(n);

        System.out.println("Drugi podpis dla wiadomości: \"" + m2 + "\"");
        System.out.println("  z2 (hash) = " + z2.toString().substring(0, 60) + "...");
        System.out.println("  r2 = " + r2.toString().substring(0, 60) + "...");
        System.out.println("  s2 = " + s2.toString().substring(0, 60) + "...");
        System.out.println();

        System.out.println("UWAGA: r1 == r2 = " + r1.equals(r2) + " (to wskazuje na ponowne użycie k!)");
        System.out.println();

        // ---ATAK: Odzyskiwanie k
        System.out.println("3. ATAK - Odzyskiwanie wartości k");
        System.out.println("-".repeat(80));
        System.out.println("Z równań ECDSA:");
        System.out.println("  s1 = k^(-1) * (z1 + r1 * dA) mod n");
        System.out.println("  s2 = k^(-1) * (z2 + r2 * dA) mod n");
        System.out.println();
        System.out.println("Mnożąc obie strony przez k:");
        System.out.println("  s1 * k = z1 + r1 * dA mod n");
        System.out.println("  s2 * k = z2 + r2 * dA mod n");
        System.out.println();
        System.out.println("Odejmując drugie równanie od pierwszego (r1 = r2, więc r*dA się skraca):");
        System.out.println("  (s1 - s2) * k = z1 - z2 mod n");
        System.out.println();
        System.out.println("Zatem:");
        System.out.println("  k = (z1 - z2) * (s1 - s2)^(-1) mod n");
        System.out.println();

        BigInteger s_diff = s1.subtract(s2).mod(n);
        BigInteger z_diff = z1.subtract(z2).mod(n);
        BigInteger k_recovered = z_diff.multiply(s_diff.modInverse(n)).mod(n);

        System.out.println("Obliczenia:");
        System.out.println("  (s1 - s2) mod n = " + s_diff.toString().substring(0, 60) + "...");
        System.out.println("  (z1 - z2) mod n = " + z_diff.toString().substring(0, 60) + "...");
        System.out.println();
        System.out.println("Odzyskane k:");
        System.out.println("  k_recovered = " + k_recovered.toString().substring(0, 60) + "...");
        System.out.println();
        System.out.println("Weryfikacja: k == k_recovered? " + k.equals(k_recovered));
        System.out.println();

        // ---ATAK: Odzyskiwanie klucza prywatnego dA
        System.out.println("4. ATAK - Odzyskiwanie klucza prywatnego dA");
        System.out.println("-".repeat(80));
        System.out.println("Z równania ECDSA:");
        System.out.println("  s = k^(-1) * (z + r * dA) mod n");
        System.out.println();
        System.out.println("Mnożąc obie strony przez k:");
        System.out.println("  s * k = z + r * dA mod n");
        System.out.println();
        System.out.println("Przekształcając:");
        System.out.println("  r * dA = s * k - z mod n");
        System.out.println("  dA = (s * k - z) * r^(-1) mod n");
        System.out.println();

        // Używamy pierwszego podpisu do odzyskania dA
        BigInteger dA_recovered = (s1.multiply(k_recovered).subtract(z1)).multiply(r1.modInverse(n)).mod(n);

        System.out.println("Odzyskany klucz prywatny:");
        System.out.println("  dA_recovered = " + dA_recovered.toString().substring(0, 60) + "...");
        System.out.println();
        System.out.println("Weryfikacja: dA == dA_recovered? " + dA.equals(dA_recovered));
        System.out.println();

        // ---Weryfikacja - sprawdzenie czy odzyskany klucz jest poprawny
        System.out.println("5. WERYFIKACJA - Sprawdzenie poprawności odzyskanego klucza");
        System.out.println("-".repeat(80));

        // Obliczamy klucz publiczny z odzyskanego klucza prywatnego
        ECPoint QA_recovered = ec.multiplyGenerator(dA_recovered);

        System.out.println("Oryginalny klucz publiczny QA:");
        System.out.println("  QA.x = " + QA.getAffineX().toString().substring(0, 60) + "...");
        System.out.println("  QA.y = " + QA.getAffineY().toString().substring(0, 60) + "...");
        System.out.println();

        System.out.println("Klucz publiczny obliczony z odzyskanego dA:");
        System.out.println("  QA_recovered.x = " + QA_recovered.getAffineX().toString().substring(0, 60) + "...");
        System.out.println("  QA_recovered.y = " + QA_recovered.getAffineY().toString().substring(0, 60) + "...");
        System.out.println();

        boolean keysMatch = QA.getAffineX().equals(QA_recovered.getAffineX()) &&
                           QA.getAffineY().equals(QA_recovered.getAffineY());

        if (keysMatch) {
            System.out.println("Klucze publiczne są identyczne.");
            System.out.println("Atak zakończony sukcesem - klucz prywatny został odzyskany!");
        } else {
            System.out.println("Klucze publiczne są różne.");
        }
        System.out.println();

        // Weryfikacja przez podpisanie nowej wiadomości odzyskanym kluczem
        System.out.println("6. DODATKOWA WERYFIKACJA - Podpisanie nowej wiadomości");
        System.out.println("-".repeat(80));

        String testMessage = "Test message signed with recovered key";
        BigInteger z_test = BigInteger.ZERO;
        try {
            MessageDigest sha = MessageDigest.getInstance("SHA-512");
            byte[] messageDigest = sha.digest(testMessage.getBytes());
            z_test = new BigInteger(1, messageDigest);
        } catch (NoSuchAlgorithmException e) {
            e.printStackTrace();
        }

        // Tworzymy nowy podpis używając odzyskanego klucza
        BigInteger k_test = new BigInteger(size - 1, random);
        var kG_test = ec.multiplyGenerator(k_test);
        BigInteger r_test = kG_test.getAffineX().mod(n);
        BigInteger s_test = k_test.modInverse(n).multiply(z_test.add(r_test.multiply(dA_recovered))).mod(n);

        System.out.println("Wiadomość: \"" + testMessage + "\"");
        System.out.println("Podpis utworzony odzyskanym kluczem:");
        System.out.println("  r = " + r_test.toString().substring(0, 60) + "...");
        System.out.println("  s = " + s_test.toString().substring(0, 60) + "...");
        System.out.println();

        // Weryfikacja tego podpisu oryginalnym kluczem publicznym
        BigInteger s_inv = s_test.modInverse(n);
        BigInteger u1 = z_test.multiply(s_inv).mod(n);
        BigInteger u2 = r_test.multiply(s_inv).mod(n);
        ECPoint tmp1 = ec.multiplyGenerator(u1);
        ECPoint tmp2 = ec.multiplyPoint(QA, u2);
        ECPoint C = ec.addPoint(tmp1, tmp2);

        boolean signatureValid = !C.getAffineX().equals(BigInteger.ZERO) &&
                                C.getAffineX().mod(n).equals(r_test);

        if (signatureValid) {
            System.out.println("Podpis jest POPRAWNY przy weryfikacji oryginalnym kluczem publicznym!");
            System.out.println("To potwierdza, że odzyskany klucz prywatny jest identyczny z oryginalnym.");
        } else {
            System.out.println("Podpis jest NIEPOPRAWNY.");
        }
        System.out.println();

        // Podsumowanie
        System.out.println("=".repeat(80));
        System.out.println("PODSUMOWANIE ATAKU");
        System.out.println("=".repeat(80));
        System.out.println("Ponowne użycie tej samej wartości k (nonce) w ECDSA jest błędem krytycznym.");
        System.out.println();
        System.out.println("Skutki ataku:");
        System.out.println("  Odzyskano wartość k (nonce)");
        System.out.println("  Odzyskano klucz prywatny dA");
        System.out.println("  Atakujący może teraz podpisywać dowolne wiadomości jako ofiara");
        System.out.println();
        System.out.println("Wnioski:");
        System.out.println("  • Każdy podpis MUSI używać unikalnej, losowej wartości k");
        System.out.println("  • Generator liczb losowych musi być kryptograficznie bezpieczny");
        System.out.println("  • Nawet jedno ponowne użycie k prowadzi do całkowitego złamania bezpieczeństwa");
        System.out.println("  • Znane ataki w rzeczywistości: PlayStation 3 (2010), Android Bitcoin (2013)");
        System.out.println("=".repeat(80));
    }
}


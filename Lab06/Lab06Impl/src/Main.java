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
}


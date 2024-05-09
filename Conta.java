public class Conta {
    private int numero;
    private double saldo;

    public Conta(int numero) {
        this.numero = numero;
        this.saldo = 0.0;
    }

    public void depositar(double valor) {
        if(valor > 0) {
            saldo += valor;
        }
    }

    public void sacar(double valor) {
        if(valor > 0 && saldo >= valor) {
            saldo -= valor;
        }
    }

    public double getSaldo() {
        return saldo;
    }
}

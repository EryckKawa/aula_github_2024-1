public class Conta {
    private int numero;
    private double saldo;
    private Cliente cliente;

    public Conta(int numero, Cliente cliente) {
        this.numero = numero;
        this.saldo = 0.0;
        this.cliente = cliente;
    }

    public void depositar(double valor) {
        if (valor > 0) {
            saldo += valor;
        }
    }

    public void sacar(double valor) {
        if (valor > 0 && saldo >= valor) {
            saldo -= valor;
        }
    }

    public double getSaldo() {
        return saldo;
    }

    public Cliente getCliente() { 
        return cliente;
    }

    public void setCliente(Cliente cliente) { 
        this.cliente = cliente;
    }
    
    @Override
    public String toString() {
        return "Conta{" +
                "numero=" + numero +
                ", saldo=" + saldo +
                ", cliente=" + cliente +
                '}';
    }
}

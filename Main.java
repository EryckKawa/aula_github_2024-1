import java.util.Arrays;

public class Main {

    public static void main(String[] args) {
        Menu mainMenu =  new Menu("Menu Principal", Arrays.asList("Conta", "Cliente", "Operacoes", "Sair"));
        String selectedOption = mainMenu.getSelection();
        
        System.out.println(selectedOption + " foi selecionada");

        if (selectedOption.equals("Sair")) {
            System.out.println("Encerrando a aplicação...");
            System.exit(0);
        }

        System.out.println("Fim");
    }
}

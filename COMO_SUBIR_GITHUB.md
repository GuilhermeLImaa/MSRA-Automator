# Como Subir o MSRA Automator no GitHub 🚀

Siga este guia simples passo a passo para enviar o código do seu programa para o GitHub e gerar um link para compartilhar o executável (`MSRA Automator.exe`) com seus colegas.

---

## Passo 1: Preparar o Repositório Local

1. Abra o **Prompt de Comando (CMD)** ou **PowerShell** no Windows.
2. Navegue até a pasta do projeto:
   ```cmd
   cd "C:\Users\guilherme.lima.9\Desktop\Acesso_remoto\msra_automator"
   ```
3. Inicialize o repositório Git local:
   ```cmd
   git init
   ```
4. Adicione todos os arquivos do projeto (o arquivo `.gitignore` que criamos impedirá o envio de lixo temporário do PyInstaller):
   ```cmd
   git add .
   ```
5. Faça o seu primeiro commit:
   ```cmd
   git commit -m "Initial commit: MSRA Automator"
   ```

---

## Passo 2: Criar o Repositório no GitHub

1. Vá para o site [GitHub](https://github.com/) e faça login em sua conta.
2. Clique no botão **New** (Novo repositório) no canto superior esquerdo ou vá em `github.com/new`.
3. Preencha as configurações:
   - **Repository name:** `msra-automator`
   - **Description:** `Automação para Assistência Remota do Windows (MSRA) usando PyQt6 e pywinauto`
   - **Public/Private:** Escolha se deseja que seja público ou privado (seus colegas precisarão de acesso se for privado).
   - **Não** marque nenhuma caixa em "Initialize this repository with" (como README, gitignore ou License), pois já temos esses arquivos localmente.
4. Clique em **Create repository**.

---

## Passo 3: Vincular e Enviar o Código

O GitHub mostrará os comandos para subir um repositório existente. Execute-os no seu terminal aberto na pasta do projeto:

1. Defina o ramo principal como `main`:
   ```cmd
   git branch -M main
   ```
2. Vincule seu repositório local ao GitHub (substitua o link abaixo pelo link real fornecido na tela do GitHub):
   ```cmd
   git remote add origin https://github.com/SEU_USUARIO/msra-automator.git
   ```
3. Envie o código para o GitHub:
   ```cmd
   git push -u origin main
   ```

*(Se solicitado, faça login no GitHub pela janela do navegador que se abrirá).*

---

## Passo 4: Criar uma "Release" para Compartilhar o Executável (.exe)

O ideal no Git é **não** enviar o executável `.exe` direto no histórico de commits para não deixar o repositório pesado. A melhor prática é disponibilizá-lo na seção de **Releases** do GitHub:

1. No topo da página do seu repositório no GitHub, clique em **Create a new release** (ou clique no link **Releases** no lado direito e depois em *Draft a new release*).
2. Em **Tag version**, digite `v1.0.0` e clique em *Create new tag*.
3. Em **Release title**, digite `Versão Inicial v1.0.0`.
4. Em **Description**, descreva brevemente a versão (ex: "Primeira versão estável do MSRA Automator").
5. Na área de upload de arquivos (com o texto *"Attach binaries by dropping them here..."*), **arraste e solte** o executável `MSRA Automator.exe` gerado na pasta do seu projeto.
6. Clique no botão verde **Publish release**.

Pronto! Agora você pode compartilhar o link da Release (ex: `https://github.com/SEU_USUARIO/msra-automator/releases`) com seus colegas. Eles só precisarão clicar para baixar o `MSRA Automator.exe` e rodá-lo diretamente, sem precisar de Python ou instalação de dependências!

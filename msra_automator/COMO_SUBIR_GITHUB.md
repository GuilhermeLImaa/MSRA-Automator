# 🚀 Guia de Publicação no GitHub e Criação de Release (v2.0.0)

Este documento fornece o passo a passo completo para publicar o **MSRA Automator** no GitHub, criar a **Tag `v2.0.0`** e disponibilizar o arquivo executável (`MSRA Automator.exe`) para download na aba de **Releases**.

---

## 📋 Pré-requisitos

1. **Git** instalado no seu computador ([Download Git](https://git-scm.com/)).
2. Uma conta ativa no [GitHub](https://github.com/).
3. O executável `MSRA Automator.exe` compilado e testado na raiz do projeto.

---

## 🛠️ Passo 1: Preparar o Repositório Local

Abra o Terminal (PowerShell ou Command Prompt) na pasta do projeto:

```bash
# 1. Verifique o status dos arquivos no Git
git status

# 2. Adicione todos os arquivos de código e documentação
git add .

# 3. Realize o commit inicial da versão v2.0.0
git commit -m "Release v2.0.0 - Código fonte e documentação completa"
```

---

## 🌐 Passo 2: Criar o Repositório no GitHub

1. Acesse [GitHub.com/new](https://github.com/new).
2. Preencha o nome do repositório: `msra_automator` (ou outro de sua preferência).
3. Escolha a visibilidade: **Público** ou **Privado**.
4. **IMPORTANTE:** Não marque as opções de adicionar `README`, `.gitignore` ou `License` (já temos no projeto).
5. Clique em **Create repository**.

---

## 🔗 Passo 3: Conectar e Enviar o Código ao GitHub

Execute os comandos exibidos na tela do GitHub:

```bash
# Adicionar o endereço do seu repositório remoto
git remote add origin https://github.com/SEU_USUARIO/msra_automator.git

# Definir a branch principal como main
git branch -M main

# Enviar o código para o GitHub
git push -u origin main
```

*(Substitua `SEU_USUARIO` pelo seu username do GitHub)*

---

## 🏷️ Passo 4: Criar e Enviar a Tag de Release (`v2.0.0`)

As **Tags** marcam um ponto específico na história do código correspondente a um lançamento oficial.

```bash
# Criar a tag anotada v2.0.0
git tag -a v2.0.0 -m "MSRA Automator Versão 2.0.0 - Release Oficial"

# Enviar a tag criada para o GitHub
git push origin v2.0.0
```

Se quiser enviar todas as tags locais de uma vez:
```bash
git push origin --tags
```

---

## 📦 Passo 5: Criar a Release no GitHub e Anexar o Executável (`.exe`)

Para que seus colegas de equipe possam baixar o **`MSRA Automator.exe`** pronto para uso sem precisar compilar o código fonte, siga as instruções abaixo:

### Método A: Pela Interface Web do GitHub (Recomendado)

1. Acesse a página principal do seu repositório no GitHub.
2. No menu do lado direito, clique em **Releases** (ou acesse `https://github.com/SEU_USUARIO/msra_automator/releases`).
3. Clique no botão **Draft a new release** (ou **Create a new release**).
4. Em **Choose a tag**, selecione a tag **`v2.0.0`** enviada no Passo 4.
5. No campo **Release title**, digite: `MSRA Automator v2.0.0`.
6. Na caixa de descrição, insira o resumo das novidades da versão (ex.: novidades, correções, instrução de uso).
7. Na seção **Attach binaries by dropping them here or selecting them**:
   - Arraste e solte o arquivo **`MSRA Automator.exe`** da raiz do projeto para dentro da área pontilhada (ou clique em escolher arquivo).
   - Aguarde o upload do executável finalizar (cerca de 50MB).
8. Clique em **Publish release**.

---

### Método B: Pelo GitHub CLI (`gh`)

Se você utiliza o utilitário de linha de comando oficial do GitHub:

```bash
gh release create v2.0.0 "./MSRA Automator.exe" --title "MSRA Automator v2.0.0" --notes "Release v2.0.0 funcional do MSRA Automator."
```

---

## ✨ Resultado Final

Após seguir os passos:
- O código-fonte estará organizado e seguro no repositório GitHub.
- A **Tag `v2.0.0`** estará registrada e visível na aba de tags.
- Na aba **Releases**, haverá o download direto do **`MSRA Automator.exe`** para qualquer usuário da equipe utilizar imediatamente.

---

## 🔄 Como Atualizar para Novas Versões no Futuro

Quando desenvolver novas funcionalidades (ex.: versão 2.1.0):

1. Atualize o código.
2. Execute `python build_v2.py` ou `build.bat` para gerar o novo `.exe`.
3. Faça o commit: `git commit -m "Feat: novas melhorias..."`.
4. Envie o código: `git push origin main`.
5. Crie a nova tag: `git tag -a v2.1.0 -m "Versão 2.1.0"` e `git push origin v2.1.0`.
6. Crie a Release v2.1.0 no GitHub anexando o novo `MSRA Automator.exe`.

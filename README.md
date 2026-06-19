# MSRA Automator 🖥️

O **MSRA Automator** é uma solução profissional em Python para simplificar e acelerar a prestação de suporte de TI utilizando a **Assistência Remota do Windows (MSRA)**. 

Desenvolvida com **PyQt6** para uma interface de usuário moderna e responsiva, e com **pywinauto** para a automação de processos, a ferramenta automatiza todas as etapas burocráticas de conexão a computadores remotos em um domínio corporativo.

---

## 🚀 Funcionalidades Principais

- **Interface Gráfica Moderna (PyQt6):** Layout limpo, responsivo, com suporte a atalhos rápidos e cópia simplificada de relatórios.
- **Resolução de Nomes Inteligente:** Seleção rápida de categorias de dispositivos (Computadores WK, Equipamentos Médicos MD, Notebooks NT) com auto-preenchimento e geração automática do hostname finalizado.
- **Teste de Conectividade Integrado:** Permite disparar pings diretamente pela interface gráfica sem travar a tela principal (utilizando threads dedicados) para validar se o dispositivo está ativo antes da conexão.
- **Automação Completa do MSRA:** Preenche automaticamente todas as telas da Assistência Remota do Windows (abertura do processo, seleção de conexões avançadas, preenchimento do hostname e envio da solicitação).
- **Elevação Automática de Privilégios (UAC):** Detecta se está sendo executado como usuário comum e solicita elevação administrativa automaticamente quando necessário, garantindo a permissão correta de automação.
- **Tratamento de Erros e Logs:** Gravação de relatórios de atividades em tempo de execução para facilitar o diagnóstico de falhas em conexões.

---

## 🛠️ Arquitetura Técnica

A aplicação é dividida de forma modular:

1. **`main.py`:** Ponto de entrada, responsável pela inicialização do PyQt6, criação de atalhos e orquestração do UAC (Controle de Conta de Usuário).
2. **`core/`:**
   - **`msra_service.py`:** Módulo que se conecta à janela nativa do Windows `msra.exe` e utiliza o backend UIA (UI Automation) do `pywinauto` para preencher os inputs de conexão.
   - **`admin_check.py`:** Lógica de validação e reexecução da aplicação com direitos de Administrador.
   - **`logger.py`:** Gerenciador de logs do sistema.
3. **`gui/`:**
   - **`main_window.py`:** Tela principal do usuário, painel de logs interativo e integração de threads.
   - **`styles.py` / `widgets.py`:** Estilização visual (CSS/QSS) e componentes customizados para o PyQt6.
4. **`models/`:**
   - **`hostname_builder.py`:** Regras para construção do hostname final a partir do prefixo do patrimônio.

---

## 📦 Como Compilar em um Executável Único (.exe)

Criamos um script que cuida de toda a configuração do ambiente e compilação do executável.

1. Navegue até a pasta do projeto.
2. Dê um duplo-clique no arquivo `build.bat`.
3. O script irá instalar as dependências do `requirements.txt` e gerar o executável final.
4. Ao término, o executável **`MSRA Automator.exe`** estará disponível na raiz da pasta.

---

## 💻 Requisitos do Sistema

- **Sistema Operacional:** Windows 10 ou superior.
- **Dependências de Código Fonte:**
  - Python 3.8+ (caso deseje executar diretamente os scripts `.py`).
  - Dependências listadas no `requirements.txt` (`PyQt6`, `pywinauto`, `pywin32`).

---

## 📡 Compartilhando no GitHub

Para colocar este projeto no seu perfil do GitHub e compartilhar com os colegas de equipe, siga o guia detalhado em [COMO_SUBIR_GITHUB.md](COMO_SUBIR_GITHUB.md).

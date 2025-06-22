## 🚀 Como Executar o Projeto PataCerta

Siga estes passos para configurar e executar a plataforma PataCerta no seu ambiente de desenvolvimento local.

---

### 🛠️ Pré-requisitos

* **Python 3.8+**
* **PostgreSQL**

---

### 1️⃣ Configuração do Banco de Dados

1. **Criar o banco de dados**
   Abra o `psql` (ou pgAdmin) e execute:

   ```sql
   CREATE DATABASE petmatch;
   ```

2. **Criar tabelas e estruturas**
   Conecte-se ao banco:

   ```sql
   \c petmatch
   ```

   Em seguida, na raiz do projeto, importe o esquema:

   ```bash
   psql -U seu_usuario_postgres -d petmatch -f schema.sql
   ```

   > *Substitua* `seu_usuario_postgres` pelo seu usuário PostgreSQL.

---

### 2️⃣ Configuração do Ambiente do Projeto

1. **Criar e ativar um ambiente virtual**

   ```bash
   # Cria o venv
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # macOS / Linux
   source venv/bin/activate
   ```

2. **Instalar dependências**

   ```bash
   pip install -r requirements.txt
   ```

3. **Definir variáveis de ambiente**
   Crie um arquivo `.env` em `app/Backend/` com:

   ```dotenv
   DB_NAME=petmatch
   DB_USER=seu_usuario_postgres
   DB_PASSWORD=sua_senha_postgres
   DB_HOST=localhost
   DB_PORT=5432
   ```

   > *Altere* os valores conforme seu ambiente.

---

### 3️⃣ Populando o Banco de Dados

1. **Dados de teste**

   ```bash
   python popula.py
   ```

2. **(Opcional) Atualizar imagens dos animais**

   ```bash
   python populate_images.py
   ```

---

### 4️⃣ Executando o Backend (API)

1. **Navegue até a pasta**

   ```bash
   cd app/Backend
   ```

2. **Inicie o servidor FastAPI**

   ```bash
   python main.py
   ```

   > O servidor estará em `http://127.0.0.1:8000` (com reload automático).

---

### 5️⃣ Acessando o Frontend

* Abra `templates/index.html` diretamente no navegador (Chrome, Firefox, etc.)
* A interface consumirá a API em execução.

---

🎉 **Pronto!**
Agora a plataforma PataCerta está rodando localmente. Aproveite!

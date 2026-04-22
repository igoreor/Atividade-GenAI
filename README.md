# E-Commerce Analytics Agent

Agente de IA que permite que qualquer pessoa faça perguntas em português sobre os dados de um e-commerce e receba respostas claras, sem precisar saber SQL ou programação.

O usuário digita algo como *"Quais estados têm maior atraso nas entregas?"* e o agente converte automaticamente para uma consulta SQL, executa no banco de dados e devolve a resposta interpretada em linguagem natural.

---

## Como funciona

```
Usuário digita uma pergunta em português
        ↓
Frontend (Next.js) envia a pergunta para o backend
        ↓
Agente (LangChain + Gemini 2.5 Flash) analisa o schema do banco
        ↓
Gemini gera a consulta SQL correspondente
        ↓
Guardrail valida: somente SELECT é permitido
        ↓
SQL é executado no banco SQLite
        ↓
Gemini interpreta os resultados e responde em português
        ↓
Resposta exibida no chat
```

Se o SQL gerado tiver algum erro, o agente se corrige automaticamente e tenta de novo (até 3 vezes).

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Modelo de IA | Gemini 2.5 Flash (Google AI) |
| Framework de agente | LangChain (LCEL + chains) |
| Backend | Python 3.11 + FastAPI + Uvicorn |
| Frontend | Next.js 16 + TypeScript + Tailwind CSS |
| Banco de dados | SQLite (sem instalação, embutido no Python) |

---

## O que o agente sabe responder

O banco contém dados reais de um e-commerce brasileiro com ~99 mil pedidos. O agente responde qualquer pergunta sobre esses dados, incluindo:

**Vendas e Receita**
- Top 10 produtos mais vendidos
- Receita total por categoria de produto
- Faturamento geral do e-commerce

**Entrega e Logística**
- Quantidade de pedidos por status (entregue, cancelado, etc.)
- Percentual de pedidos entregues no prazo por estado
- Estados com maior atraso médio nas entregas

**Avaliações e Satisfação**
- Média geral de avaliação dos pedidos
- Top 10 vendedores com melhores avaliações
- Categorias com maior taxa de avaliações negativas (notas 1 e 2)

**Consumidores**
- Estados com maior volume de pedidos
- Estados com maior ticket médio
- Distribuição geográfica dos clientes

**Vendedores e Produtos**
- Produto mais vendido em cada estado
- Comparativos de desempenho por vendedor

Além das perguntas pré-definidas acima, o agente aceita qualquer pergunta livre em linguagem natural sobre os dados.

---

## Estrutura do Projeto

```
Atividade-GenAI/
│
├── dados/                        # CSVs originais do e-commerce
│   ├── dim_consumidores.csv      # ~99 mil clientes
│   ├── dim_produtos.csv          # ~33 mil produtos
│   ├── dim_vendedores.csv        # ~3 mil vendedores
│   ├── dim_categoria_imagens.csv # imagens por categoria
│   ├── fat_pedidos.csv           # ~99 mil pedidos
│   ├── fat_itens_pedidos.csv     # ~113 mil itens
│   └── fat_avaliacoes_pedidos.csv# ~95 mil avaliações
│
├── backend/
│   ├── main.py        # API FastAPI com todos os endpoints
│   ├── agent.py       # Agente Text-to-SQL (LangChain + Gemini)
│   ├── analytics.py   # 10 consultas analíticas pré-definidas
│   ├── database.py    # Conexão SQLite e leitura de schema
│   └── models.py      # Modelos Pydantic de request e response
│
├── frontend/
│   ├── app/                  # Next.js App Router (página principal)
│   ├── components/chat/      # Componentes: header, mensagem, input
│   ├── hooks/use-chat.ts     # Lógica do chat — chama POST /api/query
│   ├── types/chat.ts         # Tipos TypeScript da aplicação
│   └── next.config.mjs       # Proxy: /api/* → http://localhost:8000/*
│
├── scripts/
│   └── build_db.py    # Cria banco.db a partir dos CSVs
│
├── banco.db           # Banco SQLite gerado (não versionado)
├── .env               # Suas credenciais (não versionado)
├── .env.example       # Modelo das variáveis de ambiente
└── requirements.txt   # Dependências Python
```

---

## Pré-requisitos

- **Node.js 18** ou superior (para o frontend)
- **Chave de API do Google AI Studio** — obtenha gratuitamente em https://aistudio.google.com/apikey
- **Docker** (recomendado para o backend) **ou** Python 3.11+ (execução manual)

---

## Rodando com Docker (recomendado)

A forma mais fácil de subir o backend. Não é necessário instalar Python, criar ambiente virtual ou gerar o banco manualmente — tudo acontece dentro do container.

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd Atividade-GenAI
```

### 2. Configure as variáveis de ambiente

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

Abra `.env` e preencha sua chave de API:

```env
GOOGLE_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
DB_PATH=banco.db
MAX_ROWS=500
```

> **Como obter a `GOOGLE_API_KEY`:** acesse o [Google AI Studio](https://aistudio.google.com/apikey), faça login com sua conta Google e crie uma chave por lá. É gratuito.

### 3. Suba o container

```bash
docker compose up --build
```

Na primeira execução, o Docker vai:
1. Baixar a imagem base do Python 3.11
2. Instalar todas as dependências
3. Gerar o banco de dados a partir dos CSVs
4. Iniciar a API na porta 8000

As próximas execuções usam o cache e sobem em segundos:

```bash
docker compose up
```

Para rodar em segundo plano:

```bash
docker compose up -d
```

Para parar:

```bash
docker compose down
```

API disponível em **http://localhost:8000** | Swagger em **http://localhost:8000/docs**

### 4. Instale as dependências do frontend

```bash
cd frontend
npm install
cd ..
```

### 5. Inicie o frontend

```bash
cd frontend
npm run dev
```

Frontend disponível em **http://localhost:3000**

> O Next.js encaminha automaticamente as chamadas `/api/*` para o backend no container. Não é necessário configurar nada extra.

---

## Instalação e Configuração (sem Docker)

Use este caminho se preferir rodar sem Docker ou se precisar do `--reload` para desenvolvimento.

### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
cd Atividade-GenAI
```

### 2. Crie e ative o ambiente virtual Python

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instale as dependências Python

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
# Linux / macOS
cp .env.example .env

# Windows
copy .env.example .env
```

Abra o arquivo `.env` e preencha sua chave de API:

```env
GOOGLE_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
DB_PATH=banco.db
MAX_ROWS=500
```

> **Como obter a `GOOGLE_API_KEY`:** acesse o [Google AI Studio](https://aistudio.google.com/apikey), faça login com sua conta Google e crie uma chave por lá. É gratuito.

### 5. Gere o banco de dados

Este comando lê os CSVs da pasta `dados/` e cria o arquivo `banco.db`. Execute uma única vez:

```bash
python scripts/build_db.py
```

Saída esperada:
```
  OK dim_consumidores               99,441 linhas
  OK dim_produtos                   32,951 linhas
  OK dim_vendedores                  3,095 linhas
  OK fat_pedidos                    99,441 linhas
  OK fat_itens_pedidos             112,650 linhas
  OK fat_avaliacoes_pedidos         95,307 linhas
  OK view fat_pedido_total criada

Banco construído em: .../banco.db
```

### 6. Instale as dependências do frontend

```bash
cd frontend
npm install
cd ..
```

---

## Como Rodar (sem Docker)

Abra **dois terminais** na raiz do projeto.

**Terminal 1 — Backend:**

```bash
# Ative o ambiente virtual se ainda não estiver ativo
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate

uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Acesse **http://localhost:3000** no navegador.

> O frontend usa um proxy interno do Next.js para encaminhar as chamadas `/api/*` direto para o backend em `localhost:8000`. Não é necessário configurar nada extra para a comunicação entre eles.

---

## Referência da API

A API pode ser usada diretamente via HTTP, sem o frontend. A documentação interativa completa (Swagger) fica em **http://localhost:8000/docs**.

### Consulta livre em linguagem natural

```
POST /query
```

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Quais são os 10 produtos mais vendidos?", "return_sql": false}'
```

Resposta:
```json
{
  "question": "Quais são os 10 produtos mais vendidos?",
  "answer": "Os 10 produtos mais vendidos são:\n1. Estante de Livros Luxo — 527 unidades...",
  "sql": null,
  "rows": [...],
  "row_count": 10,
  "error": null
}
```

Passe `"return_sql": true` para incluir o SQL gerado na resposta.

### Análises pré-definidas

```
GET /analytics/{slug}
```

| Slug | O que retorna |
|------|---------------|
| `top-produtos` | Top 10 produtos com mais unidades vendidas |
| `receita-por-categoria` | Receita, ticket médio e total de pedidos por categoria |
| `pedidos-por-status` | Contagem e percentual de pedidos por status |
| `prazo-por-estado` | % de pedidos entregues no prazo por estado do cliente |
| `media-avaliacao-geral` | Média de nota e distribuição de 1 a 5 estrelas |
| `top-vendedores-avaliacao` | Top 10 vendedores por nota média (mín. 10 avaliações) |
| `estados-volume-ticket` | Total de pedidos e ticket médio por estado |
| `estados-maior-atraso` | Estados com maior atraso médio nas entregas |
| `produtos-mais-vendidos-por-estado` | Produto campeão de vendas em cada estado |
| `categorias-avaliacao-negativa` | Categorias com maior proporção de notas 1 e 2 |

```bash
# Exemplo
curl http://localhost:8000/analytics/top-produtos
```

### Outros endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Verifica se a API e o banco estão funcionando |
| `GET` | `/schema` | Lista todas as tabelas e colunas do banco |
| `GET` | `/analytics` | Lista todos os slugs de análise disponíveis |

---

## Guardrails — Segurança e Confiabilidade

O agente possui quatro camadas de proteção:

1. **Bloqueio de intenção de escrita** — antes de qualquer chamada ao modelo, perguntas com verbos como "apagar", "deletar", "modificar", "inserir" são rejeitadas com erro 400.

2. **Validação do SQL gerado** — após o modelo gerar a query, o código verifica se ela começa com `SELECT` e não contém nenhuma instrução de escrita (`INSERT`, `UPDATE`, `DELETE`, `DROP`, etc.). Se contiver, o SQL é bloqueado.

3. **Retry com autocorreção** — se o SQL falhar na execução por erro de sintaxe, o agente reenvia o SQL com a mensagem de erro para o modelo e pede a correção. Isso acontece até 3 vezes antes de desistir.

4. **Limite de linhas** — toda consulta é limitada a `MAX_ROWS` linhas (padrão 500) para evitar respostas lentas ou excessivamente longas.

---

## Banco de Dados

O banco SQLite é construído a partir dos CSVs e contém as seguintes tabelas:

| Tabela | Linhas | Descrição |
|--------|--------|-----------|
| `dim_consumidores` | 99.441 | Clientes: id, nome anonimizado, cidade, estado |
| `dim_produtos` | 32.951 | Produtos: id, nome, categoria, peso e dimensões |
| `dim_vendedores` | 3.095 | Vendedores: id, nome, cidade, estado |
| `fat_pedidos` | 99.441 | Pedidos: status, datas de compra e entrega, prazo |
| `fat_itens_pedidos` | 112.650 | Itens: produto, vendedor, preço e frete por item |
| `fat_avaliacoes_pedidos` | 95.307 | Avaliações: nota de 1 a 5, título e comentário |
| `fat_pedido_total` *(view)* | — | Totais agregados por pedido (criada automaticamente pelo script) |

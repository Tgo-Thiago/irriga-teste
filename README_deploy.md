# Irrigatech — Deploy Gratuito

Stack: **FastAPI backend** + **Vanilla JS frontend** + **Supabase** (banco/auth)

---

## Arquitetura de deploy

| Camada    | Serviço     | Custo  | URL tipo                              |
|-----------|-------------|--------|---------------------------------------|
| Frontend  | **Vercel**  | Grátis | `irrigatech.vercel.app`               |
| Backend   | **Render**  | Grátis | `irrigatech-api.onrender.com`         |
| Banco/Auth| **Supabase**| Grátis | já configurado                        |

---

## 1. Backend no Render (FastAPI)

### Pré-requisitos
- Repositório no GitHub com o código do backend
- `requirements.txt` na raiz do backend

### Passos
1. Acesse [render.com](https://render.com) → **New Web Service**
2. Conecte seu repositório GitHub
3. Configure:
   - **Name:** `irrigatech-api`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Adicione as variáveis de ambiente:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=sua-anon-key
   SECRET_KEY=uma-chave-secreta-qualquer
   ```
5. Clique **Create Web Service**

> ⚠️ O free tier do Render "dorme" após 15 min sem requisições.  
> Primeira chamada após inatividade leva ~15s. Para beta é aceitável.

---

## 2. Frontend no Vercel

### Passos
1. Acesse [vercel.com](https://vercel.com) → **New Project**
2. Importe o repositório ou faça upload da pasta `frontend/`
3. Configure:
   - **Framework Preset:** Other (Vanilla JS estático)
   - **Root Directory:** `frontend/public`
   - **Output Directory:** `.` (raiz)
   - **Build Command:** *(deixe vazio)*
4. Clique **Deploy**

### Após o deploy, atualize a URL da API
Abra `frontend/src/config/api.js` e substitua:
```js
"https://irrigatech-api.onrender.com/api"
```
pela URL real gerada pelo Render no passo 1.

---

## 3. CORS no backend

No `main.py` do FastAPI, adicione o domínio do Vercel:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5500",
        "https://irrigatech.vercel.app",   # ← sua URL do Vercel
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 4. Domínio personalizado (opcional, gratuito)

Tanto Vercel quanto Render aceitam domínios próprios gratuitamente.  
Se você tiver um domínio (ex: `irrigatech.com.br`), basta apontar o DNS.

---

## Resumo de arquivos alterados

| Arquivo                        | O que mudou                          |
|--------------------------------|--------------------------------------|
| `frontend/src/config/api.js`   | URL detecta ambiente (dev/prod)      |
| `frontend/public/design.css`   | **NOVO** — design system completo    |
| `frontend/public/home.html`    | Landing page repaginada              |
| `frontend/public/login.html`   | Tela de login repaginada             |
| `frontend/public/cadastro.html`| Cadastro repaginado                  |
| `frontend/public/dashboard.html`| Dashboard repaginado                |
| `frontend/public/index.html`   | App principal repaginado             |
| `frontend/src/ui/panel.js`     | Troca de aba automática pós-simulação|

Todos os arquivos em `frontend/src/` (services, state, map, utils) foram preservados sem alteração.

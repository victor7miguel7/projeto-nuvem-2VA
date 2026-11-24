# Tarefas – Projeto Integrador de Computação em Nuvem (UFRPE)

## Descrição
Lista de tarefas web (criar, listar, concluir, remover) implantada na AWS com pipeline CI/CD, infraestrutura como código e observabilidade.

**Integrantes e divisão de tarefas:**
- Fulano – aplicação e testes
- Ciclano – Terraform / AWS
- Beltrano – CI/CD e segredos
- Sicrano – observabilidade e documentação

## Arquitetura
```
Desenvolvedor → GitHub → GitHub Actions (test → build → push) → Amazon ECR
                                      └── deploy via SSH ──► EC2 (Elastic IP)
                                                              ├─ app (FastAPI + SQLite em ./data)
                                                              ├─ Prometheus (métricas)
                                                              ├─ Loki + Promtail (logs)
                                                              └─ Grafana (dashboards)
```

## Tecnologias e justificativas
- **FastAPI**: leve, gera métricas facilmente e é simples de testar.
- **SQLite em volume no EBS da EC2**: persistência simples e suficiente para o escopo.
- **Docker + ECR**: imagem versionada por commit (`github.sha`).
- **Terraform**: EC2, Security Group, ECR, IAM Role, Key Pair e Elastic IP.
- **GitHub Actions**: testes, build, deploy e health check.
- **Prometheus, Loki, Grafana**: métricas, logs e visualização.

## Executar localmente
```bash
cd app && pip install -r requirements.txt && python -m pytest
# ou com Docker:
docker build -t tarefas app
IMAGE=tarefas GRAFANA_PASSWORD=admin docker compose up
```
App em http://localhost e Grafana em http://localhost:3000.

## Implantar
1. Criar a infraestrutura (uma vez):
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/tarefas -N ""
   export AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
   cd infra && terraform init
   terraform apply -var="public_key=$(cat ~/.ssh/tarefas.pub)"
   ```
2. Cadastrar secrets no GitHub (Settings → Secrets and variables → Actions):
   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `EC2_HOST` (ip_publico), `EC2_SSH_KEY` (chave privada), `GRAFANA_PASSWORD`.
3. Fazer push na `main`. O pipeline executa automaticamente.

## Remover os recursos
```bash
cd infra && terraform destroy -var="public_key=$(cat ~/.ssh/tarefas.pub)"
```

## Pipeline CI/CD
1. `test`: instala dependências e roda `pytest`.
2. `deploy` (só roda se `test` passar, via `needs: test`): build da imagem, push no ECR, envio do compose e `docker compose up -d` na EC2.
3. Health check: `curl --fail` em `/health` com retentativas; se falhar, o pipeline falha.

## Testes
Testes de API com pytest/TestClient (health, criação/listagem, validação, 404, métricas). Se algum teste falhar, o job de deploy não é executado.

## Segurança
- Credenciais armazenadas em GitHub Secrets; nenhuma no código.
- `.env` e `*.tfstate` no `.gitignore`.
- A EC2 usa IAM Role com permissão somente leitura no ECR.
- Secrets mascarados nos logs do GitHub Actions.

## Observabilidade
- **Métricas**: `/metrics` coletado pelo Prometheus (porta 9090).
- **Logs**: logs do app coletados por Promtail e armazenados no Loki.
- **Visualização**: Grafana em `http://IP:3000` (usuário `admin`). Importar dashboard ID 16110 ou consultar `{container="app-app-1"}` no Explore → Loki.

## Evidências
Adicionar aqui prints do pipeline, da aplicação e do Grafana.

# Proposta Inicial

**Grupo:** (nomes dos integrantes)

## Problema
Pessoas e equipes pequenas precisam organizar tarefas do dia a dia de forma simples e acessível de qualquer lugar. A aplicação "Tarefas" oferece uma lista de tarefas web, disponível na nuvem.

## Funcionalidades
- Criar, listar, concluir e remover tarefas
- Persistência dos dados entre reinicializações
- Endpoint de saúde (`/health`) e métricas (`/metrics`)

## Arquitetura preliminar
GitHub → GitHub Actions → Amazon ECR → EC2 (Docker Compose: app, Prometheus, Loki, Promtail, Grafana).

## Tecnologias e justificativas
| Tecnologia | Justificativa |
|---|---|
| FastAPI + HTML | Backend e frontend simples, rápido de desenvolver e testar |
| SQLite em volume (EBS) | Persistência sem custo extra e sem servidor de banco adicional |
| Docker / ECR | Artefato único e reprodutível, armazenado na AWS |
| EC2 + Elastic IP | Controle simples da execução e IP fixo para o deploy |
| Terraform | Infraestrutura versionada e reproduzível |
| GitHub Actions | Pipeline integrado ao repositório |
| GitHub Secrets | Gerenciamento de segredos sem custo (Infisical é opcional no enunciado) |
| Prometheus / Loki / Grafana | Métricas, logs e dashboards |

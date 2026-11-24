# Proposta Inicial – Projeto Integrador de Computação em Nuvem

**Grupo:** Victor Miguel

## 1. Problema

Pessoas e equipes pequenas precisam organizar tarefas do dia a dia de forma simples, acessível de qualquer dispositivo e sem depender de instalação de software. A aplicação **Tarefas** oferece uma lista de tarefas web hospedada em nuvem, com dados persistidos e monitoramento do seu funcionamento.

## 2. Funcionalidades

- Criar tarefas (com validação de título vazio)
- Listar tarefas
- Marcar tarefas como concluídas
- Remover tarefas
- Endpoint de saúde (`/health`) e de métricas (`/metrics`)

## 3. Arquitetura

```
Desenvolvedor → GitHub → GitHub Actions (testes → build → push) → Amazon ECR
                                      └── deploy via SSH ──► EC2 + Elastic IP
                                                              ├─ App (FastAPI + SQLite em volume EBS)
                                                              ├─ Prometheus (métricas)
                                                              ├─ Loki + Promtail (logs)
                                                              └─ Grafana (dashboards)
```

| Camada | Componente |
|---|---|
| Frontend | Página HTML/JavaScript servida pelo FastAPI |
| Backend | API REST em FastAPI (Python) |
| Persistência | SQLite em volume no disco da EC2 (EBS) |
| Infraestrutura | EC2, ECR, Security Group, Elastic IP e chave SSH, provisionados com Terraform |
| CI/CD | GitHub Actions: testes, build, push ao ECR, deploy e health check |
| Segredos | GitHub Secrets |
| Observabilidade | Prometheus, Loki, Promtail e Grafana |

## 4. Tecnologias e justificativas

| Tecnologia | Justificativa |
|---|---|
| FastAPI | Leve, simples de testar e com instrumentação de métricas pronta |
| SQLite | Suficiente para o escopo e sem custo de banco gerenciado |
| Docker e Docker Compose | Empacotamento reprodutível da aplicação e da pilha de observabilidade |
| Amazon EC2 | Controle simples do ambiente; uma instância comporta toda a solução |
| Amazon ECR | Registro de imagens integrado à AWS, com versionamento por commit |
| Terraform | Infraestrutura reproduzível e versionada no Git |
| GitHub Actions | Pipeline integrado ao repositório |
| GitHub Secrets | Gerenciamento de credenciais sem serviço adicional (Infisical é opcional no enunciado) |
| Prometheus, Loki, Grafana | Métricas, logs e visualização em uma pilha integrada |

## 5. Atendimento aos requisitos técnicos

| Requisito | Como será atendido |
|---|---|
| Aplicação com persistência | FastAPI + SQLite em volume |
| Terraform | Provisiona EC2, ECR, Security Group, chave SSH e Elastic IP |
| CI/CD | Testes → build → push → deploy → verificação de disponibilidade |
| Segurança e segredos | Credenciais em GitHub Secrets, fora do código e mascaradas nos logs |
| Testes automatizados | `pytest` em API, executados no pipeline; falha bloqueia o deploy |
| Observabilidade | Métricas (Prometheus), logs (Loki) e dashboard (Grafana) |
| Documentação | README com arquitetura, execução, implantação, remoção e evidências |

## 6. Divisão de tarefas

| Integrante | Responsabilidade principal |
|---|---|
| [Victor] | Aplicação e testes |
| [Victor] | Terraform e serviços AWS |
| [Victor] | Pipeline CI/CD e segredos |
| [Victor] | Observabilidade e documentação |

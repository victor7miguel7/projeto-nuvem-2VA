# Proposta Inicial – Projeto Integrador de Computação em Nuvem

**Projeto:** Tarefas na Nuvem
**Disciplina:** Computação em Nuvem – UFRPE
**Grupo:** Victor
**Repositório:** https://github.com/victor7miguel7/projeto-nuvem-2VA

## 1. Problema

Pessoas e equipes pequenas precisam organizar tarefas do dia a dia de forma simples, acessível de qualquer dispositivo e sem instalar software. Listas em papel ou em arquivos soltos não indicam o que é mais urgente, não avisam o que está atrasado e não ficam disponíveis em todos os lugares.

A solução proposta é uma aplicação web de tarefas hospedada na nuvem, que guarda os dados de forma persistente, destaca prioridades e prazos e permite acompanhar o seu próprio funcionamento por métricas e logs.

## 2. Funcionalidades previstas

**Gestão de tarefas**
- Criar tarefas com título, prioridade (alta, média ou baixa) e prazo opcional
- Listar tarefas, com ordenação por situação, prioridade e prazo
- Editar título, prioridade e prazo
- Marcar como concluída e reabrir
- Remover uma tarefa ou todas as concluídas de uma vez
- Filtrar por situação (todas, pendentes, concluídas) e buscar por texto
- Indicar tarefas atrasadas e o progresso das tarefas concluídas

**Operação e observabilidade**
- Endpoint de saúde (`/health`) para verificação automática de disponibilidade
- Endpoint de métricas (`/metrics`) com métricas HTTP e de negócio (tarefas criadas e concluídas)
- Registro de logs de operações e de erros

## 3. Arquitetura preliminar

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
| CI/CD | GitHub Actions: testes, build, push ao ECR, deploy e verificação de disponibilidade |
| Segredos | GitHub Secrets |
| Observabilidade | Prometheus, Loki, Promtail e Grafana |

**Ambiente:** AWS Academy Learner Lab, região `us-east-1`. A EC2 usa o perfil `LabInstanceProfile`, já disponível no laboratório, para baixar imagens do ECR.

## 4. Tecnologias e justificativas

| Tecnologia | Justificativa |
|---|---|
| FastAPI | Leve, simples de testar e com instrumentação de métricas pronta |
| SQLite | Suficiente para o escopo e sem custo de banco gerenciado |
| Docker e Docker Compose | Empacotamento reprodutível da aplicação e de toda a pilha de observabilidade |
| Amazon EC2 | Controle simples do ambiente; uma instância comporta aplicação e observabilidade |
| Amazon ECR | Registro de imagens integrado à AWS, com versionamento por commit |
| Terraform | Infraestrutura reproduzível e versionada no Git |
| GitHub Actions | Pipeline integrado ao repositório |
| GitHub Secrets | Gerenciamento de credenciais sem serviço adicional. O Infisical é citado como opcional no enunciado, e esta escolha será confirmada nas aulas de acompanhamento |
| Prometheus, Loki, Grafana | Métricas, logs e visualização em uma pilha integrada |

## 5. Atendimento aos requisitos técnicos

| Requisito | Como será atendido |
|---|---|
| Aplicação com persistência | FastAPI + SQLite em volume |
| Terraform | Provisiona EC2, ECR, Security Group, chave SSH e Elastic IP; instala Docker na criação da máquina |
| CI/CD | Testes → build → push → deploy → verificação de disponibilidade |
| Segurança e segredos | Credenciais em GitHub Secrets, fora do código e mascaradas nos logs; validação dos dados de entrada na API |
| Testes automatizados | `pytest` em API (criação, edição, filtros, validações, métricas), executados no pipeline; falha bloqueia o deploy |
| Observabilidade | Métricas (Prometheus), logs (Loki) e dashboard (Grafana) |
| Documentação | README com arquitetura, execução, implantação, remoção e evidências |

## 6. Etapas previstas

1. Proposta e criação do repositório
2. Desenvolvimento da aplicação e dos testes
3. Provisionamento da infraestrutura com Terraform
4. Pipeline CI/CD e gerenciamento de segredos
5. Observabilidade: métricas, logs e dashboard
6. Documentação e coleta de evidências

## 7. Riscos e limitações previstos

- As credenciais do Learner Lab são temporárias e precisam ser renovadas nos secrets a cada sessão.
- Uma única EC2 e um banco SQLite não oferecem alta disponibilidade nem múltiplas instâncias; em produção seriam usados balanceamento de carga e um banco gerenciado.
- A primeira versão não terá autenticação de usuários, o que fica como evolução futura.

## 8. Divisão de tarefas

| Integrante | Responsabilidade principal |
|---|---|
| Victor | Aplicação (backend, frontend) e testes |
| Victor | Terraform e serviços AWS |
| Victor | Pipeline CI/CD e segredos |
| Victor | Observabilidade e documentação |

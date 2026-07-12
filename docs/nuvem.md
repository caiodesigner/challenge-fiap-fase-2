# Implantação opcional no Google Cloud

## Escopo

A aplicação foi preparada para execução containerizada no Google Cloud Run. A
infraestrutura é declarada em Terraform e cobre:

- Artifact Registry para imagens privadas;
- Cloud Run com escala de zero a duas instâncias por padrão;
- conta de serviço exclusiva para o runtime;
- provedor de linguagem configurável por variáveis de ambiente;
- probes de inicialização e atividade em `/health`;
- logs de requisição, aplicação e plataforma no Cloud Logging;
- acesso público configurável por IAM.

O provisionamento real não é executado automaticamente pelo repositório, pois
gera recursos faturáveis e exige um projeto Google Cloud sob responsabilidade do
grupo.

## Arquitetura

```mermaid
flowchart LR
    U[Operador] -->|HTTPS| R[Cloud Run]
    R --> A[FastAPI + algoritmo genético]
    R -->|imagem| AR[Artifact Registry]
    R -->|identidade| SA[Service Account]
    R --> CL[Cloud Logging]
    A -.->|host configurável| O[Serviço Ollama]
```

O Cloud Run termina TLS e injeta a porta de execução. O processo Python respeita
`HOST` e `PORT`; no contêiner, os padrões são `0.0.0.0:8080`. Os cenários são
lidos de `DATA_DIR=/app/data`. O modo `LLM_PROVIDER=local` não depende de outro
serviço. Para usar Ollama na nuvem, `OLLAMA_HOST` deve apontar para uma instância
separada e acessível pelo Cloud Run; o modelo não está embutido na imagem web.

## Pré-requisitos

- conta Google Cloud com faturamento habilitado;
- projeto e permissões para habilitar APIs e criar os recursos declarados;
- Google Cloud CLI autenticado;
- Terraform 1.7 ou superior;
- Docker 24 ou superior.

Defina os valores da sessão:

```bash
export PROJECT_ID="meu-projeto-gcp"
export REGION="southamerica-east1"
export SERVICE_NAME="rotas-medicas"
export IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/app:$(git rev-parse --short HEAD)"
gcloud auth login
gcloud auth application-default login
gcloud config set project "${PROJECT_ID}"
```

## Teste local do contêiner

```bash
docker build -t rotas-medicas:local .
docker run --rm -p 8080:8080 rotas-medicas:local
curl --fail http://127.0.0.1:8080/health
```

Acesse `http://127.0.0.1:8080`. Para conectar o contêiner a um Ollama acessível,
passe as configurações em tempo de execução:

```bash
docker run --rm -p 8080:8080 \
  -e LLM_PROVIDER=ollama \
  -e OLLAMA_HOST=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=qwen2.5:1.5b \
  rotas-medicas:local
```

## Provisionamento

O Artifact Registry precisa existir antes do primeiro push. Faça uma aplicação
direcionada somente ao repositório, publique a imagem e então aplique o conjunto:

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform fmt -check
terraform validate
terraform apply -target=google_artifact_registry_repository.app
gcloud auth configure-docker "${REGION}-docker.pkg.dev"
cd ../..
docker build -t "${IMAGE}" .
docker push "${IMAGE}"
cd infra/terraform
terraform apply
terraform output -raw application_url
```

Substitua os valores de `terraform.tfvars`, inclusive `container_image`, pela
mesma imagem enviada. Use uma tag imutável, como o SHA do commit, em vez de
`latest`.

O state local é ignorado pelo Git e contém metadados da infraestrutura. Para
trabalho em equipe ou ambiente duradouro, configure um backend GCS com
versionamento e acesso restrito antes do primeiro `terraform apply`.

### Habilitar o Ollama

O padrão do Cloud Run é `llm_provider = "local"`, pois o contêiner da aplicação
não executa o servidor de modelos. Para usar uma instância Ollama já implantada,
configure:

```hcl
llm_provider = "ollama"
ollama_host  = "https://ollama.exemplo.interno"
ollama_model = "qwen2.5:1.5b"
```

Essa implantação separada é opcional; a demonstração acadêmica da LLM pode ser
feita integralmente na máquina local, sem custos de API ou de GPU em nuvem.

## Operação e observabilidade

Valide a versão publicada:

```bash
APP_URL="$(terraform output -raw application_url)"
curl --fail "${APP_URL}/health"
curl --fail "${APP_URL}/api/scenarios"
gcloud run services logs read "${SERVICE_NAME}" \
  --region "${REGION}" --limit 50
```

O Cloud Run registra status HTTP, latência, revisões, uso de CPU e memória. As
probes reiniciam uma instância não saudável. O limite de instâncias controla
custo e protege a API de escalonamento inesperado.

Como as soluções ficam em memória, cada revisão deve operar inicialmente com
poucas instâncias. Para escala horizontal consistente, o próximo incremento é
persistir soluções em banco ou armazenamento compartilhado e mover otimizações
longas para uma fila.

## Atualização e rollback

Publique cada versão com uma nova tag e altere `container_image` antes de
`terraform apply`. O Cloud Run cria uma revisão. Para rollback operacional:

```bash
gcloud run services update-traffic "${SERVICE_NAME}" \
  --region "${REGION}" --to-revisions "REVISAO_ANTERIOR=100"
```

Depois, restaure no Terraform a imagem correspondente à revisão estável para
evitar divergência entre a operação e a infraestrutura declarada.

## Remoção e custos

Inspecione o plano e remova os recursos quando a demonstração terminar:

```bash
terraform plan -destroy
terraform destroy
```

Cloud Run em escala zero reduz consumo ocioso, mas Artifact Registry, logs,
tráfego e um eventual serviço Ollama em nuvem podem gerar cobrança. Consulte a
calculadora do provedor antes da implantação.

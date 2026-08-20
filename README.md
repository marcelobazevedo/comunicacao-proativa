# Protege Antes — Comunicação Proativa com Segurados

A aplicação consulta condições meteorológicas, detecta riscos por
regras explícitas, seleciona segurados por apólice, gera mensagens com IA e entrega notificações
por WhatsApp quando a Evolution API está habilitada. SMS e e-mail permanecem simulados.

## Arquitetura

O fluxo é um grafo LangGraph com agentes especializados:

```text
coleta → verificação de mudança
              ├─ automática sem mudança → fim
              └─ manual ou com mudança → processamento → análise de risco → decisão
                                                           ├─ sem destinatários → fim
                                                           └─ comunicação → notificação → fim
```

- Open-Meteo para previsão real e geocodificação de cidades;
- Ollama + `ministral-3:14b` no modo local;
- Groq + `openai/gpt-oss-20b` no modo remoto gratuito;
- SQLite acessado com SQLAlchemy e versionado com Alembic;
- Flask/Jinja para execução e auditoria visual;
- Evolution API `v2.3.7`, PostgreSQL e Redis para WhatsApp;
- uv para dependências e Docker Compose para o ambiente de desenvolvimento.

## Desenvolvimento com Docker e Ollama local

O fluxo recomendado usa Flask/Python dentro do Docker e o Ollama já instalado no computador.
Verifique primeiro se o Ollama está ativo e se o modelo responde:

```bash
ollama list
curl http://localhost:11434/api/tags
docker compose up --build
```

Acesse [http://localhost:5001](http://localhost:5001). A porta pode ser alterada por `PORTA` no `.env`. O primeiro
`--build` cria apenas a imagem de desenvolvimento.
Depois disso, use normalmente:

```bash
docker compose up
```

O projeto inteiro é montado em `/aplicacao`, e o Flask roda com recarga automática. Alterações em
arquivos Python, templates e CSS entram sem rebuild. O `uv sync` é executado ao iniciar o serviço,
portanto mudanças no `pyproject.toml` também são aplicadas sem reconstruir a imagem.

Volumes utilizados:

- `ambiente_virtual`: dependências Python do contêiner;
- `cache_uv`: downloads e cache do uv;
- `dados_aplicacao`: arquivo SQLite persistente.
- `dados_evolution_postgres`: banco da Evolution API;
- `dados_evolution_redis`: cache persistente da Evolution API;
- `dados_evolution_instancias`: sessão pareada do WhatsApp.

No Linux, o contêiner usa a rede do host e acessa o Ollama em `127.0.0.1:11434`; ele não baixa nem
mantém uma segunda cópia do `ministral-3:14b`. Um rebuild só será necessário se o
`Dockerfile` for alterado.

Comandos úteis:

```bash
docker compose logs -f aplicacao
docker compose logs -f monitor
docker compose exec aplicacao uv run ruff check .
docker compose down                         # preserva os volumes
docker compose down --volumes               # apaga banco, ambiente e cache
```

O último comando é destrutivo e deve ser usado somente quando os dados locais puderem ser
descartados.

### Execução sem Docker (alternativa)

```bash
uv sync
uv run comunicacao-proativa preparar
uv run python main.py
```

## Seleção do modelo

O arquivo `.env` centraliza toda a configuração. Para Ollama:

```dotenv
LOCAL=True
OLLAMA_MODELO=ministral-3:14b
```

Para Groq, crie uma chave no plano gratuito e altere:

```dotenv
LOCAL=False
GROQ_API_KEY=sua-chave
GROQ_MODELO=openai/gpt-oss-20b
```

O catálogo do Groq pode mudar; o identificador é configurável sem alteração no código. Se a LLM
estiver indisponível, o fluxo registra a ocorrência e usa uma mensagem de contingência para que
o processamento continue.

## Monitoramento automático

O serviço `monitor` consulta a previsão ao iniciar e repete a verificação no intervalo definido
no `.env`. Antes da análise, o sistema calcula um resumo SHA-256 normalizado da previsão. Quando
o conteúdo é igual ao da última consulta, a execução termina sem aplicar regras, chamar a LLM ou
criar notificações. O histórico identifica essas execuções com origem **Automática**. O botão
**Verificar agora** registra a origem **Manual** e sempre percorre a pipeline completa, mesmo que
a previsão não tenha mudado.

O monitor executa em segundo plano em um contêiner separado. Enquanto o painel estiver aberto,
ele é atualizado a cada 15 segundos para apresentar mudanças no histórico. Na execução manual,
a interface mostra um indicador de processamento e desativa o botão até a resposta.

Falhas temporárias de transporte ao consultar o Open-Meteo são repetidas até três vezes. Quando
somente algumas localidades falham, a execução fica como **concluída com ressalvas** e processa
os dados obtidos; quando nenhuma previsão é coletada, fica como **erro**. Mensagens da LLM são
solicitadas sem Markdown e também normalizadas antes da persistência e da exibição.

Datas e horários são persistidos em UTC e convertidos na interface para o fuso
`America/Sao_Paulo`. A conversão também se aplica ao histórico existente e aos valores que o
SQLite retorna sem informação explícita de fuso.

Cada chamada meteorológica registra fonte, parâmetros, tentativa, duração, status e resposta
resumida. A página da execução mostra a linha do tempo dos agentes e as razões para notificar ou
não cada segurado.

```dotenv
MONITORAMENTO_ATIVO=True
INTERVALO_MONITORAMENTO_MINUTOS=30
```

O intervalo pode ser alterado para `10`, por exemplo. Depois da alteração, recrie o serviço sem
rebuild: `docker compose up -d --force-recreate monitor`.

## WhatsApp com Evolution API

Quando existe risco e um segurado elegível, a aplicação registra uma notificação auditável com
mensagem, canal, destino, tentativas, status e horário. WhatsApp utiliza envio real quando
`ENVIO_WHATSAPP_ATIVO=True`; SMS e e-mail continuam ilustrativos e simulados.

O ambiente final foi validado com a instância `protege-antes` no estado `open`. A pipeline recebeu
HTTP 201 da Evolution API, confirmou a entrega em uma tentativa e persistiu o identificador
externo. Nenhum telefone, conteúdo enviado ou credencial é incluído nesta documentação.

```dotenv
CANAL_NOTIFICACAO=whatsapp
```

Os valores aceitos são `whatsapp`, `sms` e `email`. O telefone é normalizado com o código `55`.
Somente segurados ativos com canal principal WhatsApp são enviados à Evolution API; não há
fallback automático para outro canal.

A infraestrutura usa a imagem fixa `evoapicloud/evolution-api:v2.3.7`, PostgreSQL 16, Redis 7 e
volumes persistentes. Preencha no `.env` as senhas, chave e instância e inicie o perfil:

```bash
docker compose --profile whatsapp up -d evolution-api
```

Abra [http://localhost:8080/manager](http://localhost:8080/manager), informe a URL
`http://localhost:8080` e a chave presente em `EVOLUTION_API_KEY`, crie ou abra a instância
indicada por `EVOLUTION_API_INSTANCIA` e escaneie o QR Code em **WhatsApp → Dispositivos
conectados → Conectar dispositivo**.

Após o estado da instância ficar `open`, valide sem enviar:

```bash
docker compose exec aplicacao uv run comunicacao-proativa validar-evolution
```

Para um envio real explícito:

```bash
docker compose exec aplicacao uv run comunicacao-proativa testar-whatsapp \
  --numero "(11) 99999-9999" \
  --mensagem "Teste de integração do Protege Antes."
```

Em uma instalação nova, por fim altere `ENVIO_WHATSAPP_ATIVO=True` e recrie aplicação e monitor
para que a pipeline passe a enviar automaticamente:

```bash
docker compose up -d --force-recreate aplicacao monitor
```

A chave de idempotência impede duplicidades por execução, segurado, evento e mensagem. Falhas
temporárias recebem retentativas; códigos permanentes são registrados sem repetição automática.

## Segurança e saída da LLM

Todos os formulários POST usam token CSRF. Ollama e Groq recebem um JSON Schema e a resposta é
validada por Pydantic antes da persistência. `LLM_MAXIMO_TENTATIVAS` controla as novas tentativas.
Para validar uma chave Groq e confirmar o modelo configurado:

```bash
docker compose exec aplicacao uv run comunicacao-proativa validar-groq
```

## Parâmetros dos alertas

Todos os limiares meteorológicos são configurados no `.env`:

```dotenv
ALERTA_CHUVA_INTENSA_MM=50
ALERTA_CHUVA_COM_PROBABILIDADE_MM=30
ALERTA_PROBABILIDADE_MINIMA_CHUVA=80
ALERTA_VENTO_FORTE_KMH=75
ALERTA_VENTO_SEVERIDADE_ALTA_KMH=90
ALERTA_CODIGOS_WMO_GRANIZO=[96,99]
```

| Variável                             |     Padrão | Unidade/formato | Finalidade                                                   |
| ------------------------------------- | ----------: | --------------- | ------------------------------------------------------------ |
| `ALERTA_CHUVA_INTENSA_MM`           |          50 | mm/dia          | Dispara chuva intensa diretamente e define severidade alta.  |
| `ALERTA_CHUVA_COM_PROBABILIDADE_MM` |          30 | mm/dia          | Acumulado mínimo usado junto à probabilidade.              |
| `ALERTA_PROBABILIDADE_MINIMA_CHUVA` |          80 | %               | Probabilidade mínima para o alerta condicionado de chuva.   |
| `ALERTA_VENTO_FORTE_KMH`            |          75 | km/h            | Rajada mínima para detectar vento forte.                    |
| `ALERTA_VENTO_SEVERIDADE_ALTA_KMH`  |          90 | km/h            | Rajada mínima para classificar o vento com severidade alta. |
| `ALERTA_CODIGOS_WMO_GRANIZO`        | `[96,99]` | lista JSON      | Códigos WMO interpretados como trovoada com granizo.        |

Os valores são validados na inicialização:

- acumulados e velocidades devem ser positivos;
- a probabilidade deve ficar entre 0 e 100;
- o acumulado condicionado à probabilidade não pode superar o limiar de chuva intensa;
- o limiar de severidade alta do vento não pode ficar abaixo do limiar de vento forte;
- os códigos WMO devem ser informados como lista JSON, por exemplo `[96,99]`.

Uma configuração incoerente interrompe a inicialização com uma mensagem explícita, evitando que
o sistema execute regras inválidas silenciosamente.

Após alterar o `.env`, recrie somente o contêiner — não é necessário reconstruir a imagem:

```bash
docker compose up -d --force-recreate aplicacao
```

## Qualidade

```bash
docker compose exec aplicacao uv run pytest -q
docker compose exec aplicacao uv run ruff check .
docker compose exec aplicacao uv run pyright
```

Resultado de referência: dezenove testes aprovados, Ruff e Pyright sem erros.

## Regras do MVP

### Cadastro de segurados

Use **Novo segurado** na navegação. O formulário solicita nome, e-mail, telefone com DDD, cidade,
UF, apólices e canal preferido. A
aplicação consulta a API de geocodificação do Open-Meteo, escolhe a cidade dentro da UF informada
e armazena latitude e longitude automaticamente. O novo segurado participa das próximas
execuções com previsão real.

O botão **Editar segurado** abre o formulário preenchido para alterar nome, contatos, cidade, UF,
apólices e canal preferido.
Quando cidade ou UF mudam, a geocodificação atualiza automaticamente as coordenadas. O botão
**Excluir segurado** solicita confirmação e realiza exclusão lógica: o segurado deixa de participar
de novas análises, mas o histórico de eventos e notificações é preservado.

No painel, **Excluir todas** remove permanentemente o histórico de execuções, eventos,
verificações meteorológicas e notificações após uma confirmação no navegador. Segurados e
apólices são preservados. A operação é bloqueada enquanto houver uma verificação em andamento.

| Evento        | Regra                                         | Apólices                |
| ------------- | --------------------------------------------- | ------------------------ |
| Chuva intensa | ≥ 50 mm ou ≥ 30 mm com probabilidade ≥ 80% | Residencial e automóvel |
| Vento forte   | Rajada ≥ 75 km/h                             | Residencial e automóvel |
| Granizo       | Código WMO 96 ou 99                          | Automóvel               |

Os valores mostrados são os padrões do `.env` e podem ser ajustados sem alterar o código. São
premissas didáticas, não recomendações operacionais. Os dados iniciais de segurados são fictícios.
WhatsApp pode realizar envio real quando habilitado; nenhuma comunicação promete cobertura.

## Documentação

A fonte meteorológica segue a [documentação do Open-Meteo](https://open-meteo.com/en/docs); os modelos
seguem os catálogos oficiais do [Ollama](https://ollama.com/library/ministral-3/tags) e do
[Groq](https://console.groq.com/docs/models).

O relatório final está disponível em [`docs/relatorio-tecnico.pdf`](docs/relatorio-tecnico.pdf).

## Licença

Este projeto está licenciado sob a licença MIT.

Copyright (c) 2026 Marcelo

É concedida permissão, gratuitamente, a qualquer pessoa que obtenha uma cópia
deste software e dos arquivos de documentação associados, para usar, copiar,
modificar, mesclar, publicar, distribuir, sublicenciar e/ou vender cópias do
software, desde que este aviso de direitos autorais e esta permissão sejam
incluídos em todas as cópias ou partes substanciais do software.

O software é fornecido "como está", sem garantias de qualquer tipo, expressas
ou implícitas. Em nenhuma circunstância os autores ou detentores dos direitos
autorais serão responsáveis por reivindicações, danos ou outras obrigações
decorrentes do software ou de seu uso.

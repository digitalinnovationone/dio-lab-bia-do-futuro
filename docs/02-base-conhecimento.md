# Base de Conhecimento

## Dados Utilizados

| Arquivo | Formato | Utilização no Agente |
|---------|---------|---------------------|
| `perfil_investidor.json` | JSON | Nome e renda mensal do cliente. A renda permite ao agente dimensionar o impacto do PIX suspeito (ex.: R$ 3.500 equivalem a 70% da renda de R$ 5.000). |
| `transacoes.csv` | CSV | Histórico de gastos do cliente. A **mediana das saídas** é usada como valor habitual para detectar PIX fora do padrão. |
| `base_conhecimento_seguranca.json` *(novo)* | JSON | Base do RAG: diretrizes de segurança por tipo de golpe (Falsa Central/Falso Funcionário, conta segura, PIX agendado e comprovante falso, acesso remoto, dados sensíveis e pós-golpe com o MED do Banco Central). |

Os arquivos `historico_atendimento.csv` e `produtos_financeiros.json` fazem parte do template da DIO e **não são utilizados** nesta versão, pois o escopo do agente é segurança contra golpes e ele não recomenda produtos.

---

## Adaptações nos Dados

Os dados do template (`transacoes.csv` e `perfil_investidor.json`) foram mantidos sem alteração e reaproveitados como referência de comportamento do cliente.

Como o histórico não traz atributos de risco, os sinais contextuais da transação em análise são **simulados pela interface** (Streamlit): valor, chave PIX de destino, horário e chamada telefônica ativa. Eles alimentam o motor de risco em tempo real.

Foi criada a `base_conhecimento_seguranca.json`, com descrições dos principais golpes, regras e ações recomendadas, incluindo o **Mecanismo Especial de Devolução (MED)** do Banco Central para PIX ligados a fraude.

---

## Estratégia de Integração

### Como os dados são carregados?

A integração ocorre em duas camadas:

1. **Camada Analítica (Python/Pandas):** ao iniciar, o app lê `perfil_investidor.json` e `transacoes.csv` e calcula o valor habitual do cliente. O motor de risco combina esse padrão com os sinais da transação (valor, chave nova, horário e chamada ativa) e gera um score de 0 a 100 e um nível (baixo, médio ou alto).
2. **Camada de Linguagem (RAG simples):** a `base_conhecimento_seguranca.json` é carregada em memória. A cada mensagem, o agente busca por palavras-chave (texto do cliente + fatores de risco) e recupera as 2 diretrizes mais relevantes; se nada corresponder, usa a orientação geral anti-golpe.

### Como os dados são usados no prompt?

Os dados são consultados dinamicamente e anexados ao **System Prompt** a cada mensagem:

* **System Prompt base:** persona, tom de voz, regras de segurança, técnica de raciocínio e exemplos few-shot (ver `03-prompts.md`).
* **Contexto dinâmico:** dados da transação, score, fatores de risco, renda do cliente e as diretrizes recuperadas (com o campo *Fonte*). O agente deve usar essas informações como base para responder.

### Guardrails aplicados sobre os dados

* **Entrada:** mensagens com tentativa de *Prompt Injection* ou com dados sensíveis (senha, CPF, cartão) são bloqueadas antes de chegar ao modelo.
* **Saída:** respostas que peçam dados sensíveis, autorizem transações ou contenham telefones inventados são substituídas por uma orientação segura da base.

---

## Exemplo de Contexto Montado

```
[SYSTEM PROMPT]
Você é a GuardIA Bradesco, uma assistente virtual especializada em segurança cibernética... (ver 03-prompts.md)

[DADOS DA TRANSAÇÃO]
- Cliente: João Silva
- Valor do PIX: R$ 3500.00
- Renda mensal do cliente: R$ 5000.00 (o PIX equivale a 70% da renda)
- Score de risco: 100/100 (nível alto)
- Fatores de risco: Valor (R$ 3500.00) muito acima do padrão do cliente (habitual: R$ 120.00), Transação em horário noturno atípico, Ligação telefônica ativa detectada no dispositivo, Destinatário recente ou não salvo na agenda

[BASE DE CONHECIMENTO DE SEGURANÇA (RAG)]
- Golpe/tema: Falsa Central / Falso Funcionário
  Regra: O Bradesco não liga pedindo PIX, transferência, PIX de teste, estorno ou 'cancelamento' de compra...
  Ação recomendada: Desligar a chamada, não concluir o PIX e conferir o extrato pelo app oficial...
  Fonte: Orientações públicas de segurança do Bradesco
```

---

## Limitações e Evolução

* A recuperação usa palavras-chave; uma evolução natural é um banco vetorial (ChromaDB/FAISS) com as cartilhas oficiais completas.
* A checagem de "destinatário novo" é simulada pelo prefixo `nova_` na chave; em produção viria do histórico de destinatários do cliente.
* O conteúdo da base de segurança deve ser validado contra as fontes oficiais do Bradesco e do Banco Central antes de qualquer uso real.

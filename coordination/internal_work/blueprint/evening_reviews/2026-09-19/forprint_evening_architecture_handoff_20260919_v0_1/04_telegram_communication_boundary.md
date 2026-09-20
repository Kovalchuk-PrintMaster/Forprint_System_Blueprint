# Telegram Bot Communication Boundary

## Mission

ForPrint Telegram Bot should act as a **personalized communication orchestrator**.

### Owns / coordinates
- conversation identity and state;
- current dialogue context;
- what has already been communicated;
- communication preferences;
- preferred language;
- formality/addressing preference;
- style/verbosity/tone;
- clarification flow;
- intent/style/sentiment classification;
- routing messages to domain modules;
- rendering domain facts into natural language.

### Does not own
- product catalog truth;
- pricing truth;
- accounting truth;
- payment/credit truth;
- logistics truth;
- production truth;
- historical asset truth;
- customer economic analytics;
- durable workflow/process truth.

## Presentation vs facts

The communication layer may change **presentation**, not **facts**.

It may adjust:
- tone;
- structure;
- length;
- formality;
- contextual explanation.

It must not silently alter:
- price;
- quantity;
- deadline;
- status;
- payment requirement;
- delivery fact;
- guarantee;
- domain authority decision.

## Addressing preference

Do not hard-code `ти/ви` from age, gender or job title.

Preferred source order:
1. explicit customer preference;
2. known manager-entered preference;
3. established interaction history;
4. safe neutral default.

## Communication contracts

### Inbound

```text
Human
→ Telegram Bot
→ normalize / classify / clarify
→ structured domain request/event
→ responsible module
```

### Outbound

```text
Responsible module
→ structured communication intent
→ Telegram Bot
→ communication profile + dialogue context
→ natural message
→ Human
```

### Conversation continuity

Repeated notifications must consider prior communication and should not repeat the same template blindly.

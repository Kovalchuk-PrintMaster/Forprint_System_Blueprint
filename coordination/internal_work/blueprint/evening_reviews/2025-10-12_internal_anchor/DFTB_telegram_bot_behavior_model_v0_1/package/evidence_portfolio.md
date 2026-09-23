# Evidence Portfolio — Telegram behavior model / AI escalation / ML evaluation

- Source SHA-256: `6335dcb444643b175483f69c87290967f01b84868161dcf192b4b43b52d4ad0d`
- Evidence records: **32**
- Message blocks: **83**
- Authority: **Telegram module history / non-Blueprint authority**
- Internal chronology anchor: **2025-10-12**
- Turn 1 contains embedded prior dialogue/scaffold and is not treated as fresh direct owner acceptance.

## EV-TG1210B-0001 — turn 1
**Speaker:** user  
**Evidence role:** owner_requirement, behavior_model  
**Confidence:** high

> дам тобі зараз каркас для організації моделі поведінки telegram бота ознайомся з нею і потім дай соє коротке резюме а потім я дам тобі основні критерії поведінки бота щоб ти підготувала якісне наповнення скриптів які будуть моделювати роботу бота відразу передбачила основні можливі додаткові моделі поведінки які я не вкажу але вони цілком ймовірні їх треба буде теж внестив політику роботи бота головний прворітет це грамотна і продумана структура поведінки яка максимально охоплює ті задачі що я тобі надам і всі суміжні аспекти що ти зможеш сама додати даю каркас для початку для аналізу Це якраз той рівень, де бот перестає бути просто “відповідачем” і починає діяти як агент з повед

**Cue:** Owner opens with a request to review a behavior-model scaffold and prepare for later behavior criteria.

---

## EV-TG1210B-0002 — turn 1
**Speaker:** user  
**Evidence role:** embedded_prior_dialogue, chronology_anchor  
**Confidence:** high

> idence: | I want to make sure I respond correctly. Could you rephrase or add more details? meta: version: 0.1 updated: "2025-10-12" author: "Igor Kovalchuk" ✅ Що далі Хочеш, щоб я: Згенерував generate_human_talk.py, який читає цей YAML і формує відповідь? Додав bot_state.yaml, який зберігає фазу розвитку (наприклад: шаблон → генерація → адаптація)? Додав feedback_flow.py, який зберігає реакцію користувача і запускає retrain? Твій бот уже на шляху до справжньої поведінкової системи. Готовий рухатись далі? давай всі 3 фали генеруй я ознайомлюсь з каркасом і подумау як краще рухатисб далі Окей, Ігор — ось три каркасні файли, які задають основу для керування поведінкою, розвитку і фідбеку Telegram-бота. Вони повністю узгоджені між собою і готові

**Cue:** Embedded scaffold contains an internal 2025-10-12 update timestamp.

---

## EV-TG1210B-0003 — turn 1
**Speaker:** user  
**Evidence role:** embedded_prior_dialogue, architecture_context  
**Confidence:** high

> + intent classifier 7 Адаптується до користувача персоналізовані шаблони, стиль, мова 🧩 2. Як це моделювати: bot_behavior_config.yaml Це буде централізований файл, який задає: 🔹 Поведінкові правила yaml intents: 18: # Оплата fallback_style: 12 always_ask: ["номер замовлення", "метод оплати"] confirm: "Підтверджую статус після уточнення" 🔹 Стилі для кожної інтенції yaml styles: polite: emoji: true tone: "мʼякий, ввічливий" aggressive: emoji: false tone: "прямий, вимогливий" 🔹 Fallback-логіка yaml fallback: if_no_template: mistral_generate mistral_prompt: | Respond clearly and warmly to the user intent: {intent_name} Style: {style_name} Sentiment: {sentiment_name} 🧠 3. Мінімальний розвиток: що вже можна зробити ✅ A. Поведінкові фази phase_1: від

**Cue:** Embedded prior dialogue proposes behavior config, bot state and feedback flow scaffolding.

---

## EV-TG1210B-0004 — turn 1
**Speaker:** user  
**Evidence role:** embedded_prior_dialogue, state_model  
**Confidence:** high

> його режим, адаптацію до користувача, і статуси. yaml # bot_state.yaml — поточний стан розвитку Telegram-бота phase: 2 # 1=template, 2=generate, 3=adaptive mode: "production" # або "debug" user_adaptation: enabled: true strategy: "style_personalization" last_style_id: 12 preferred_language: "uk" feedback_tracking: enabled: true last_negative_feedback: "2025-10-10" retrain_triggered: false intent_history: recent_intents: [18, 4, 7] unresolved_intents: [7] meta: updated: "2025-10-12" author: "Igor Kovalchuk" 📥 3. feedback_flow.py Скрипт, який зберігає фідбек користувача, аналізує його, і при потребі запускає retrain або зміну стилю. python # feedback_flow.py — обробка фідбеку користувача для розвитку поведінки бота import json fro

**Cue:** Embedded bot-state scaffold represents behavior phases and user-adaptation/feedback state.

---

## EV-TG1210B-0005 — turn 5
**Speaker:** user  
**Evidence role:** owner_requirement, conversation_quality  
**Confidence:** high

> “Такий сухий діалог не підходить, це має бути більш розвинута система, це має бути дуже потужний бот, у людини, яка спілкується, має бути прямо враження, що вона спілкується з живою людиною. Це основна стратегічна мета, до якої ми будемо йти. Зрозуміло, що вона буде поступово реалізовуватися, спочатку вона буде у нас вчитися, буде примітивні якісь робити перші кроки, але головна мета – це вийти на рівень, який буде доволі потужний. Зараз пишеться БКН для цього бота, і ми вже наповнюємо деберту, базу даних, щоб бот знав, які взагалі приходять запити, стиль комунікації налаштовують, буде підключено, щоб він розумів агресивні, не агресивні стилі, дам йому інформацію за декілька, можливо, півроку роботи друкарні, які запити приходили, і як живі люди, живі менеджери відповідали на ці запити для аналізу. І підключаємо зараз ще паралельно Містраль, щоб трошки додавати, оживити дискусію або діал

**Cue:** Owner says the bot should feel like a powerful live human interlocutor, not a dry scripted responder.

---

## EV-TG1210B-0006 — turn 9
**Speaker:** user  
**Evidence role:** owner_process_rule, information_capture  
**Confidence:** high

> “Так, продовжуємо, але поки що тільки коротко підтверджуй мені, що ти прийняла інформацію, і я буду переходити до наступних блоків. Поки що ніякий там аналіз чи ще чогось, рекомендації давати не треба. Тільки якщо дійсно щось тобі дуже сильно не зрозуміло з того, що я скажу, то тоді можеш перепитати. А так, максимальний режим тиші, тільки короткі підтвердження, що інформацію зрозуміла і там готова далі до наступного блоку.”

**Cue:** Owner temporarily asks the assistant only to confirm receipt while he provides behavior information.

---

## EV-TG1210B-0007 — turn 13
**Speaker:** user  
**Evidence role:** owner_requirement, client_identity  
**Confidence:** high

> ні щось там в чаті, я не можу зрозуміти, чи пропало з повіщення, чи запам'ятала ти інформацію про директорію, номер телефону клієнта, навіщо це треба? Чи є в тебе це в твоїй базі?”

**Cue:** Owner checks that the phone-number/client-directory rationale was retained.

---

## EV-TG1210B-0008 — turn 19
**Speaker:** user  
**Evidence role:** owner_process_rule, voice_text_sync  
**Confidence:** high

> “Так, дивись, я все-таки в чаті поки що не бачу тієї інформації, що я тобі передаю. І хочу переконатися, що ти дійсно всю інформацію прийняла. Зроби зараз прямо в чат тезис, тільки щоб для тебе було зрозуміло. Мені не важливо, як там буде написано. Для себе такий чек-лист, задачу тих, які ми можемо вирішувати, виходячи з тієї ситуації, це інформація, яку я тобі вже передав. Я побачу, що з'явився такий чек-лист, з'явилась інформація з тезисами, що треба зробити, коротко їх дуже швиденько оціню, чи там є все, про що я балакав, і далі почнемо рухатися далі. Я хочу, щоб ми чітко розуміли, що нічого не втрачається з нашою живою розмовою.”

**Cue:** Owner asks for a compact in-chat checklist of what was just communicated so he can verify synchronization.

---

## EV-TG1210B-0009 — turn 39
**Speaker:** user  
**Evidence role:** owner_requirement, order_dialogue  
**Confidence:** high

> м'ятаєш, голосовий помічник, про те, як має поводити себе бот при оформленні замовлення. Що розрізняти, чи це одна пачка, чи ціла упаковка з декількох пачок. Ти ж пам'ятаєш цю інформацію? Підтвердь мені. Дякую.”

**Cue:** Owner references a concrete order-handling rule: distinguish one pack/item from a larger package containing multiple packs.

---

## EV-TG1210B-0010 — turn 41
**Speaker:** user  
**Evidence role:** owner_requirement, voice_text_sync  
**Confidence:** high

> “Супер, дивись. Але я не можу від тебе добитися, щоби оцю останню розмову ти вивела в чат тезисно, щоб я бачив наглядно, про що ми говорили. Бо ти пам'ятаєш це собі в пам'яті, а я собі, мені має бути шпрегалка, я хочу, щоб після того, як у нас відбулася голосова розмова, я виходжу з голосового чату, закриваю хрестиком, заходжу в чат, кажу тобі, дай мені короткий звіт, і ти мені даєш звіт по тому, що ми проговорили. І я сам собі розумію, яку інформацію я тобі вже надав, наприклад, завтра згадати, про що ми балакали. А добитися від тебе оцього звіту мені дуже важко. Як нам організувати роботу, щоб інформацію, яку я тобі передаю голосом, щоб ти мені її правильно адаптувала і перекидувала на устний чат звітом? Що мені зробити до цього?”

**Cue:** Owner explains that post-voice text summaries are needed as a personal visible memory/checklist.

---

## EV-TG1210B-0011 — turn 43
**Speaker:** user  
**Evidence role:** owner_decision, voice_text_sync  
**Confidence:** high

> но за оцю розмову. Не треба робити звід за всі усні діалоги, за останніх дві години, що у нас були. Не треба. Тільки останній в списку. У тебе є останній в списку діалог усний, і ти його в останній в списку акуратно підсумувала. Окей?”

**Cue:** Owner requires summaries to cover only the exact latest voice dialogue, not a broad time window.

---

## EV-TG1210B-0012 — turn 48
**Speaker:** user  
**Evidence role:** owner_requirement, ai_escalation  
**Confidence:** high

> ry important to note that when the bot sees that it cannot make the right, unambiguous decision, it must have two options for further steps. The first step is to turn to the mentor, if the mentor responds in general, or to call artificial intelligence. We must assume that the bot must be integrated with artificial intelligence, for example, with the chatGPT assistant. And when there is a question that cannot be solved, the bot responds to you and you get all the information from it, by order, access to the database, and you try to solve the problem together. Did you understand the task I gave you?”

**Cue:** Owner requires two escalation paths when the bot cannot make a clear decision: Mentor or AI.

---

## EV-TG1210B-0013 — turn 48
**Speaker:** user  
**Evidence role:** owner_requirement, ai_escalation  
**Confidence:** high

> a question that cannot be solved, the bot responds to you and you get all the information from it, by order, access to the database, and you try to solve the problem together. Did you understand the task I gave you?”

**Cue:** Owner expects escalation context to include relevant dialogue/order/database information.

---

## EV-TG1210B-0014 — turn 59
**Speaker:** user  
**Evidence role:** owner_question, tool_execution  
**Confidence:** high

> ргу цікавить, як, ну, по-перше, яка задача. АІ, ну, ти або інші АІ, ви не можете на тему мати доступ до, там, Google Дисків взагалі, якихось файлової системи комп'ютера, ну, або взагалі до чого-небудь такого, що виходить за рамки чатки. Але, наскільки я знаю, то через інструмент TelegramBot, ви можете, якщо вас підключити, законектити, напряму під'єднати, то ви можете виконувати його руками практично всі маніпуляції, мінімум, з хмарними середовищами і з тими ресурсами, які є на комп'ютері. Я правильно розумію цю реалізацію?”

**Cue:** Owner asks whether a Telegram bot can serve as the execution bridge giving AI controlled access to external/cloud/computer resources.

---

## EV-TG1210B-0015 — turn 61
**Speaker:** user  
**Evidence role:** owner_requirement, personal_assistant  
**Confidence:** high

> у добре, одного їх, там певно, щоб декілька були цих телеграм-ботів, і як мінімум ціль одного з них – це бути особистим асистентом. Я, наприклад, даю там якісь задачі, ну конкретні, перевір пошту, і скажи мені, від кого є які листи. Перевіряється пошта, дається мені інформація, які листи, який контекст тих листів, я кажу, що треба відповісти по кожному, бо у нас є проговорений алгоритм роботи по відповіді на ці листи. І ботам, або власними силами, якщо може розібратися, відповідає, або підключає AI, і те саме робот відповідає, або там копіює якісь файли на комп'ютер, далі їх якось обробляє, можливо це прайси, чи що, редагує, потім загружає знову через пошту, відправляє там клієнтам. От такий асистент мені треба, і я так розумію, що Telegram

**Cue:** Owner defines a personal-assistant use case involving email review/replies and file manipulation with AI assistance when needed.

---

## EV-TG1210B-0016 — turn 63
**Speaker:** user  
**Evidence role:** owner_question, runtime_reasoning  
**Confidence:** high

> ння, я взагалі не розумію, ну якщо там, наприклад, з AI мені ще зрозуміло, то мені не зрозуміло, чи є взагалі якісь інструменти передбачені розвитку, чи є якийсь взагалі модель мислення у бота, просто відрождення, тому що, ну добре, я зараз розробляю цього бота, ми зробимо для нього купу-купу всього корисного, моделі поведінки, наповнимо діалогами базу знань, щоб він розумів демоконтекст, там всю-всю-всю інформацію, щоб він міг виконувати такі рутинні прості задачі, ми це все йому дамо. Але мене цікавить, чи є в нього взагалі якісь коробки або передбачені, можливо, інтеграційно, окрім як AI, якісь інструменти, які йому додають трохи логіки більше, коли він бачить запит, наприклад, приходить, якийсь на нього там запит від клієнта, він обучений по всьому, по п

**Cue:** Owner asks how a deterministic bot can reason beyond pre-scripted scenarios and what logic layers exist besides AI.

---

## EV-TG1210B-0017 — turn 65
**Speaker:** user  
**Evidence role:** owner_decision, runtime_reasoning  
**Confidence:** high

> “Я зрозумів. Сам по собі бот без AI – це такий собі дуже потужний телькулятор. Тобто ти вводиш якісь комбінації чисел, і він просто віддає тобі правильний результат. Я так розумію, що це і є бот. Якщо я хочу трошки глибше, якщо я хочу якоїсь аналітики питання, то я маю активувати, як ти кажеш, цей прошарок з AI. І далі AI мені дає корисну і правильну інформацію по аналізу.”

**Cue:** Owner summarizes his model: deterministic bot logic handles defined procedures, AI is the deeper analytic/reasoning layer.

---

## EV-TG1210B-0018 — turn 67
**Speaker:** user  
**Evidence role:** owner_requirement, 1c_automation  
**Confidence:** high

> м забезпеченням, і я думаю, що якщо з міжнародними пакетами простіше, то мене цікавий такий пакет, як 1С, ну, 1С-бухгалтерія. Чи є взагалі якийсь, наприклад, напрацювання в інтернеті, можливо, якісь бібліотеки, можливо, якісь, або вже прописані інструменти. Я хочу, щоб бот створював замовлення паралельно, приймав замовлення від клієнта, відкривав 1С, ну, або не відкривав її, туди підключався до 1С, і робив там, створював замовлення, списував матеріал, щоб він виконував таку дрібну механічну роботу. Наскільки це взагалі реалізуємо, і наскільки це взагалі описано в інтернеті, наскільки це легко, які є проблеми чи багисти? Скажи мені, будь ласка.”

**Cue:** Owner wants the bot to eventually perform routine 1C/accounting-system procedures such as creating orders or material actions.

---

## EV-TG1210B-0019 — turn 68
**Speaker:** assistant  
**Evidence role:** assistant_recommendation, 1c_automation  
**Confidence:** high

> ької системи — це реально можливо, але треба врахувати кілька нюансів. Перше, що тобі потрібно знати: існують API і бібліотеки, які дозволяють взаємодіяти з 1С віддалено. Є певні готові рішення, і в інтернеті можна знайти деякі напрацювання. Але одразу скажу, що це може бути трохи специфічно, бо 1С — це така система, яка має свої версії, свої нюанси, і доведеться трохи покопатися. Якщо коротко, то так: ти можеш знайти бібліотеки або API-інтеграції, які дозволять боту виконувати стандартні дії в 1С (наприклад, створювати замовлення, додавати матеріали, оновлювати записи). Це не щось надзвичайне, але вимагатиме трохи часу на налаштування. Зазвичай це працює так: бот отримує запит, через API звертається до 1С, передає необхідн

**Cue:** Assistant says 1C integration is possible via APIs/libraries but depends on version/security/access details.

---

## EV-TG1210B-0020 — turn 73
**Speaker:** user  
**Evidence role:** owner_requirement, repository_knowledge  
**Confidence:** high

> “Так, слухай, давай пройдемося коротко по тій файловій структурі, яку я тобі передав як приказ. Розкажи мені, що ти думаєш і за що, який файл відповідає, і яке наповнення очікує. Дай мені такий короткий анализ.”

**Cue:** Owner asks to inspect the bot skeleton/file structure already supplied in chat.

---

## EV-TG1210B-0021 — turn 98
**Speaker:** assistant  
**Evidence role:** assistant_limit, continuity_failure  
**Confidence:** high

> Зрозуміло, на жаль, я не можу безпосередньо переглядати історію чату або шукати файли. Якщо є якась конкретна назва або деталі, які ви пам’ятаєте, просто повідомте мені, і ми зможемо далі розібратися. Я завжди готова допомогти!

**Cue:** Assistant eventually admits it cannot reliably retrieve the requested historic file name from chat context.

---

## EV-TG1210B-0022 — turn 101
**Speaker:** user  
**Evidence role:** owner_architecture, runtime_stack  
**Confidence:** high

> t. I'm interested in another question. We are creating a chatbot, a Telegram chatbot. The chatbot is based on three things globally. The first thing is that it has a de-berth connected to it. Now we are teaching it intent, style, and sentiment. And Mistral Sync will be connected to it. For better dialogue, which we will soon start teaching. And the third tool is AI, maybe GPT, which will be connected in difficult conditions, when the bot will not understand what to do and what decisions to make on their own. I want to ask you such questions. We are teaching de-berth, classify the input stream, as by intent, by style. I understand that these tools will be used in the future. We have a table for this. But I want the bot to have sales skills. B

**Cue:** Owner summarizes the intended stack as DeBERTa classification + Mistral dialogue generation + AI escalation for difficult decisions.

---

## EV-TG1210B-0023 — turn 101
**Speaker:** user  
**Evidence role:** owner_requirement, sales_dialogue  
**Confidence:** high

> understand that these tools will be used in the future. We have a table for this. But I want the bot to have sales skills. Because it will be a bot-manager for processing customers. And I want it not only to be able to take requests, but also to generate sales dialogues. Or to push the product, to push the service. How can this be realized? Can it be connected? I understand that giving sales examples, to fill this table with dialogues, does not make sense. Because it will be very difficult to filter. I don't think it can be practically realized. Can you connect a few more tables? For example, the sales table, or the processing of customer objections. And fill these tables with real examples, so that the bot can refer to these examp

**Cue:** Owner wants the bot-manager to actively support sales and objection handling, not only accept requests.

---

## EV-TG1210B-0024 — turn 103
**Speaker:** user  
**Evidence role:** owner_requirement, intent_taxonomy  
**Confidence:** high

> то це відноситься, в першу чергу, до бази даних інтенту в деберті. Тобто в інтенті має мати такі чинники, як продаж, відмова або можливість запротонування продажу. Тобто мають бути такі поля в інтент, і потім, коли знаходиться щось подібне, то вже потім логіка спрацьовує на ці інтент-поля і звідти йде вибірка. Я правильно зрозумію? Мені треба, щоб це було в інтент.”

**Cue:** Owner expects sales/refusal/objection concepts to be represented in intent classification or downstream routing logic.

---

## EV-TG1210B-0025 — turn 105
**Speaker:** user  
**Evidence role:** owner_decision, training_data_architecture  
**Confidence:** high

> ts are written there. DeBerti classifies them. We create additional intents that we need. We are now creating several tables in parallel. For example, a table of sales, a table of processing of orders, a table of orders received, a table of orders put into operation. When we see that our DeBerti does not work, for example, it does not work in the processing of orders, it is confused, it cannot classify different goods. And we do not fill the entire table, because we renew everything, but only work with a table that corresponds to the processing of goods. We fill it with real dialogues, real stylistic phrases, so that the bot learns. And then we either teach the bot or re-train it. But at the same time, when it is trained, it must process several

**Cue:** Owner prefers multiple specialized datasets/tables rather than one giant training table.

---

## EV-TG1210B-0026 — turn 105
**Speaker:** user  
**Evidence role:** owner_requirement, continuous_learning  
**Confidence:** high

> difficult. It will be necessary to filter and make selections. For example, we have a table of dialogues. All real dialogues with clients are written there. DeBerti classifies them. We create additional intents that we need. We are now creating several tables in parallel. For example, a table of sales, a table of processing of orders, a table of orders received, a table of orders put into operation. When we see that our DeBerti does not work, for example, it does not work in the processing of orders, it is confused, it cannot classify different goods. And we do not fill the entire table, because we renew everything, but only work with a table that corresponds to the processing of goods. We fill it with real dialogues, real stylistic p

**Cue:** Owner wants weak domains improved by adding real examples specifically to the relevant specialized dataset.

---

## EV-TG1210B-0027 — turn 107
**Speaker:** user  
**Evidence role:** owner_requirement, ml_quality  
**Confidence:** high

> е питання. Значить, у нас є, наприклад, навчена модель. Мені просто не дуже зрозумілий алгоритм, як ми можемо автоматизувати тестування, наприклад, моделі, де берти умовно раз на місяць, раз на портал, щоб розуміти, де вона помиляється, де вона не точно розпізнає контекст, не точно його класифікує, щоб її донавчити. І, по-перше, як взагалі автоматично можна цей процес на навченій моделі запускати, чи не буде він, скажімо так, поміжувати її загальний рівень знань. І хто може реально так прокласифікувати, яким інструментом можна, наприклад, оцінити автоматично, що дійсно де берта класифікує або правильно, або дуже сильно помиляється, як ми назначаємо відсоток помилок, 20 відсотків, це вже треба її донавчати. Як це реалізується професійно?”

**Cue:** Owner asks for periodic automated classifier evaluation, error thresholds and targeted retraining.

---

## EV-TG1210B-0028 — turn 109
**Speaker:** user  
**Evidence role:** owner_requirement, ml_quality  
**Confidence:** high

> облю такий тестувальний датасет і буду його запускати автоматично, то через деякий час Deberta точно до нього адаптується і точно буде проходити саме цей конкретний датасет на успішну. І все, і все тестування далі немає ніякого сенсу, наприклад, через півроку. А я собі сижу і думаю, що у мене там модель проходить тестування, донавчається, все-все добре. А вона просто вже цей датасет вивчила і не рухається далі. От в цьому саме велика і питання, чи є якісь інструменти, можливо якісь зовнішні ресурси, можливо якісь спеціальні сервіси, які генерують, наприклад, по деякій тематиці нові спеціалізовані запити, підкидуючи їх, наприклад, в мою якусь там… Ну я там до когось звертаюся по АПІ, чи я там загружаю якийсь там рандомний знову набі

**Cue:** Owner identifies test-set memorization as a failure mode and rejects a static evaluation dataset as long-term evidence.

---

## EV-TG1210B-0029 — turn 109
**Speaker:** user  
**Evidence role:** owner_requirement, dynamic_evaluation  
**Confidence:** high

> ей, і воно автоматично підгружається у цю таблицю тест, таблиця тестування. І Деберта кожен раз тестується на новому датасеті. Я от про це кажу, тому що просто з стандартним набором даних, ну то взагалі не годиться.”

**Cue:** Owner asks for dynamic/external generation of fresh unseen test requests for recurring evaluation.

---

## EV-TG1210B-0030 — turn 111
**Speaker:** user  
**Evidence role:** owner_decision, dynamic_evaluation  
**Confidence:** high

> “Добре, давай розглянемо на практиці. Третій варіант точно мені не підходить. Перші два варіанти, які ти вважаєш більш-ліпші для автоматичної роботи без участі людини. І давай його розберемо прямо покроково, на пальцях. Тобто, який сервіс ти пропонуєш, як ми до нього підключаємося, що нам для цього треба, скільки це коштує, чи є безкоштовні сервіси, чи є trial версії якісь. І які таблиці ми створюємо в базі. Розкажи мені в загальних, але відносно чітких кроках суть роботи, як це відбувається.”

**Cue:** Owner rejects simple rotation-only test sets and prefers the more automated fresh-generation options.

---

## EV-TG1210B-0031 — turn 112
**Speaker:** assistant  
**Evidence role:** assistant_recommendation, external_dependency  
**Confidence:** high

> можливість генерувати нові запити на основі твоїх тем. Наприклад, деякі API від постачальників LLM (на кшталт OpenAI або інших подібних сервісів) дозволяють генерувати випадкові запити з певної тематики. Ти можеш подивитися на їхні API-документації, там є безкоштовні рівні використання або пробні версії, які дають змогу спробувати це без зайвих витрат. Другий крок: підключення до API. Тобі потрібно зареєструватися на такому сервісі, отримати API-ключ і налаштувати свій скрипт або програму, щоб вона періодично зверталася до цього API. Наприклад, раз на місяць твій скрипт робить запит: "Згенеруй мені 100 нових тестових запитів на тему поліграфії чи продажів". API повертає тобі ці запити. Третій крок: збереження нових тестових да

**Cue:** Assistant suggests an LLM/API service as one possible generator of fresh evaluation examples.

---

## EV-TG1210B-0032 — turn 112
**Speaker:** assistant  
**Evidence role:** assistant_recommendation, dynamic_evaluation  
**Confidence:** high

> мати API-ключ і налаштувати свій скрипт або програму, щоб вона періодично зверталася до цього API. Наприклад, раз на місяць твій скрипт робить запит: "Згенеруй мені 100 нових тестових запитів на тему поліграфії чи продажів". API повертає тобі ці запити. Третій крок: збереження нових тестових даних. Ти просто додаєш ці нові приклади в окрему тестову таблицю в базі даних. Наприклад, кожен новий набір додається в окремий "пул", і коли ти запускаєш тестування, воно просто бере свіжий набір з цієї таблиці. Четвертий крок: автоматизація цього процесу. Ти налаштовуєш це як регулярне завдання — наприклад, за допомогою крону чи іншого планувальника завдань. І кожен місяць або квартал у тебе автоматично оновлюється тестовий набір. Що до витрат

**Cue:** Assistant outlines scheduled API generation of fresh test pools and recurring model evaluation.

---

# саенс арт не реже раза в неделю

_Ссылка на канал: https://t.me/science_art_at_least_once_a_week_

Привет и добро пожаловать!

**Что это за канал?**

Как следует из названия, сюда периодически будут выкладываться случайные работы из архива фестиваля Ars Electronica. Постинг полностью автоматизирован

**Зачем это всё?**

Локально: успешное познание — это заслуга инфраструктуры, а не мотивации. Поэтому мне кажется важным внести вклад в создание этой инфраструктуры. А ещё мне нравится играть с идеями админского ви́дения, эрудиции и вовлечённости. Я ведь не видел большинства работ, которые будут опубликованы, да и скорее не делюсь ими, но открываю их вместе с вами

Глобально: формирование любого художественного канона — это политизированный процесс, несущий на себе клеймо различных систем угнетения. [Вот](https://syg.ma/@ekaterina-zakharkiv/ursula-k-lie-guin-ischiezaiushchiie-babushki) пронзительное эссе Урсулы Ле Гуин про литературу, а [вот](https://deweyhagborg.com/projects/kissmyars) — мощное высказывание биохудожницы Heather Dewey-Hagborg о современном технологическом искусстве. Мне кажется, техногенная случайность — это один из способов сопротивления инерции этого процесса, один из способов задуматься, почему мы называем классиками тех, кого мы называем классиками

**Как это работает?**

Если вкратце, то я:
1. Собрал данные о работах с [сайта](https://archive.aec.at/prix/) архива Ars Electronica при помощи [парсера](https://github.com/andreygetmanov/ars_electronica_parser) (категории — Интерактивное искусство и AI-искусство)
2. Перевёл описания работ при помощи [Google Translate API](https://cloud.google.com/translate)
3. Написал скрипт для постинга через [Телеграм-бота](https://core.telegram.org/bots/api)
4. Запустил его на удалённом сервере и установил расписание запуска

**Благодарности**

[Github Copilot](https://github.com/features/copilot) и [ChatGPT](http://chat.openai.com/) внесли неоценимый вклад в проект, на всех этапах работы помогая мне в написании кода и решении технических сложностей

**Исходный код**

Открыт и доступен (лицензия GPL3). Буду рад вашим звёздочкам!

**Вопросы и предложения**

Пишите сюда: [@AGet_man_off](https://t.me/AGet_man_off)

**Дальнейшие планы**

Обязательно расширю список категорий работ
А ещё я планирую интеграцию с ChatGPT. Как именно — скоро узнаете!
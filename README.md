# Ogon_AI_Hackathons

## Информация для экспертов хакатона

*Название команды – **1С PRO**

*Название проекта – **Помощник менеджера проектов**

*Ссылка на рабочее приложение – **https://t.me/vgn_io_test_bot** (хостинг медленный, бот отвечает очень долго (4-5 минут),если вдруг бот не отвечает, сообщите пожалуйста https://t.me/a_vgn_peston так как все вертится на домашнем компьютере)

*Ссылка на presentation.pdf - **https://docs.google.com/presentation/d/1XjFjO2hjHO3T-s3dLO7st0HcCiXobTvpBOQD0WbbkvU/edit?usp=sharing**

*Ссылка на видео-демо - **https://disk.yandex.com/d/ZsXAkhHifOwUlg**

*Участники команды **Ваганов Алексей и Дмитрий Гришаев**

**History**
Основной целью хакатона было погружение в технологию MCP: разобраться в архитектуре, создании серверов, настройке, подготовке основы для дальнейшего использования.
Погрузившись в технологию, мы поняли, что можем найти её применение в разрабатываемом нами продукте «Помощник менеджера проекта».
В рамках хакатона была выполнена работа по созданию телеграм бота, хоста MCP и интеграция с сервером MCP для интеграции с Open Project.
Как сервер использовалась сторонняя разработка: https://github.com/jessebautista/mcp-openproject?ysclid=mbp5d3z8g6142178764



## Информация для членов команды

Проект выполнен в рамках Хакатона Ogon.AI Hackathons, а также для тестирования mcp

Установите предварительно:
- Ollama. Модель укажите в файле - mcp_agent_core.py в процедуре - query_ollama
- OpenProject. Для тестирования рекомендуется устанавливать в docker (информация укзана ниже)
Проект включает в себя:

Описание модулей:
- math_server.py Сервер mcp для сложения двух чисел. Старт python math_server.py
- qa_server.py Сервер mcp для получения произвольных ответов от Ollama. Старт python qa_server.py
- time_server.py Сервер mcp для получения текущего времени. Старт python time_server.py
- папка mcp_openproject. MCP сервер OpenProject- для запуска воспользоваться инструкцией https://github.com/jessebautista/mcp-openproject?ysclid=mbp5d3z8g6142178764
Для запуска сервера MCP OPENPROJECT зайти в папку и запустить netlify dev
- telegram_bot.py телеграм бот для обращения к хосту mpc
- mcp_agent_core.py - хост (ядро) mcp 
Для старта - uvicorn mcp_agent_core:app --host 0.0.0.0 --port 8000
обратиться к серверу curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"user_input": "сложи 3 и 6"}'
- client_test.py - скрипт для теста доступа к серверу mcp
- config.py - формат записи доступов к серверам mcp
- tools.py - разбор ответа от сервера mcp


УСТАНОВКА OPENPROJECT

👉 https://www.docker.com/products/docker-desktop/ Нажми кнопку Download для macOS.

✅ Шаг: Установи Docker Desktop
После загрузки ты получишь .dmg файл (например, Docker.dmg).
Открой этот файл — просто дважды кликни по нему.
Перетащи значок Docker в папку Applications.
Перейди в папку Applications и запусти приложение Docker (двойной клик).
✅ Шаг: Запусти Docker
При первом запуске система может запросить разрешение на использование некоторых функций (сетевой доступ, диск и т.д.) — подтверди всё.
В правом верхнем углу экрана появится значок 🐳 (Docker). Подожди, пока он завершит инициализацию (может занять пару минут).
✅ Шаг: Проверь установку
Открой Terminal и выполни команду:

bash
docker --version
получаешь ошибку:
zsh: command not found: docker
— это означает, что утилиты Docker (docker CLI) не добавлены в PATH или не установлены должным образом.

Вот как можно исправить эту проблему:
🔧 Шаг 1. Проверь, запущен ли Docker Desktop
Открой приложение Docker Desktop и дождись, пока появится надпись:
"Docker Desktop is now up and running!" 
Или посмотри на значок 🐳 в правом верхнем углу — он должен быть активным.
🔧 Шаг 2. Убедись, что docker доступен в терминале
Попробуй запустить:
bash
1
/Applications/Docker.app/Contents/Resources/bin/docker --version
Если это сработало — значит, бинарный файл есть, но он не добавлен в PATH.
✅ Шаг 3. Добавь docker в системный PATH
Выполни следующую команду в терминале:
bash
ln -s /Applications/Docker.app/Contents/Resources/bin/docker /usr/local/bin/docker
Теперь команда docker будет доступна глобально.

🔄 Шаг 4. Перезапусти терминал
Закрой и снова открой терминал, затем проверь:

bash
docker --version
Должно вывести версию Docker, например:
Docker version 24.0.5, build ced0996
🧪 Шаг 5. Проверь подключение к демону Docker
bash
docker info
или
bash
docker run hello-world
Если всё работает — всё готово!
дальше запустить https://www.openproject.org/docs/installation-and-operations/installation/docker/
в консоли

docker run -it -p 8085:80 \
  -e OPENPROJECT_SECRET_KEY_BASE=secret \
  -e OPENPROJECT_HOST__NAME=localhost:8085 \
  -e OPENPROJECT_HTTPS=false \
  -e OPENPROJECT_DEFAULT__LANGUAGE=ru \
  openproject/openproject:16

первый раз зайти admin admin потом поменять пароль

ЗАПУСК MCP OPENPROJECT

Local Development

Create Environment File:

Create a file named .env in the project root.
Add your OpenProject details:
OPENPROJECT_API_KEY="your_openproject_api_key_here"
OPENPROJECT_URL="https://your_openproject_instance.com"
OPENPROJECT_API_VERSION="v3"
(Important): Ensure .env is listed in your .gitignore file to avoid committing secrets.
Run Netlify Dev Server:

This command starts a local server, loads variables from .env, and makes your function available.
netlify dev
Your local MCP endpoint will typically be available at http://localhost:8888/mcp.
Test Locally with MCP Inspector:

In a separate terminal, run the MCP Inspector, pointing it to your local server via mcp-remote:
npx @modelcontextprotocol/inspector npx mcp-remote@next http://localhost:8888/mcp
Open the Inspector URL (usually http://localhost:6274) in your browser.
Connect and use the "Tools" tab to test the OpenProject CRUD operations.


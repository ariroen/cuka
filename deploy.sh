#!/bin/bash

# =============================================================================
# Контракт-61: Диспетчер - Автодеплой скрипт
# Автоматическая установка и запуск проекта на сервере
# =============================================================================

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   Контракт-61: Диспетчер - Автодеплой${NC}"
echo -e "${BLUE}=================================================${NC}"

# Проверка прав суперпользователя
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Запустите скрипт от имени root (sudo bash deploy.sh)${NC}"
    exit 1
fi

# Конфигурация
PROJECT_DIR="/opt/contract61-dispatcher"
ENV_FILE="$PROJECT_DIR/.env"
DOCKER_COMPOSE_VERSION="v2.24.5"

echo -e "\n${YELLOW}[1/8] Обновление пакетов...${NC}"
apt-get update -qq

echo -e "\n${YELLOW}[2/8] Установка зависимостей (git, curl, docker.io)...${NC}"
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq git curl docker.io > /dev/null 2>&1

# Проверка и установка Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}[3/8] Установка Docker Compose...${NC}"
    curl -sL "https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
else
    echo -e "${GREEN}[3/8] Docker Compose уже установлен${NC}"
fi

# Создание директории проекта
echo -e "\n${YELLOW}[4/8] Создание директории проекта...${NC}"
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Клонирование репозитория (если не существует)
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}[5/8] Клонирование репозитория...${NC}"
    # Замените URL на ваш реальный репозиторий
    git clone https://github.com/YOUR_USERNAME/contract61-dispatcher.git . 2>/dev/null || {
        echo -e "${YELLOW}Репозиторий не найден. Используем локальные файлы...${NC}"
        # Если скрипт запущен изнутри проекта, файлы уже здесь
        if [ ! -f "docker-compose.yml" ]; then
            echo -e "${RED}Ошибка: Файлы проекта не найдены в $PROJECT_DIR${NC}"
            exit 1
        fi
    }
else
    echo -e "${GREEN}[5/8] Репозиторий уже клонирован${NC}"
    # Обновление кода
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || true
fi

# Создание .env файла
echo -e "\n${YELLOW}[6/8] Настройка переменных окружения...${NC}"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << EOF
# Токен бота от @BotFather
BOT_TOKEN=YOUR_BOT_TOKEN_HERE

# API ключ Groq (получить на console.groq.com)
GROQ_API_KEY=YOUR_GROQ_API_KEY_HERE

# ID администраторов (через запятую, опционально)
ADMIN_IDS=

# Часовой пояс
TZ=Europe/Moscow

# Порт для веб-сервера (опционально)
WEB_PORT=8000
EOF
    echo -e "${YELLOW}Создан файл .env. ОТРЕДАКТИРУЙТЕ ЕГО ПЕРЕД ЗАПУСКОМ!${NC}"
    echo -e "${YELLOW}Команда: nano $ENV_FILE${NC}"
else
    echo -e "${GREEN}[6/8] Файл .env уже существует${NC}"
fi

# Проверка наличия обязательных переменных
if grep -q "YOUR_BOT_TOKEN_HERE" "$ENV_FILE" || grep -q "YOUR_GROQ_API_KEY_HERE" "$ENV_FILE"; then
    echo -e "\n${RED}⚠️  ВНИМАНИЕ: Замените значения по умолчанию в $ENV_FILE${NC}"
    echo -e "${YELLOW}Откройте файл и укажите:${NC}"
    echo -e "  - BOT_TOKEN (получить в @BotFather)"
    echo -e "  - GROQ_API_KEY (получить на console.groq.com)"
    echo -e "\n${YELLOW}Продолжить установку? (y/n)${NC}"
    read -r response
    if [[ "$response" != "y" ]]; then
        echo -e "${RED}Установка прервана. Отредактируйте $ENV_FILE и запустите скрипт снова.${NC}"
        exit 1
    fi
fi

# Сборка и запуск контейнеров
echo -e "\n${YELLOW}[7/8] Сборка Docker образов...${NC}"
docker compose build --no-cache

echo -e "\n${YELLOW}[8/8] Запуск сервисов...${NC}"
docker compose up -d

# Проверка статуса
sleep 5
echo -e "\n${GREEN}=================================================${NC}"
echo -e "${GREEN}   ✅ Установка завершена успешно!${NC}"
echo -e "${GREEN}=================================================${NC}"

# Вывод статуса контейнеров
echo -e "\n${BLUE}Статус сервисов:${NC}"
docker compose ps

# Инструкция
cat << EOF

${GREEN}📋 СЛЕДУЮЩИЕ ШАГИ:${NC}

1. ${YELLOW}Отредактируйте конфиг:${NC}
   nano $ENV_FILE
   
   Укажите реальные значения:
   - BOT_TOKEN (от @BotFather)
   - GROQ_API_KEY (от Groq)

2. ${YELLOW}Перезапустите бота после настройки:${NC}
   cd $PROJECT_DIR
   docker compose restart

3. ${YELLOW}Просмотр логов:${NC}
   docker compose logs -f bot

4. ${YELLOW}Остановка сервиса:${NC}
   docker compose down

5. ${YELLOW}Обновление кода:${NC}
   cd $PROJECT_DIR
   git pull
   docker compose up -d --build

${BLUE}📍 Директория проекта: $PROJECT_DIR${NC}
${BLUE}🔗 Документация: $PROJECT_DIR/README.md${NC}

${GREEN}🚀 Бот готов к работе!${NC}
EOF

# Добавление в автозагрузку
echo -e "\n${YELLOW}Настройка автозапуска при перезагрузке системы...${NC}"
if ! systemctl is-enabled docker.service > /dev/null 2>&1; then
    systemctl enable docker.service
    systemctl start docker.service
fi

# Создание systemd сервиса (опционально, для управления через systemctl)
cat > /etc/systemd/system/contract61-dispatcher.service << EOF
[Unit]
Description=Contract-61 Dispatcher Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/docker compose up -d
ExecStop=/usr/local/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable contract61-dispatcher.service

echo -e "${GREEN}✅ Сервис добавлен в автозагрузку${NC}"
echo -e "${YELLOW}Управление: systemctl start|stop|status contract61-dispatcher${NC}"

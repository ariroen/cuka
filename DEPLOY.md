# 🚀 Автодеплой «Контракт-61: Диспетчер»

## Быстрый старт на сервере

### Одна команда для полной установки:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/contract61-dispatcher/main/deploy.sh | sudo bash
```

Или если вы уже скачали проект:

```bash
sudo bash deploy.sh
```

---

## 📋 Что делает скрипт автоматически:

1. ✅ Обновляет пакеты системы
2. ✅ Устанавливает Docker и Docker Compose
3. ✅ Клонирует репозиторий в `/opt/contract61-dispatcher`
4. ✅ Создает шаблон `.env` файла
5. ✅ Собирает Docker образы
6. ✅ Запускает контейнеры
7. ✅ Настраивает автозапуск через systemd
8. ✅ Добавляет сервис в автозагрузку при перезагрузке сервера

---

## ⚙️ После установки:

### 1. Отредактируйте конфиг:
```bash
nano /opt/contract61-dispatcher/.env
```

Укажите реальные значения:
- `BOT_TOKEN` — получите в [@BotFather](https://t.me/BotFather)
- `GROQ_API_KEY` — получите на [console.groq.com](https://console.groq.com)

### 2. Перезапустите бота:
```bash
cd /opt/contract61-dispatcher
docker compose restart
```

### 3. Проверьте логи:
```bash
docker compose logs -f bot
```

---

## 🔧 Управление сервисом

### Через systemctl:
```bash
# Статус
systemctl status contract61-dispatcher

# Остановка
systemctl stop contract61-dispatcher

# Запуск
systemctl start contract61-dispatcher

# Перезапуск
systemctl restart contract61-dispatcher
```

### Через docker compose:
```bash
cd /opt/contract61-dispatcher

# Просмотр логов
docker compose logs -f

# Остановка
docker compose down

# Запуск
docker compose up -d

# Пересборка после обновлений
docker compose up -d --build
```

---

## 🔄 Обновление кода

```bash
cd /opt/contract61-dispatcher
git pull origin main
docker compose up -d --build
```

---

## 🛡 Требования к серверу

- **ОС**: Ubuntu 20.04+ / Debian 11+ / любой Linux с Docker
- **RAM**: минимум 512 MB (рекомендуется 1 GB+)
- **CPU**: 1 ядро+
- **Диск**: 2 GB+ свободного места

---

## 🆘 Troubleshooting

### Бот не запускается:
```bash
# Проверьте логи
docker compose logs bot

# Проверьте .env файл
cat /opt/contract61-dispatcher/.env
```

### Ошибка токена:
Убедитесь, что `BOT_TOKEN` скопирован полностью без пробелов

### Ошибка Groq API:
Проверьте ключ на [console.groq.com/keys](https://console.groq.com/keys)

### Контейнер упал:
```bash
docker compose down
docker compose up -d --force-recreate
```

---

## 📞 Поддержка

При возникновении проблем проверьте:
1. Логи: `docker compose logs -f`
2. Статус: `docker compose ps`
3. Наличие переменных в `.env`

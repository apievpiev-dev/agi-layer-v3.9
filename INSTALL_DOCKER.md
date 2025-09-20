# Установка Docker для AGI Layer v3.9

## Быстрая установка

### Вариант 1: Автоматическая установка

```cmd
install_docker.bat
```

### Вариант 2: PowerShell

```powershell
powershell -ExecutionPolicy Bypass -File install_docker.ps1
```

## Ручная установка

### 1. Скачать Docker Desktop

- Перейдите на <https://www.docker.com/products/docker-desktop/>
- Скачайте Docker Desktop for Windows
- Запустите установщик

### 2. Через winget (если доступен)

```cmd
winget install Docker.DockerDesktop
```

### 3. Настройка

1. **Перезагрузите компьютер** после установки
2. **Запустите Docker Desktop** из меню Пуск
3. **Включите WSL2** (если не включен):

   ```cmd
   wsl --install
   ```

## Проверка установки

```cmd
docker --version
docker run --rm hello-world
```

Если команды работают - Docker установлен правильно!

## Запуск AGI Layer v3.9

После установки Docker:

```cmd
docker-compose up -d
```

## Требования

- **Windows 10/11** (64-bit)
- **WSL2** (устанавливается автоматически)
- **Минимум 4GB RAM** для Docker
- **Виртуализация включена** в BIOS

## Возможные проблемы

### Docker Desktop не запускается

- Проверьте виртуализацию в BIOS
- Обновите драйверы
- Перезагрузите компьютер

### Ошибка WSL2

```cmd
wsl --install
wsl --update
```

### Недостаточно памяти

- Увеличьте лимит памяти в Docker Desktop
- Закройте другие приложения

## Поддержка

Если проблемы остаются:

1. Проверьте логи Docker Desktop
2. Перезагрузите компьютер
3. Переустановите Docker Desktop
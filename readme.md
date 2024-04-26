# Инструкция по запуска бота по отслеживанию крипты


## Как запустить бота: 

Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Ice444-222/CryptoCheckBot.git
```

Создать и активировать виртуальное окружение

```
python3 -m venv venv
```

```
source venv/bin/activate
```

Установить зависимости
```
pip install -r requirements.txt
```

Запустить файл бота
```
python3 main.py
```


## Инструкции по работе

Бот доступен в телеграмм по ссылке https://t.me/CryptoTestKhegdeBot

Для начала работы нужны выполнить компанду /start

В дальнейшем нужно пользоваться встроенной клавиатурой

Для отслеживание криптовалюты, бот принимает на вход алфавитные коды криптовалюты, например, такие как 'ETH' 'BTC'

Возможно отслеживать несколько порогов и несколько криптовалют

Бот делает запрос к API каждые 60 секунд

Когда достигнут нужный порог, бот присылает уведомление, и перестает отслеживать заданный порог

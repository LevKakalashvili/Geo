# Приложение для магазина [География. Крафтовое пиво](https://vk.com/geo_sarov)

## Приложение для синхронизации данных между сервисами [МойСклад](https://www.moysklad.ru) и [Контур.Маркет](https://market.kontur.ru/)

## Стэк:
- Python
- Django
- pydantic
- requests
- PostgreSql
- Docker


## Описание:
**1. [МойСклад](https://www.moysklad.ru)**
Вся работа происходит по [JSON API](https://dev.moysklad.ru/doc/api/remap/1.2/#mojsklad-json-api)
- Запросы к сервису происходят с использованием выданного токена.
- Получение ассортимента товаров происходит по всем торговым точкам, одного юр. лица. Для этого используется endpoint
```
https://online.moysklad.ru/api/remap/1.2/entity/assortment
```
c фильтром по корневой папке товара:
```
productFolder=https://online.moysklad.ru/api/remap/1.2/entity/productfolder/8352f575-b4c1-11e7-7a34-5acf0009a77f
```
Запуск синхронизации из командной строки:
```
manage.py do_sync --moysklad_assortment
```
Какие товары нужно загружать, настраивается в карточке самого товара в сервисе МойСклад (Пользовательское поле "Алкогольная продукция"). 

<center>
    <img src="https://user-images.githubusercontent.com/75985452/194100649-11b4d476-a254-4357-a3c0-163259325420.png" width="40%" height="40%">
</center>

- Получение списка розничных продаж за выбранную дату. Для этого используется endpoint
```
https://online.moysklad.ru/api/remap/1.2/entity/retaildemand
```
c фильтрами:
по организации
```
organization=https://online.moysklad.ru/api/remap/1.2/entity/organization/0a405989-b28a-11e7-7a31-d0fd00338283&
```
ассортименту
```
assortment=https://online.moysklad.ru/api/remap/1.2/entity/productfolder/8352f575-b4c1-11e7-7a34-5acf0009a77f
```
и диапазону розничных продаж
```
moment>2022-06-16 00:00:00
moment<2022-06-16 23:59:00
```
Запуск синхронизации из командной строки:
```
manage.py do_sync --moysklad_retaildemand YYYYMMDD
```

- Получение списка возвратов товаров за выбранную дату. Для этого используется endpoint
```
https://online.moysklad.ru/api/remap/1.2/entity/retailsalesreturn
```
c фильтрами:
по организации
```
organization=https://online.moysklad.ru/api/remap/1.2/entity/organization/0a405989-b28a-11e7-7a31-d0fd00338283&
```
ассортименту
```
assortment=https://online.moysklad.ru/api/remap/1.2/entity/productfolder/8352f575-b4c1-11e7-7a34-5acf0009a77f
```
и диапазону розничных продаж
```
moment>2022-06-16 00:00:00
moment<2022-06-16 23:59:00
```

**2. [Контур.Маркет](https://market.kontur.ru/)**
Вся работа происходит путем взаимодействия с API сервиса (не документировано)
- Авторизация происходит отправикой POST запроса на endpoint
```
https://auth.kontur.ru/api/authentication/password/auth-by-password
```
логина и пароля пользователя в зашифрованом виде

- Получение ЕГАИС наименований ассортимента товаров происходит по всем торговым точкам, одного юр. лица. Для этого используется endpoint
```
https://market.kontur.ru/api/v105/<client_uuid>/<organization_uuid>/<retail_uuuid>/Rests/List
```
Запуск синхронизации из командной строки:
```
manage.py do_sync --konturmarket_assortment
```

- Создание журнала списания товаров, ЕГАИС наименований проданных за смену. 
Для этого используется endpoint
```
https://market.kontur.ru/api/v105/<client_uuid>/<organization_uuid>/<retail_uuuid>/SalesJournal/WriteDay
```
Запуск синхронизации из командной строки:
```
manage.py --create_sales_journal
```

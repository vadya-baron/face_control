# Face Control
**AI проект фиксации времени входа/выхода сотрудников**


**Серверная часть**
- Файл **./server/service/config/example-config.yml** переименовать в **./service/config/config.yml** и изменить его данные на реальные.
- В файле **./service/config/config.yml указать секретный ключь в параметре **secret_key**
- Файл **./server/.env-example** переименовать в **./.env** и изменить его данные на реальные.
- Запустите терминал в папке **./server** и выполните команду **docker compose up -d**
-------

**Если серверная часть стоит на локальном компьютере**
- У себя в /etc/hosts (linux) или C:\Windows\System32\drivers\etc (Windows) прописать:
  - 127.0.1.1 adminer.face-control.local
  - 127.0.1.1 api.face-control.local

- **Пинг сервиса:** http://api.face-control.local:5678/ping (GET)
- **Контроллер для веб интерфейса:** http://api.face-control.local:5678/detect (POST)
- **Для удобной работы с базой:** http://adminer.face-control.local:9081
-------

- **Насройка бекапа базы:** (только для продакшена)
  - Настроить пути в файле: ./databases/backup-script.sh

-------

- **Насройка nginx:** (для изменения адресов api.face-control.local и adminer.face-control.local) 
  - ./nginx/conf.d/01_sites.conf

-------

- **Насройка cron:** (только для продакшена)
  - ./dockerfiles/install-cron-backup-db.sh 
  - Перед запуском настроить пути в файле: ./dockerfiles/backup-cron

-------

- **Веб интерфейс администрирования:** 
  - Исполняемый файл ./web_interface/admin/index.html 
  - Файл конфигурации ./web_interface/admin/js/example-config.js переименовать в ./web_interface/admin/js/config.js 
  - В файле ./web_interface/admin/js/config.js (Параметр **apiKey** должен совпадать с **secret_key** сервиса)

-------

- **Веб интерфейс детектора:** 
  - Исполняемый файл ./web_interface/detector/index.html 
  - Файл конфигурации ./web_interface/detector/js/example-config.js переименовать в ./web_interface/detector/js/config.js 
  - В файле ./web_interface/detector/js/config.js (Параметр **apiKey** должен совпадать с **secret_key** сервиса)

-------

- Если config.yml -> incoming_data_raw = **1**, передается изображение:

  curl -X "POST" -F "file=@image.jpg" http://api.face-control.local:5678/detect

- Если config.yml -> incoming_data_raw = **0**, передается массив:
  
  curl -X "POST" -H "Content-Type: application/json" --data "{\"data\":[[1, 1, 1], [2, 2, 2]]}" http://api.face-control.local:5678/detect
  
- Для подготовки датасета, можно передать изображение  **/crop**. Подготовленное лицо сохраниться в папке **./service/dataset**:
  curl -v -H "Content-Type: multipart/form-data" --form file="@image.jpg" http://api.face-control.local:5678/crop
- Можно добавить имя файлу:
  curl -v -H "Content-Type: multipart/form-data" --form file="@image.jpg" --form name="mane_image" http://api.face-control.local:5678/crop
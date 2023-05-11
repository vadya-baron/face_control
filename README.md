# Face Control
**AI проект фиксации времени входа/выхода сотрудников**

- Файл **./service/config/example-config.yml** переименовать в **./service/config/config.yml** и изменить его данные на реальные.
- Файл **./.env-example** переименовать в **./.env** и изменить его данные на реальные.
- docker compose up -d
- **Пинг сервиса:** http://api.face-control.local:9080/ping (GET)
- **Контроллер для веб интерфейса:** http://api.face-control.local:9080/detect (POST)
- **Для удобной работы с базой:** http://adminer.face-control.local:9081
- У себя в /etc/hosts (linux) или C:\Windows\System32\drivers\etc (Windows) прописать:
  - 127.0.1.1 adminer.face-control.local
  - 127.0.1.1 api.face-control.local

-------

- **Насройка бекапа базы:** 
  - Настроить пути в файле: ./databases/backup-script.sh

-------

- **Насройка nginx:** 
  - ./nginx/conf.d/01_sites.conf

-------

- **Насройка cron:** 
  - ./dockerfiles/install-cron-backup-db.sh 
  - Перед запуском настроить пути в файле: ./dockerfiles/backup-cron

-------

- **Папка с сотрудниками:** 
  - ./service/persons 
  - Название папки должно соответствовать ID сотрудника 
  - (ID = 3, значит фото сотрудника должны находиться в папке: ./service/persons/3)
  - Папка: ./service/persons/blocked хранит фото, кону доступ запрещен

-------

- Если config.yml -> incoming_data_raw = **1**, передается изображение:

  curl -X "POST" -F "file=@image.jpg" http://api.face-control.local:9080/detect

- Если config.yml -> incoming_data_raw = **0**, передается массив:
  
  curl -X "POST" -H "Content-Type: application/json" --data "{\"data\":[[1, 1, 1], [2, 2, 2]]}" http://api.face-control.local:9080/detect
  
- Для подготовки датасета, можно передать изображение  **/crop**. Подготовленное лицо сохраниться в папке **./service/dataset**:
  curl -v -H "Content-Type: multipart/form-data" --form file="@image.jpg" http://api.face-control.local:9080/crop
- Можно добавить имя файлу:
  curl -v -H "Content-Type: multipart/form-data" --form file="@image.jpg" --form name="mane_image" http://api.face-control.local:9080/crop
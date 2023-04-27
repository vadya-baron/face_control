# face_control
AI проект фиксации времени входа/выхода сотрудников 

- Файл **./service/config/example-config.yml** переименовать в **./service/config/config.yml** и изменить его данные на реальные.


- **Тестировать пока можно так:**

  - Запустить **./service/main.py**

  - Если config.yml -> incoming_data_raw = **1**, передается изображение:

    curl -X "POST" -F "file=@image.jpg" http://0.0.0.0:5678/detect

  - Если config.yml -> incoming_data_raw = **0**, передается массив:
  
    curl -X "POST" -H "Content-Type: application/json" --data "{\"data\":[[1, 1, 1], [2, 2, 2]]}" http://0.0.0.0:5678/detect
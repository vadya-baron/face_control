import os
import fnmatch
import requests
import pickle

employees_dir = './test_employees/'
api_url = 'http://51.250.90.162:8093' # 'http://api.face-control.local:9080'
add_employee = '/employees/add-employee'
update_employee_data_url = '/service/update-employee-data'
headers = {'AuthKey': 'hmF27N68ZAu3_kh7rnq5j9B63_5e17ASMnm62s'}
employees_dictionary = {}
employees_not_added = []
max_photo = 3

try:
    folders = [f.path[len(employees_dir):] for f in os.scandir(employees_dir) if f.is_dir()]
except Exception as e:
    print(e)
    exit(1)

if len(folders) == 0:
    print('Нет сотрудников')
    exit(1)

for folder in folders:
    itemData = folder.split(', ')
    if len(itemData) != 2:
        print('Папка (' + folder + ') не соответствует стандарту: ФИО, должность')
        continue

    itemImages = fnmatch.filter(os.listdir(os.path.join(employees_dir, folder)), '*.jpg')
    if len(itemImages) == 0:
        print('Папка (' + folder + ') не содержит фотографий')
        continue

    files = []
    img_count = 0
    for img in itemImages:
        img_count += 1
        if img_count <= max_photo:
            files.append(('files[]', (img, open(employees_dir + folder + '/' + img, 'rb'), 'image/jpeg')))
        break

    data = {'display_name': itemData[0], 'employee_position': itemData[1], 'external_id': 0}

    try:
        response = requests.post(api_url + add_employee, files=files, data=data, headers=headers)
        res = response.json()
        employee = res.get('employee')
    except Exception as e:
        print('ERROR: ', e)
        employees_not_added.append(itemData[0] + ' - ' + ' '.join(res['messages']))
        continue

    print('')
    if employee is None or employee.get('id') is None:
        print('Сотрудник не добавлен: ', folder)
        print('Статус ответа: ', response.status_code)
        print('Ответ: ', res)
        employees_not_added.append(itemData[0] + ' - ' + ' '.join(res['messages']))
        continue

    if type(res) == dict and res['employee']['id'] != 0:
        employees_dictionary[folder] = res['employee']['id']
        print('Добавлен сотрудник: ', folder)
    else:
        print('Ошибка добавления сотрудника: ', folder)
        if type(res) == dict:
            print('Сообщение сервиса: ', ' '.join(res['messages']))

    print('Статус ответа: ', response.status_code)
    print('Ответ: ', res)

with open(employees_dir + 'employees_dictionary.pkl', 'wb') as f:
    pickle.dump(employees_dictionary, f)

requests.post(api_url + update_employee_data_url, headers=headers)

with open(employees_dir + 'employees_dictionary.pkl', 'rb') as f:
    loaded_dict = pickle.load(f)

print('')
print('---------------')
print('Содержание файла для теста:')
print(loaded_dict)
print('---------------')
print('Не добавленные сотрудники: ')
print(' | '.join(employees_not_added))
print('---------------')
print('Загрузка сотрудников завершена')

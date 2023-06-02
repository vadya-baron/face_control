import os
import fnmatch
import requests
import pickle
import time


start_time = time.time()
employees_dir = './test_employees/'
api_url = 'http://51.250.90.162:8093' #'http://api.face-control.local:9080'
detect = '/detect'
headers = {'AuthKey': 'hmF27N68ZAu3_kh7rnq5j9B63_5e17ASMnm62s'}
total_certain_employees = 0
undetermined_employees = 0
undetermined_employees_names = []
blocked_employees = 0
correctly_defined_employees = 0
employee_is_identified_incorrectly = 0

try:
    folders = [f.path[len(employees_dir):] for f in os.scandir(employees_dir) if f.is_dir()]
except Exception as e:
    print(e)
    exit(1)

if len(folders) == 0:
    print('Нет сотрудников')
    exit(1)

with open(employees_dir + 'employees_dictionary.pkl', 'rb') as f:
    loaded_dict = pickle.load(f)

if len(loaded_dict) == 0:
    print('В файле employees_dictionary.pkl нет сотрудников')
    exit(1)

for folder in folders:
    itemData = folder.split(', ')
    if len(itemData) != 2:
        print('Папка (' + folder + ') не соответствует стандарту: ФИО, должность')
        continue

    itemImages = fnmatch.filter(os.listdir(os.path.join(employees_dir, folder, 'test')), '*.jpg')
    if len(itemImages) == 0:
        print('Папка (' + folder + '/test) не содержит фотографий')
        continue

    for img in itemImages:
        print('')
        print('---------------')
        files = {'file': open(os.path.join(employees_dir, folder, 'test', img), 'rb')}
        try:
            response = requests.post(api_url + detect, files=files, headers=headers)
            res = response.json()
        except Exception as e:
            print('ERROR: ', e)
            continue

        if type(res) != dict:
            print('Ошибка ответа сервиса')
            continue

        total_certain_employees += 1

        if res['employee_id'] > 0:
            if res['employee_id'] != loaded_dict[folder]:
                employee_is_identified_incorrectly += 1
                print('Сотрудник определен не верно: ', folder)
                continue

            correctly_defined_employees += 1
            print('Сотрудник определен: ', folder)
        elif res['employee_id'] == -1:
            blocked_employees += 1
            print('Сотрудник определен как заблокированный: ', folder)
        else:
            undetermined_employees += 1
            undetermined_employees_names.append(itemData[0] + ' - ' + img)
            print('Сотрудник не определен: ', folder)
            print('Сообщение сервиса: ', ' '.join(res['messages']))

        print('Статус ответа: ', response.status_code)
        print('Ответ: ', res)

print('')
print('---------------')

print('Всего протестировано: ', total_certain_employees)
print('Верных определений: ', correctly_defined_employees)
print('Ошибочных определений: ', employee_is_identified_incorrectly)
print('Не определен: ', undetermined_employees, ' '.join(undetermined_employees_names))
print('---------------')
print('Процент успешного определения: ', 100 * (correctly_defined_employees / (total_certain_employees - undetermined_employees)))

print('')
print('---------------')
print('Тестирование сотрудников завершено')
print("Время выполнения: %s сек." % (round(time.time() - start_time, 2)))

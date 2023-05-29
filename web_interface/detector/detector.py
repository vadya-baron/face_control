import eel
import platform

systemName = platform.system()

eel.init('src', allowed_extensions=['.js', '.html', '.css', '.png'])
if systemName == 'Linux':
    eel.browsers.set_path('chrome', './src/chrome/linux/chrome')
elif systemName == 'Windows':
    eel.browsers.set_path('chrome', './src/chrome/windows/chrome.exe')
elif systemName == 'Darwin':
    eel.browsers.set_path('chrome', './src/chrome/darwin/chrome')
else:
    print('Неизвестная платформа')
    exit(1)

eel.start('index.html', mode='chrome', size=(650, 800))

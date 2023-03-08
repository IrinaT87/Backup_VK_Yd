import requests
import settings
from tqdm import tqdm
import json


class VK:
    ''' Класс для получения фото с VK '''

    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version,
        }
        self.images = []

    def get_photos(self, user_id=None):
        ''' Получение фото пользователя по id '''
        get_photos_url = self.url + 'photos.get'
        get_photos_params = {
            'owner_id': user_id,
            'album_id': 'profile',
            'extended': 1,
            # 'count': count,
}
        response = requests.get(get_photos_url,params={**self.params, **get_photos_params},).json()

        # Составление списка изображений
        for el in response['response']['items']:
            likes_count = el['likes']['count']
            date = el['date']
            size = el['sizes'][-1]['height'] * el['sizes'][-1]['width']
            url = el['sizes'][-1]['url']
            self.images.append({
                'file_name': f"{likes_count}" if not self.is_filename_exist_in_imagelist(likes_count) else f"{likes_count}_{date}",
                'size': size,
                'url': url,
            })
        self.images = sorted(self.images, key=lambda x: x['size'], reverse=True)[:settings.yd_photo_count]


    def is_filename_exist_in_imagelist(self, fn):
        ''' Проверка наличия файла в списке изображений '''
        for el in self.images:
            if el['file_name'] == str(fn):
                return True
        return False


    def save_photo_info_to_file(self, filename='log.json'):
        ''' Запись информации о фото в файл '''
        json_object = json.dumps(self.images, indent=4)
        with open(filename, "w") as outfile:
            outfile.write(json_object)


class YaUploader:
    ''' Класс для работы с Яндекс диском '''

    host = 'https://cloud-api.yandex.net/'

    def __init__(self, token):
        self.token = token


    def get_headers(self):
        ''' Авторизация '''
        return {'Content_Type': 'application/json', 'Authorization': f'OAuth {self.token}'}


    def create_folder(self, folder_name):
        ''' Создание папки '''
        uri = 'v1/disk/resources/'
        url = self.host + uri
        params = {'path': f'/{folder_name}', 'overwrite': 'true'}
        requests.put(url, headers=self.get_headers(), params=params)


    def upload_from_VK(self, file_url, file_name, folder_name):
        ''' Загрузка файла на сервер '''
        uri = 'v1/disk/resources/upload'
        url = self.host+uri
        params = {'path': f'/{folder_name}/{file_name}',
                  'url': file_url, 'overwrite': 'true'}
        response = requests.post(url, headers=self.get_headers(), params=params)
        if response.status_code == 202:
            print(f'Загрузка файла {file_name} прошла успешно')


if __name__ == '__main__':
# Подключаемся к VK
    vk_user = VK(settings.vk_token, version='5.131')
# Получаем фото
    vk_user.get_photos(settings.owner_id)
# Сохраняем информацию в json
    vk_user.save_photo_info_to_file()

# Подключаемся к Яндекс диску
    uploader = YaUploader(settings.yd_token)
    uploader.get_headers()

# Создаем папку для фото
    folder_name = '20230307'
    uploader.create_folder(folder_name)

# Загружаем фото на сервер
    for i in tqdm(range(len(vk_user.images))):
        el = vk_user.images[i]
        uploader.upload_from_VK(el['url'], el['file_name'], folder_name)

    
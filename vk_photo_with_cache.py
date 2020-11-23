from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from _datetime import datetime
import cv2
import numpy as np
import os.path
from datetime import datetime
import time
import sys


def log(message):
    print(str(datetime.today()) + ' ' + str(message))

# API documentation:
#
# Server receives POST and GET requests to URI /?id=vk_profile_id&access_token=vk_token
#
# GET receives profile photo, put there dates and sends it back to browser
#
# POST receives the same but image becomes inverted


class VKPhoto(BaseHTTPRequestHandler):

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(204)
            return
        self.send_response(200)
        self.send_header("Content-type", "image/jpeg")
        self.end_headers()
        request = self.path.split("&")
        user_id = request[0].split("=")[-1]
        if len(request) == 2:
            access_token = request[1].split("=")[-1]
        else:
            log('ERROR: no token')
            sys.exit(2)
        if os.path.exists(f'{user_id}.jpg'):       # check if file exists
            log('Existed for: ' + str(time.time() - os.path.getmtime(f'{user_id}.jpg')))     # print how old file is
        else:
            color_text = self.get_photo(user_id, access_token, invert=False)
            # if file not exists, get photo and color for text
            image_for_text = cv2.imread(f'{user_id}.jpg')
            today = datetime.today()
            text = str("Copy date: " + today.strftime("%Y-%m-%d %H:%M:%S"))
            cv2.putText(image_for_text, text, (100, 80), cv2.FONT_HERSHEY_COMPLEX, 1, color=color_text, thickness=2)
            # put the text about date of copy file
            cv2.imwrite(f'{user_id}.jpg', image_for_text)       # write photo with text in jpeg
        image = cv2.imread(f'{user_id}.jpg')
        self.wfile.write(cv2.imencode('.JPEG', image)[1].tobytes())     # send the photo in browser

    def do_PUT(self):
        self.send_response(200)
        self.send_header("Content-type", "image/jpeg")
        self.end_headers()
        request = self.path.split("&")
        user_id = request[0].split("=")[-1]
        access_token = request[1].split("=")[-1]
        self.wfile.write(self.get_photo(user_id, access_token, invert=True))

    @staticmethod
    def get_photo(user_id, access_token, invert=False):
        log(user_id)
        params_prof_photo = {
            'user_id': user_id,
            'album_id': 'profile',
            'rev': '1',
            'access_token': access_token,
            'v': '5.120',
            'Pragma-directive': 'no-cache',
            'ache-directive': 'no-cache',
            'Cache-control': 'no-cache',
            'Pragma': 'no-cache',
            'Expires': 0
        }
        prof_photo_response = requests.get('https://api.vk.com/method/photos.get', params=params_prof_photo)
        photo_info = prof_photo_response.json()
        log(photo_info)
        photo = photo_info['response']['items'][0]
        urls = photo['sizes'][-1]
        log('url:' + urls['url'])
        date = str(datetime.fromtimestamp(photo['date']))
        log('date:' + date)
        picture = requests.get(urls['url'], stream=True).raw
        image = np.asarray(bytearray(picture.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        x0 = 100
        x2 = x0 + len(date) * 20
        x1 = x2 // 2
        y = 50
        color1 = image[x0, y - 30]
        color2 = image[x1, y - 15]
        color3 = image[x2, y]
        background = list()
        background.append(int(color1[0]) + int(color1[1]) + int(color1[2]))
        background.append(int(color2[0]) + int(color2[1]) + int(color2[2]))
        background.append(int(color3[0]) + int(color3[1]) + int(color3[2]))
        background.sort()
        if background[1] < 155:
            color_text = (255, 255, 255)
        else:
            color_text = (0, 0, 0)
        text = str("Creation date: " + date)
        cv2.putText(image, text, (x0, y), cv2.FONT_HERSHEY_COMPLEX, 1, color=color_text, thickness=2)
        # put the text about creation date
        if invert:
            image = cv2.bitwise_not(image)
            return cv2.imencode('.JPEG', image)[1].tobytes()
        else:
            cv2.imwrite(f'{user_id}.jpg', image)    # write photo with text in file
            return color_text      # return color for text


if __name__ == '__main__':
    server_class = HTTPServer
    httpd = server_class(('localhost', 8081), VKPhoto)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

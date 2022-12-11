import os.path
from io import BytesIO
from urllib.request import urlopen
from zipfile import ZipFile

# TODO: change this once there is an official download url
RIME_URL = "https://i.nofate.me/36goiuRT0V1fZWd.zip"


def get_path():
	return os.path.join(os.getcwd(), 'rime')


def is_downloaded():
	return os.path.exists(get_path())


def download():
	print("Downloading Rime...")

	resp = urlopen(RIME_URL)
	with ZipFile(BytesIO(resp.read())) as rime_zip:
		rime_zip.extractall(get_path())

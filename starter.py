import os
import urllib.request
import sys
import requests
from pyhocon import ConfigFactory, HOCONConverter
import pywaves as pw
import base58
import string
import random
import math
from tqdm import tqdm

DEFAULT_VERSION = 'latest'
DEFAULT_AUTODETECT = 'yes'
network_names = ['MAINNET', 'TESTNET', 'CUSTOM']

NETWORK = os.environ.get('WAVES_NETWORK')


def generate_password(size=12, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for i in range(size))


def get_latest_version(network):
    releases_url = "https://api.github.com/repos/wavesplatform/Waves/releases"
    r = requests.get(url=releases_url)
    data = r.json()
    for item in data:
        if network.lower() in item['name'].lower():
            print('Latest version for ' + network + ' is: ', item['name'])
            return item['tag_name'].replace('v', '')


def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def create_configs_dir():
    if not os.path.isdir("/waves/configs"):
        os.mkdir("/waves/configs")
    if not os.path.isdir("/waves/data"):
        os.mkdir("/waves/data")


def parse_env_variables():
    dictionary = dict()
    for env_key in os.environ:
        if "__" in env_key:
            parts = env_key.split('__')
            keys = [x.lower().replace('_', '-') for x in parts]
            nested_set(dictionary, keys, os.environ[env_key])
    return dictionary


def download_from_url(url, dst):
    # Streaming, so we can iterate over the response.
    r = requests.get(url, stream=True)

    # Total size in bytes.
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024
    wrote = 0
    with open(dst, 'wb') as f:
        for data in tqdm(r.iter_content(block_size), total=math.ceil(total_size // block_size), unit='KB',
                         unit_scale=True):
            wrote = wrote + len(data)
            f.write(data)
    if total_size != 0 and wrote != total_size:
        print("ERROR, something went wrong")


def download_jar_file(version_name, version_number):
    file_name = "waves-all-" + version_number + ".jar"
    print('Downloading file: ' + file_name)
    link = "https://github.com/wavesplatform/Waves/releases/download/v" + version_number + "/" + file_name
    download_from_url(link, '/waves-node/waves-all-' + version_name + '.jar')


def get_wallet_data():
    seed = os.environ.get('WAVES_WALLET_SEED', pw.Address().seed)
    seed_base58 = os.environ.get('WAVES_WALLET_SEED_BASE58')
    base58_provided = False
    if seed_base58 is not None:
        try:
            base58.b58decode_check(seed_base58)
            base58_provided = True
        except:
            seed_base58 = base58.b58encode(seed.encode())
    else:
        seed_base58 = base58.b58encode(seed.encode())
    password = os.environ.get('WAVES_WALLET_PASSWORD', generate_password())
    if base58_provided is False:
        print('Seed phrase:', seed)
    print('Wallet password:', password)
    return seed_base58, password


def get_external_ip():
    return requests.get('http://ifconfig.co/ip').text.rstrip("\n\r")


def get_port_number(network):
    if network == 'TESTNET':
        return '6863'
    elif network == 'MAINNET':
        return '6868'
    else:
        return '6869'


if __name__ == "__main__":
    if NETWORK is None or NETWORK not in network_names:
        NETWORK = 'TESTNET'

    WAVES_VERSION = os.getenv('WAVES_VERSION', DEFAULT_VERSION)
    VERSION = os.getenv('WAVES_VERSION', DEFAULT_VERSION)
    if VERSION.lower() == 'latest':
        VERSION = get_latest_version(NETWORK)

    create_configs_dir()

    file_path = "/waves/configs/waves-config.conf"
    url = "https://raw.githubusercontent.com/wavesplatform/Waves/v" + VERSION + "/waves-" + NETWORK.lower() + ".conf"
    urllib.request.urlretrieve(url, file_path)

    env_dict = parse_env_variables()
    wallet_data = get_wallet_data()

    nested_set(env_dict, ['waves', 'directory'], '/waves')
    nested_set(env_dict, ['waves', 'data-directory'], '/waves/data')
    nested_set(env_dict, ['waves', 'wallet', 'seed'], wallet_data[0])
    nested_set(env_dict, ['waves', 'wallet', 'password'], wallet_data[1])

    WAVES_AUTODETECT_ADDRESS = os.getenv('WAVES_AUTODETECT_ADDRESS', DEFAULT_AUTODETECT)
    WAVES_DECLARED_ADDRESS = os.getenv('WAVES_DECLARED_ADDRESS')
    if WAVES_AUTODETECT_ADDRESS.lower() == 'yes' and WAVES_DECLARED_ADDRESS is None:
        WAVES_DECLARED_ADDRESS = get_external_ip() + ':' + get_port_number(NETWORK)
        print("Detected address is " + WAVES_DECLARED_ADDRESS)
        nested_set(env_dict, ['waves', 'network', 'declared-address'], WAVES_DECLARED_ADDRESS)
    elif WAVES_DECLARED_ADDRESS is not None:
        nested_set(env_dict, ['waves', 'network', 'declared-address'], WAVES_DECLARED_ADDRESS)

    config = ConfigFactory.from_dict(env_dict)
    local_conf = HOCONConverter.convert(config, 'hocon')
    with open('/waves/configs/local.conf', 'w') as file:
        file.write(local_conf)

    download_jar_file(WAVES_VERSION, VERSION)

import os
import urllib.request
import requests
from pyhocon import ConfigFactory, HOCONConverter
import pywaves as pw
import base58
import string
import random
import math
from tqdm import tqdm
import ipaddress
import ast
from time import sleep


DEFAULT_VERSION = 'latest'
DEFAULT_THRESHOLD = 0
DEFAULT_AUTODETECT = 'yes'
network_names = ['MAINNET', 'TESTNET', 'DEVNET']

DEFAULT_NODES = ['https://nodes.wavesnodes.com', 'https://testnodes.wavesnodes.com/', 'http://127.0.0.1:6869']
NETWORK = os.environ.get('WAVES_NETWORK')

LOCAL_FILE_PATH = '/waves/configs/local.conf'


def generate_password(size=12, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for i in range(size))


def get_latest_version(network):
    releases_url = "https://api.github.com/repos/wavesplatform/Waves/releases"
    r = requests.get(url=releases_url)
    data = r.json()

    if network.lower() == 'devnet':
        network_name = 'testnet'
    else:
        network_name = network.lower()

    for item in data:
        if network_name in item['name'].lower():
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


def parse_env_variables(ext_dict=dict()):
    dictionary = ext_dict
    for env_key in os.environ:
        value = os.environ[env_key]
        print(f"Key: {env_key} , value: {value}")
        if "__" in env_key:
            parts = env_key.split('__')
            keys = [x.lower().replace('_', '-') for x in parts]
            value = os.environ[env_key]
            if isinstance(value, str):
                if value.lower() == 'true':
                    value = 'yes'
                if value.lower() == 'false':
                    value = 'no'
            if isinstance(value, str) and len(value) > 0 and value[0] == '[' and value[-1] == ']':
                value = ast.literal_eval(value)
            nested_set(dictionary, keys, value)
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
    seed = os.environ.get('WAVES_WALLET_SEED', pw.Address(privateKey=None).seed)
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
        if seed != os.environ.get('WAVES_WALLET_SEED'):
            print('Seed phrase: ', seed)
        print('Address: ', pw.Address(seed=seed).address)
    print('Wallet password:', password)
    return {'seed': seed_base58, 'password': password}


def get_external_ip():
    plain_response = requests.get('http://ipinfo.io/ip').text.rstrip("\n\r")
    try:
        ip = ipaddress.ip_address(plain_response)
        return plain_response
    except ValueError:
        plain_response = requests.get('http://ipecho.net/plain').text.rstrip("\n\r")
        ip = ipaddress.ip_address(plain_response)
        return plain_response
    except ValueError:
        return requests.get('http://icanhazip.com').text.rstrip("\n\r")


def get_port_number(network):
    declared_port = os.getenv('WAVES_AUTODETECT_ADDRESS_PORT')
    if declared_port is not None:
        return declared_port
    if network == 'TESTNET':
        return '6863'
    elif network == 'MAINNET':
        return '6868'
    else:
        return '6816'


def set_pywaves_node(network):
    if network == 'TESTNET':
        # node = DEFAULT_NODES[1]
        chain_id = None
    elif network == 'MAINNET':
        # node = DEFAULT_NODES[0]
        chain_id = None
    else:
        # node = DEFAULT_NODES[2]
        chain_id = 'E'
    pw.setNode(chain=network.lower(), chain_id=chain_id)


if __name__ == "__main__":
    if NETWORK is None or NETWORK not in network_names:
        NETWORK = 'TESTNET'

    WAVES_VERSION = os.getenv('WAVES_VERSION', DEFAULT_VERSION)
    WAVES_THRESHOLD = int(os.getenv('WAVES_THRESHOLD', DEFAULT_THRESHOLD))
    VERSION = os.getenv('WAVES_VERSION', DEFAULT_VERSION)

    if WAVES_THRESHOLD > 0:
        print(f"Sleeping for {WAVES_THRESHOLD} seconds")
        sleep(WAVES_THRESHOLD)

    if VERSION.lower() == 'latest':
        VERSION = get_latest_version(NETWORK)
    print("Version: " + WAVES_VERSION + "(" + VERSION + ")")
    create_configs_dir()

    file_path = "/waves/configs/waves-config.conf"
    url = "https://raw.githubusercontent.com/wavesplatform/Waves/v" + VERSION + "/node/waves-" + NETWORK.lower() + ".conf"
    urllib.request.urlretrieve(url, file_path)

    set_pywaves_node(NETWORK)

    wallet_data = get_wallet_data()

    print(wallet_data)

    if os.path.exists(LOCAL_FILE_PATH):
        env_dict = ConfigFactory.parse_file(LOCAL_FILE_PATH)
        if 'waves' in env_dict and 'wallet' in env_dict['waves']:
            if 'seed' in env_dict['waves']['wallet']:
                wallet_data['seed'] = env_dict['waves.wallet.seed']
            if 'password' in env_dict['waves']['wallet']:
                wallet_data['password'] = env_dict['waves.wallet.password']
    else:
        env_dict = {}
    env_dict = parse_env_variables(env_dict)

    nested_set(env_dict, ['waves', 'directory'], '/waves')
    nested_set(env_dict, ['waves', 'data-directory'], '/waves/data')
    nested_set(env_dict, ['waves', 'wallet', 'seed'], wallet_data['seed'])
    nested_set(env_dict, ['waves', 'wallet', 'password'], wallet_data['password'])

    WAVES_AUTODETECT_ADDRESS = os.getenv('WAVES_AUTODETECT_ADDRESS', DEFAULT_AUTODETECT)
    WAVES_DECLARED_ADDRESS = os.getenv('WAVES_DECLARED_ADDRESS')
    print("WAVES_DECLARED_ADDRESS", WAVES_DECLARED_ADDRESS)
    if WAVES_AUTODETECT_ADDRESS.lower() == 'yes' and WAVES_DECLARED_ADDRESS is None:
        WAVES_DECLARED_ADDRESS = get_external_ip() + ':' + get_port_number(NETWORK)
        print("Detected address is " + WAVES_DECLARED_ADDRESS)
        nested_set(env_dict, ['waves', 'network', 'declared-address'], WAVES_DECLARED_ADDRESS)
    elif WAVES_DECLARED_ADDRESS is not None:
        nested_set(env_dict, ['waves', 'network', 'declared-address'], WAVES_DECLARED_ADDRESS)

    config = ConfigFactory.from_dict(env_dict)
    local_conf = HOCONConverter.convert(config, 'hocon')
    print(local_conf)
    with open(LOCAL_FILE_PATH, 'w') as file:
        file.write(local_conf)

    download_jar_file(WAVES_VERSION, VERSION)

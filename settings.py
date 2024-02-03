import yaml
from collections import namedtuple

def dict_to_namedtuple(name, dictionary):
    """
    Convierte recursivamente un diccionario en un namedtuple.

    Parámetros:
        name (str): El nombre del namedtuple.
        dictionary (dict): El diccionario a convertir.

    Retorna:
        namedtuple: Un objeto namedtuple representando el diccionario.
    """
    for key, value in dictionary.items():
        if isinstance(value, dict):
            dictionary[key] = dict_to_namedtuple(key, value)
    return namedtuple(name, dictionary.keys())(**dictionary)


def load_config(filename='settings.yml'):
    with open(filename, 'r') as file:
        config_dict = yaml.safe_load(file)
    return dict_to_namedtuple('Config', config_dict)


config = load_config()

if __name__ == "__main__":
    config = load_config('settings.yml')
    print(config)

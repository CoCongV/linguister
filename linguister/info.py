from functools import partial

from colorama import init, Fore, Back, Style

from linguister.errout import err

print = partial(print, end='')

def out(data):
    info_out(data['words'], data['ph'], data['source'])
    for mean in data.get('means', []):
        mean_out(mean)
    if data.get('translate_msg') and data.get('translate_result'):
        translate_out(data['translate_msg'], data['translate_result'])
    for n, s in enumerate(data['sentences'], start=1):
        sentence_out(n, s['example'], s['translate'])
    separator()

def err_out(err_data):
    if err_data.get('exc'):
        indent(2)
        err(str(err_data['exc']) + ' ~ ' + err_data['source'])
        separator()
        return

def info_out(word, ph, source):
    indent(2)
    ph = str(ph if ph else [])
    print(word + '  ' + Fore.RED + ph)
    print(Style.DIM + '  ~  ' + source)
    change_line()

def mean_out(mean):
    indent()
    print(Style.DIM + '- ')
    print(Fore.GREEN + mean)
    change_line()

def translate_out(source, translate_msg):
    indent()
    print(Fore.GREEN + translate_msg)
    change_line()
    indent()
    print(Fore.YELLOW + source)
    change_line()

def sentence_out(id_, sentence, trans_sentence):
    id_ = str(id_)
    indent()
    print(Style.DIM + id_ + '. ' + sentence)
    change_line()
    indent(4)
    print(Fore.BLUE + trans_sentence)
    change_line()

def indent(num=2):
    spaces = ''
    for i in range(num):
        spaces += ' '
    print(spaces)

def change_line():
    print('', end='\n')

def separator(symbol='-', nums=10):
    change_line()
    indent(2)
    string = ''
    for i in range(nums):
        string += symbol
    print(string)
    change_line()
    change_line()

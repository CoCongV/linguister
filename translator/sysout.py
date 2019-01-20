from functools import partial

from colorama import init, Fore, Back, Style

print = partial(print, end='')

def info_out(word, ph, source):
    indent(2)
    print(word + '  ' + Fore.RED + str([ph]))
    print(Style.DIM + '  ~  ' + source)
    change_line()

def means_out(part, means):
    indent()
    print(Style.DIM + '- ')
    means_string = '; '.join(means)
    print(Fore.GREEN + part + '.' + ' ' + means_string)
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

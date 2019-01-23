
# def generate_ph(en=None, us=None):
def generate_ph(**kwargs):
    if kwargs:
        string = ''
        for k, v in kwargs.items():
            string += '{} [{}] '.format(str(k), str(v))
    else:
        string = '[]'
    return string

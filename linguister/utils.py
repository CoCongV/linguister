import tempfile

def generate_ph(**kwargs):
    if kwargs:
        string = ''
        for k, v in kwargs.items():
            string += '{} [{}] '.format(str(k), str(v))
    else:
        string = '[]'
    return string


def generate_temp(data, prefix, suffix=".mp3"):
    file, filename = tempfile.mkstemp(suffix=".mp3", prefix=prefix,)
    with open(filename, "wb") as f:
        f.write(data)
    return filename
from translator.sysout import out


word_data = {
    'sentences':
    [{
        'translate':
        '英语伤我千百遍，我待英语如初恋。',
        'example':
        'English has hurt me a thousand times, but I still regard it as my first love.'
    },
     {
         'translate': '热爱生活，生活也会厚爱你。',
         'example': 'If you love life, life will love you back.'
     },
     {
         'translate':
         '我会回去，找到你，爱你，娶你，活的光明正大。《赎罪》',
         'example':
         'I will return, find you, love you, marry you and live without shame.'
     }],
    'ph':
    "US ['lʌv'] UK ['lʌv']",
    'words':
    'love',
    'source':
    'iciba',
    'means': [
        'vt.& vi. 爱，热爱; 爱戴; 喜欢; 赞美，称赞', 'vt. 喜爱; 喜好; 喜欢; 爱慕',
        'n. 爱情，爱意; 疼爱; 热爱; 爱人，所爱之物'
    ],
    'audio':
    'http://res.iciba.com/resource/amp3/1/0/b5/c0/b5c0b187fe309af0f4d35982fd961d7e.mp3'
}

sentence_data = {
    'sentences': [{
        'example':
        'You know I love you baby, but you left me to hang.',
        'translate':
        '你知道我爱你宝贝, 但你却敷衍我.'
    },
                  {
                      'example': 'I love you baby and if its quite all right.',
                      'translate': '我需要你们的婴儿,如果其相当好.'
                  },
                  {
                      'example':
                      "I'll do anything to prove I love you, Baby girl.",
                      'translate':
                      '我会做一些事来证明我爱你, 我的爱.'
                  }],
    'source':
    'iciba',
    'words':
    'i love you baby',
    'translate_result':
    '我爱你宝贝',
    'ph':
    'US [] UK []',
    'audio':
    None,
    'translate_msg':
    '以上结果来自腾讯翻译君。'
}


class TestOut:
    def test_word_out(self):
        out(word_data)

    def test_sentence_out(self):
        out(sentence_data)

from linguister.audio import play


audio_url = 'http://res.iciba.com/resource/amp3/1/0/b5/c0/b5c0b187fe309af0f4d35982fd961d7e.mp3'


class TestPlay:
    def test_audio(self):
        play(audio_url)
        
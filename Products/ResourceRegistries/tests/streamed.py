import os.path
from ZPublisher.Iterators import filestream_iterator

class StreamedResource(object):
    
    def __call__(self):
        f = os.path.join(
                os.path.dirname(__file__),
                'test_resources',
                'streamed.js',
            )
        return filestream_iterator(f)

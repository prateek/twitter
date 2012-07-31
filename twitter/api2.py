import requests
import json

from .api import TwitterError
from .auth import NoAuth


class TwitterAPIError(TwitterError):
    def __init__(self, message, res):
        self.res = res
        TwitterError.__init__(self, message)


class TwitterAPI(object):
    def __init__(self, host='api.twitter.com', api_ver='1', auth=NoAuth(),
                 secure=True, stream=False, return_raw_response=False):
        self.host = host
        self.api_ver = api_ver
        self.auth = auth
        self.secure = secure
        self.stream = stream
        self.return_raw_response = return_raw_response


    def get(self, path, **kwargs):
        url, remaining_params = make_url(self.secure, self.host, self.api_ver,
                                         path, kwargs)
        data = self.auth.encode_params(url, 'GET', remaining_params)
        headers = self.auth.generate_headers()
        res = requests.get(url + '?' + data, headers=headers)
        return handle_res(res, self.return_raw_response, self.stream)


    def post(self, path, **kwargs):
        url, remaining_params = make_url(self.secure, self.host, self.api_ver,
                                         path, kwargs)
        data = self.auth.encode_params(url, 'POST', remaining_params)
        headers = self.auth.generate_headers()
        res = requests.post(url, data=data, headers=headers)
        return handle_res(res, self.return_raw_response, self.stream)


_default_api = TwitterAPI()

get = _default_api.get


_search_api = TwitterAPI(host="search.twitter.com", api_ver=None)

def search(q, **kwargs):
    return _search_api.get("search", q=q, **kwargs)


def make_url(secure, host, api_ver, path, params):
    remaining_params = dict(params)
    real_params = []
    for param in path.split('/'):
        if param.startswith(':'):
            if param[1:] not in params:
                raise TwitterError("Missing parameter for ':{}'".format(param))
            param = str(params.pop(param[1:]))
        real_params.append(param)
    real_path = '/'.join(real_params)
    api_ver_str = '{}/'.format(str(api_ver)) if api_ver is not None else ""
    secure_str = 's' if secure else ''
    url = 'http{}://{}/{}{}.json'.format(secure_str, host, str(api_ver_str),
                                         real_path)
    return url, remaining_params


def handle_res(res, return_raw_response, stream):
    if res.status_code != 200:
        raise TwitterAPIError(
            "Twitter responded with invalid status code: {}"
            .format(res.status_code),
            res)
    if return_raw_response:
        result = res
    elif stream:
        def generate_json():
            for line in res.iter_lines():
                yield json.loads(line.decode('utf-8'))
        return generate_json()
    else:
        result = res.json
    return result

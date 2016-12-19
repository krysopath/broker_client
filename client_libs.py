#!/usr/bin/env python3
# coding=utf-8

from functools import wraps
from time import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def requester(fn):
    @wraps(fn)
    def req(*args, **kwargs):
        #t = time()
        resp = fn(*args, **kwargs)
        #tdelta = time() - t
        #print('resource: ', resp.url)
        with open('last-response.txt', 'w') as last:
            last.write(resp.text)

        #print(round(tdelta, 5), 'sec for', resp.request)
        if resp.status_code != 200:
            if resp.status_code == 401:
                raise NotAuthedError
            raise ApiError(
                '{} {}'.format(resp.request, resp.url),
                resp.status_code)
        else:
            return resp

    return req


def decoder(fn):
    @wraps(fn)
    def req(*args, **kwargs):
        def timed():
            t = time()
            response = fn(*args, **kwargs)
            dtime = time() - t
            print(
                round(dtime, 5),
                'sec for requesting & decoding JSON'
            )
            return response, dtime

        response, dtime = timed()
        try:
            json_data = response.json()
            return json_data, response.status_code
        except TypeError:
            return None, 404

    return req


class Actor:
    verify = False
    automatic = False

    def __init__(self, uri, username=None, password=None, ressource=None, verify_ssl=None, token=None):
        self.verify = verify_ssl or self.verify
        self._credentials = username, password
        self._base_uri = uri
        self._ressource = ressource
        self._uri = None
        self._token = token or None

    def get_token(self):
        print("snatching token for", self._credentials[0])
        data, status_code = self.get(
            self._base_uri.format(
                self._credentials[0],
                self._credentials[1],
                "token"  # API endpoint of broker that provides token
            )
        )
        self.token = data['result']['token']

    def make_uri(self):
        if not self.token:
            return self._base_uri.format(
                self._credentials[0],
                self._credentials[1],
                self.ressource
            )
        else:
            return self._base_uri.format(
                self.token,
                "authbytoken",
                self.ressource
            )

    @property
    def uri(self):
        return self.make_uri()

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        self._token = token

    @property
    def ressource(self):
        return self._ressource

    @ressource.setter
    def ressource(self, ressource):
        self._ressource = ressource

    @decoder
    @requester
    def get(self, uri):
        try:
            return requests.get(
                uri,
                verify=self.verify
            )
        except NotAuthedError:
            self.get_token()
            return requests.get(
                uri,
                verify=self.verify
            )

    @decoder
    @requester
    def put(self, uri, data):
        try:
            return requests.put(
                uri,
                verify=self.verify,
                json=data
            )
        except NotAuthedError:
            self.get_token()
            return requests.put(
                uri,
                verify=self.verify,
                json=data
            )

    @decoder
    @requester
    def post(self, uri, data):
        try:
            return requests.post(
                uri,
                verify=self.verify,
                json=data
            )
        except NotAuthedError:
            self.get_token()
            return requests.post(
                uri,
                verify=self.verify,
                json=data
            )

    @decoder
    @requester
    def delete(self, uri):
        try:
            return requests.delete(
                uri,
                verify=self.verify,
            )
        except NotAuthedError:
            self.get_token()
            return requests.delete(
                uri,
                verify=self.verify,
            )

    def request_all(self):
        data, status_code = self.get(self.uri)
        return data, status_code

    def get_user(self, name):
        data, status_code = self.get(self.uri + "/%s" % name)
        return data, status_code

    def update_user(self,
                    username,
                    **user_args):
        data, status_code = self.put(
            self.uri + "/%s" % username,
            user_args
        )
        return data, status_code

    def add_user(self, **user_args):
        data, status_code = self.post(
            self.uri,
            data=user_args,
        )
        return data, status_code

    def del_user(self, name):
        data, status_code = self.delete(
            self.uri + "/%s" % name,
        )
        return data, status_code

    @requester
    def get_adresses(self, name):
        return requests.get(
            self.uri + "/%s" % name,
            verify=self.verify
        )


class ApiError(Exception):
    pass


class NotAuthedError(ApiError):
    pass

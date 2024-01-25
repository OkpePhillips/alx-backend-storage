#!/usr/bin/env python3
'''
Using redis in python via the redis-py library.
'''
import redis
import uuid
from typing import Union, Callable
import functools
import json


def count_calls(method):
    ''' A decorator returning a callable '''
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        ''' Wrapper to increment key. '''
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    ''' Defining a history decorator '''
    @functools.wraps(method)
    def history_wrapper(self, *args, **kwargs):
        ''' Adding calls and result to input
        and output lists '''
        input_key = method.__qualname__ + ":inputs"
        output_key = method.__qualname__ + ":outputs"
        normalized_args = str(args)
        self._redis.rpush(input_key, normalized_args)
        output = method(self, *args, **kwargs)
        self._redis.rpush(output_key, json.dumps(output))
        return output
    return history_wrapper


class Cache:
    '''
    A cache class to create an instance of Redis.
    '''
    def __init__(self, host='localhost', port=6379, db=0):
        '''
        Instantiating a redis object.
        '''
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: Union[str, bytes, int, float]) -> str:
        '''
        A method to store input data in redis and return key.
        '''
        r_key = str(uuid.uuid4())
        self._redis.set(r_key, data)
        return r_key

    def get(self, key: str, fn: Callable = None) -> Union[str,
                                                          bytes, int,
                                                          float, None]:
        '''
        Retrieving a redis object and converting to desired
        format using the callback function.
        '''
        data = self._redis.get(key)
        if data is None:
            return None
        if fn is not None:
            return fn(data)
        return data

    def get_str(self, key: str) -> Union[str, None]:
        ''' Returning a string format of the data '''
        return self.get(key, fn=lambda d: d.decode("utf-8"))

    def get_int(self, key: str) -> Union[int, None]:
        ''' Returning and integer of the data '''
        return self.get(key, fn=int)


def replay(method):
    '''
    A function to display the history of calls of a particular function.
    '''
    method_name = method.__qualname__

    key_inputs = method_name + ":inputs"
    key_outputs = method_name + ":outputs"
    inputs = [json.loads(data) for data in cache._redis.lrange(
                                key_inputs, 0, -1)]
    outputs = [json.loads(data) for data in cache._redis.lrange(
                                key_outputs, 0, -1)]

    print(f"{method_name} was called {len(inputs)} times:")
    for input_args, output in zip(inputs, outputs):
        print(f"{method_name}(*{input_args}) -> {output}")

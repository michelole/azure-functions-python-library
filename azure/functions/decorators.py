# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
import json
from typing import Dict, List, Union

from azure.functions._decorators import Binding, DataType, DummyTrigger, \
    InputBinding, OutputBinding, Scaffold, StringifyEnum, Trigger


class HttpMethod(StringifyEnum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"


class AuthLevel(StringifyEnum):
    FUNCTION = "function"
    ANONYMOUS = "anonymous"
    ADMIN = "admin"


class EventHubTrigger(Trigger):

    def __init__(self, name, connection):
        self.connection = connection
        super(EventHubTrigger, self).__init__(name)

    @staticmethod
    def get_binding_name():
        return "EventHubTrigger"

    def get_dict_repr(self):
        return {"connection": self.connection,
                "name": self.name}


class HttpTrigger(Trigger):
    @staticmethod
    def get_binding_name():
        return "httpTrigger"

    def __init__(self, name, methods=None,
                 auth_level: AuthLevel = AuthLevel.ANONYMOUS,
                 route='/api') -> None:
        self.auth_level = auth_level
        self.route = route
        self.methods = methods
        super().__init__(name=name)

    def get_dict_repr(self):
        dict_repr = {
            "authLevel": str(self.auth_level),
            "type": self.get_binding_name(),
            "direction": self.get_binding_direction(),
            "name": self.name
        }
        if self.methods is not None:
            dict_repr["methods"] = [str(m) for m in self.methods]

        return dict_repr


class Http(OutputBinding):
    @staticmethod
    def get_binding_name():
        return "http"

    def __init__(self, name) -> None:
        super().__init__(name=name)

    def get_dict_repr(self):
        return {
            "type": self.get_binding_name(),
            "direction": self.get_binding_direction(),
            "name": self.name
        }


class BlobOutput(OutputBinding):
    @staticmethod
    def get_binding_name():
        return "blob"

    def __init__(self, name: str, connection: str, path: str,
                 data_type: DataType):
        self.connection = connection
        self.path = path
        self.data_type = data_type
        super().__init__(name=name)

    def get_dict_repr(self):
        return {
            "type": self.get_binding_name(),
            "direction": self.get_binding_direction(),
            "name": self.name,
            "dataType": self.data_type,
            "path": self.path,
            "connection": self.connection
        }


class BlobInput(InputBinding):
    @staticmethod
    def get_binding_name():
        return "blob"

    def __init__(self, name: str, connection: str, path: str, data_type: str):
        self.connection = connection
        self.path = path
        self.data_type = data_type
        super().__init__(name=name)

    def get_dict_repr(self):
        return {
            "type": self.get_binding_name(),
            "direction": self.get_binding_direction(),
            "name": self.name,
            "dataType": self.data_type,
            "path": self.path,
            "connection": self.connection
        }


class BlobTrigger(Trigger):

    @staticmethod
    def get_binding_name():
        return "blobTrigger"

    def __init__(self, name: str, connection: str, path: str, data_type: str):
        self.connection = connection
        self.path = path
        self.data_type = data_type
        super().__init__(name=name)

    def get_dict_repr(self):
        return {
            "type": self.get_binding_name(),
            "direction": self.get_binding_direction(),
            "name": self.name,
            "dataType": self.data_type,
            "path": self.path,
            "connection": self.connection
        }


class Function(object):
    def __init__(self, func, script_file=None):
        self._func = func
        self._trigger: Trigger = DummyTrigger()
        self._bindings: List[Binding] = []

        self.script_file = script_file or "dummy"

    def add_binding(self, binding: Binding):
        self._bindings.append(binding)

    def add_trigger(self, trigger: Trigger):
        if self._trigger and not isinstance(self._trigger, DummyTrigger):
            raise ValueError("A trigger was already registered to this "
                             "function. Adding another trigger is not the "
                             "correct behavior as a function can only have one"
                             f" trigger. New trigger being added {trigger}")
        self._trigger = trigger
        self._bindings.append(trigger)

    def get_trigger(self):
        return self._trigger

    def get_bindings(self):
        return self._bindings

    def get_dict_repr(self):
        stub_f_json: Dict[str, Union[List[str], str]] = {
            "scriptFile": self.script_file, "bindings": []}
        for b in self._bindings:
            stub_f_json["bindings"].append(b.get_dict_repr())  # NoQA

        return stub_f_json

    def get_user_function(self):
        return self._func

    def get_function_json(self):
        return json.dumps(self.get_dict_repr())

    def __str__(self):
        return self.get_function_json()


class FunctionsApp(Scaffold):
    def __init__(self, script_file):
        self.functions = []
        super().__init__(script_file)

    def get_functions(self) -> List[Function]:
        return self.functions

    def on_trigger(self, trigger: Trigger, *args, **kwargs):
        def decorator(func, *args, **kwargs):
            if isinstance(func, Function):
                f = self.functions.pop()
            elif callable(func):
                f = Function(func, self.script_file)
            else:
                raise ValueError("WTF Trigger!")
            f.add_trigger(trigger)
            self.functions.append(f)
            return f
        return decorator

    def binding(self, binding: Binding = None, *args, **kwargs):
        def decorator(func, *args, **kwargs):
            if isinstance(func, Function):
                f = self.functions.pop()
            elif callable(func):
                f = Function(func, self.script_file)
            else:
                raise ValueError("WTF Binding!")
            f.add_binding(binding=binding)
            self.functions.append(f)
            return f
        return decorator

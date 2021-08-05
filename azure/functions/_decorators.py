import typing
from abc import ABC, ABCMeta, abstractmethod
from enum import Enum
import json


class StringifyEnum(Enum):
    def __str__(self):
        return str(self.value)


class BindingDirection(StringifyEnum):
    IN = "in"
    OUT = "out"


class HttpMethod(StringifyEnum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"


class AuthLevel(StringifyEnum):
    FUNCTION = "function"
    ANONYMOUS = "anonymous"
    ADMIN = "admin"


class BlobDataType(StringifyEnum):
    STRING = "string"
    BINARY = "binary"
    STREAM = "stream"


class Binding(ABC):
    @staticmethod
    @abstractmethod
    def get_binding_name():
        pass

    def __init__(self, name: str,
                 direction: BindingDirection) -> None:
        self.direction = direction
        self.binding_type = self.get_binding_name()
        self.name = name

    @abstractmethod
    def get_dict_repr(self):
        pass

    def get_binding_direction(self):
        return str(self.direction)

    def __str__(self):
        return str(self.get_dict_repr())


class Trigger(Binding, metaclass=ABCMeta):
    def __init__(self, name) -> None:
        self.is_trigger = True
        super().__init__(direction=BindingDirection.IN,
                         name=name)


class InputBinding(Binding, metaclass=ABCMeta):
    def __init__(self, name) -> None:
        super().__init__(direction=BindingDirection.IN,
                         name=name)


class OutputBinding(Binding, metaclass=ABCMeta):
    def __init__(self, name) -> None:
        super().__init__(direction=BindingDirection.OUT,
                         name=name)


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
            "type": self.binding_type,
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
        self._script_file = script_file or "dummy"
        self._func = func
        self._trigger: typing.Optional[Trigger] = None
        self._bindings: typing.List[Binding] = []

    def add_binding(self, binding: Binding):
        self._bindings.append(binding)

    def add_trigger(self, trigger: Trigger):
        if self._trigger:
            raise ValueError("A trigger was already registered to this function"
                             ". Adding another trigger is not the correct "
                             "behavior as a function can only have one trigger."
                             f" New trigger being added {trigger}")
        self._trigger = trigger

    def get_trigger(self):
        return self._trigger

    def get_bindings(self):
        return self._bindings

    def get_dict_repr(self):
        stub_f_json = {"scriptFile": self._script_file, "bindings": []}
        stub_f_json["bindings"].append(self._trigger.get_dict_repr())
        for b in self._bindings:
            stub_f_json["bindings"].append(b.get_dict_repr())

        return stub_f_json

    def get_user_function(self):
        return self._func

    def get_function_json(self):
        return json.dumps(self.get_dict_repr())

    def __str__(self):
        return self.get_function_json()


class Scaffold(object):
    def __init__(self, script_file=None):
        self.functions = []
        self.script_file = script_file or "dummy"

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


class FunctionsApp(Scaffold):
    def __init__(self, script_file):
        super().__init__(script_file)

    def get_functions(self) -> typing.List[Function]:
        return self.functions

    def blob_output(self, name: str, connection: str, path: str,
                    data_type: str):
        pass

    def route(self):
        pass

import datetime
import time

from intercom.lib.flat_store import FlatStore
from intercom.lib.typed_json_deserializer import JsonDeserializer


def type_field(attribute):
    return attribute == "type"


def timestamp_field(attribute):
    return attribute.endswith('_at')


def custom_attribute_field(attribute):
    return attribute == 'custom_attributes'


def typed_value(value):
    return hasattr(value, 'keys') and 'type' in value


def datetime_value(value):
    return hasattr(value, "timetuple")


def to_datetime_value(value):
    if value:
        return datetime.datetime.fromtimestamp(int(value))


class Resource(object):

    def __init__(_self, **params):
        _self.changed_attributes = []
        _self.from_dict(params)
        self = _self

        if hasattr(_self, 'flat_store_attributes'):
            for attr in self.flat_store_attributes:
                if not hasattr(self, attr):
                    setattr(self, attr, FlatStore())
        _self.changed_attributes = []

    def _flat_store_attribute(self, attribute):
        if hasattr(self, 'flat_store_attributes'):
            return attribute in self.flat_store_attributes
        return False

    @classmethod
    def from_api(cls, response):
        obj = cls()
        obj.from_response(response)
        return obj

    def from_response(self, response):
        self.from_dict(response)
        self.changed_attributes = []
        return self

    def from_dict(self, dict):
        for attribute, value in dict.items():
            if type_field(attribute):
                continue
            setattr(self, attribute, value)

    @property
    def attributes(self):
        res = {}
        for name, value in self.__dict__.items():
            if self.submittable_attribute(name, value):
                res[name] = value
        return res

    def submittable_attribute(self, name, value):
        return name in self.changed_attributes or isinstance(value, FlatStore)

    def __getattribute__(self, attribute):
        value = super(Resource, self).__getattribute__(attribute)
        if timestamp_field(attribute):
            return to_datetime_value(value)
        else:
            return value

    def __setattr__(self, attribute, value):
        if typed_value(value) and not custom_attribute_field(attribute):
            value_to_set = JsonDeserializer(value).deserialize()
        elif self._flat_store_attribute(attribute):
            value_to_set = FlatStore(value)
        elif timestamp_field(attribute) and datetime_value(value):
            value_to_set = time.mktime(value.timetuple())
        else:
            value_to_set = value
        if attribute != 'changed_attributes':
            self.__dict__['changed_attributes'].append(attribute)
        super(Resource, self).__setattr__(attribute, value_to_set)

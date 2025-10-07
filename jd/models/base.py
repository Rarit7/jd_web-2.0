import datetime
from decimal import Decimal

from jd import db


class BaseModel(db.Model):
    __abstract__ = True

    def to_dict(self):
        data = {}
        for k, v in self.__dict__.items():
            if k.startswith('_'):
                continue
            if k == 'replies_info':
                # TODO:过滤回复信息
                continue
            if isinstance(v, datetime.datetime):
                v = v.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(v, Decimal):
                v = float(v)
            elif isinstance(v, (dict, list)):
                # JSON 类型字段（如 extra_info）直接保留原始值，不转换为字符串
                pass
            elif v is not None:
                v = format(v)
            data[k] = v
        return data

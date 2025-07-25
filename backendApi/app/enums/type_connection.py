from enum import Enum


class TypeConnection(Enum):
    MySQL = "mysql"
    MongoDB = "mongo"
    File = "file"
    Elastic = "elastic"
    Api = "api"
    PTX = "ptx"

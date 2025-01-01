from abc import abstractmethod

from qcflow.entities._qcflow_object import _QCFlowObject


class _ModelRegistryEntity(_QCFlowObject):
    @classmethod
    @abstractmethod
    def from_proto(cls, proto):
        pass

    def __eq__(self, other):
        return dict(self) == dict(other)

from typing import Dict, Optional


class Issue:
    def __init__(self, resource: str):
        self._resource = resource

    @property
    def issue(self) -> str:
        return type(self).__name__

    @property
    def resource(self) -> str:
        return self._resource

    @property
    def help(self) -> Optional[str]:
        pass

    def to_json(self) -> Dict[str, Optional[str]]:
        return {"issue": self.issue, "resource": self.resource, "help": self.help}

"""
Type aliases for domain-specific identifiers.

Using NewType for type safety without runtime overhead.
"""

from typing import NewType

EntityId = NewType("EntityId", str)
UNII = NewType("UNII", str)
RxCUI = NewType("RxCUI", str)
NDC = NewType("NDC", str)
ApplicationNumber = NewType("ApplicationNumber", str)
SPLId = NewType("SPLId", str)
CASNumber = NewType("CASNumber", str)

__version__ = '0.1'

import ndict as _ndict
import sndict as _sndict

NestedDict = ndict = _ndict.NestedDict
StructuredNestedDict = sn_dict = _sndict.StructuredNestedDict

__all__ = (
    'ndict', 'NestedDict',
    'sn_dict', 'StructuredNestedDict',
)

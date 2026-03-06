# Get parent of parent
import os, sys
pp = os.path.realpath(__file__)
for _ in range(2): 
    pp = os.path.dirname(pp)

#Add API root to path
sys.path.append(os.path.join(pp))

from utils.validate import validate_keys_strict

class Emissions:
    def __init__(self, EFsyn={'iso':3.73}, EFpl={'apin':0.021,'dlim':0.017}, bexp=[0.13,0.1,0.1,0.1,0.08,0.13,0.1,0.1,0.13,0.17,0.17,0.17,0.1],EFno=0.05):
        self.EF_order = [
                'iso',
                'apin',
                'bpin',
                'dlim',
                'omt',
                'bcar',
                'afar',
                'osqt',
                'meoh',
                'acetaldehyde',
                'acetone',
                'mvk-mcr',
                'mbo',
                'oVOC',
        ]
        self.EFsyn = EFsyn
        self.EFpl  = EFpl
        self.bexp  = bexp
        self.EFno  = EFno

        self._validate()

    def _validate(self):
        if not isinstance(self.bexp, (list,tuple)):
            raise TypeError("bexp must be list or tuple")
        if len(self.bexp) != 13:
            raise ValueError(f"Length of bexp ({len(self.bexp)}) must be equal to 13")

        # Allow dict, list, or tuple
        if isinstance(self.EFsyn, (list, tuple)):
            if len(self.EFpl) != 14:
                raise ValueError("EFsyn list/tuple must have length 14")
        
            # Convert to dictionary using EF_order
            self.EFsyn = dict(zip(self.EF_order, self.EFsyn))
        
        elif not isinstance(self.EFsyn, dict):
            raise TypeError("EFsyn must be dict, list, or tuple")
        
        # Validate keys strictly
        validate_keys_strict(self.EFsyn, self.EF_order)
        
        # Allow dict, list, or tuple
        if isinstance(self.EFpl, (list, tuple)):
            if len(self.EFpl) != 14:
                raise ValueError("EFpl list/tuple must have length 14")
        
            # Convert to dictionary using EF_order
            self.EFpl = dict(zip(self.EF_order, self.EFpl))
        
        elif not isinstance(self.EFpl, dict):
            raise TypeError("EFpl must be dict, list, or tuple")
        
        # Validate keys strictly
        validate_keys_strict(self.EFpl, self.EF_order)

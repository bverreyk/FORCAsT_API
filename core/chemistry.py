class Chemistry:
    def __init__(self,ichem=0, impmpo=0):
        self.ichem = ichem
        self.impmpo = impmpo

    def to_dict(self):
        return self.__dict__.copy()

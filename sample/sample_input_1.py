class Base1:
    def __init__(self, name):
        self._name = name
        self.area = 0
        self.__test = "test"

    def test(self):
        pass

    def __private(self):
        print("private")

    def test2(self):
        pass

class Base2:
    pass

class A1(Base1):
    def test2(self):
        self.area = 1
        pass

    def test4(self):
        pass

    def _t_protected():
        print("protected")

class A2(Base1):
    pass

class B1(A1):
    class_attribute = "test"

class C1(B1):
    def test(self):
        pass

    def test3(self):
        pass
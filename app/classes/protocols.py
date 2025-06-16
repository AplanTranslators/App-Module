import re
from typing import Tuple, List
from ..classes.parametrs import ParametrArray
from ..classes.basic import Basic, BasicArray

from ..classes.element_types import ElementsTypes


class BodyElement(Basic):
    def __init__(
        self,
        identifier: str,
        pointer_to_related: Basic | None = None,
        element_type: ElementsTypes = ElementsTypes.NONE_ELEMENT,
        parametrs: ParametrArray = ParametrArray(),
    ):
        super().__init__(identifier, (0, 0), element_type)
        self.parametrs = parametrs
        self.pointer_to_related = pointer_to_related

    def copy(self):
        element = BodyElement(
            self.identifier, self.pointer_to_related, self.element_type, self.parametrs
        )

        return element

    def getName(self):
        if self.parametrs:
            if self.parametrs.getLen() == 0:
                return self.identifier
            else:
                return "{0}({1})".format(self.identifier, str(self.parametrs))
        else:
            return self.identifier


class BodyElementArray(BasicArray):
    def __init__(self, element_type: ElementsTypes = ElementsTypes.NONE_ELEMENT):
        super().__init__(BodyElement)
        self.element_type = element_type

    def copy(self):
        new_aray: BodyElementArray = BodyElementArray(BodyElement)
        for element in self.getElements():
            new_aray.addElement(element.copy())
        new_aray.element_type = self.element_type
        return new_aray

    def getElementByIndex(self, index) -> BodyElement:
        return self.elements[index]

    def addElement(self, new_element: BodyElement):
        self.elements.append(new_element)
        return self.getLen() - 1

    def getElements(self):
        return self.elements

    def getLen(self):
        return len(self.elements)

    def __str__(self):
        return self.toStr()

    def toStr(self, last_coma=True):
        body_to_str = ""
        brackets = False
        for index, body_element in enumerate(self.elements):
            element_str = body_element.getName()
            protocol_element = False
            if index != 0:
                if self.element_type == ElementsTypes.GENERATE_ELEMENT:
                    body_to_str += " || "
                else:
                    prev_body_element = self.getElementByIndex(index - 1)
                    if body_element.element_type == ElementsTypes.FOREVER_ELEMENT:
                        body_to_str += ";"
                    elif (
                        body_element.element_type == ElementsTypes.IF_CONDITION_RIGTH
                        and prev_body_element.element_type
                        == ElementsTypes.IF_CONDITION_LEFT
                    ):
                        body_to_str += " + "
                    elif (
                        prev_body_element.element_type == ElementsTypes.ACTION_ELEMENT
                        and (
                            body_element.element_type == ElementsTypes.ACTION_ELEMENT
                            or body_element.element_type
                            == ElementsTypes.PROTOCOL_ELEMENT
                        )
                    ):
                        body_to_str += "."
                    else:
                        protocol_element = True
                        body_to_str += ";"

            if body_element.pointer_to_related:
                if not isinstance(body_element.pointer_to_related, BodyElementArray):
                    element_str = re.sub(
                        r"\b{}\b".format(
                            re.escape(body_element.pointer_to_related.identifier)
                        ),
                        body_element.pointer_to_related.getName(),
                        element_str,
                    )
                else:
                    element_str = body_element.pointer_to_related.toStr(False)

            if body_element.element_type == ElementsTypes.FOREVER_ELEMENT:
                body_to_str += "{" + element_str + "}"
            elif protocol_element == False:
                body_to_str += element_str
            else:
                if body_element.element_type == ElementsTypes.IF_CONDITION_LEFT:
                    brackets = True
                    body_to_str += "(" + element_str
                else:
                    body_to_str += "(" + element_str + ")"

            if brackets:
                if body_element.element_type == ElementsTypes.IF_CONDITION_RIGTH:
                    body_to_str += element_str + ")"
                    brackets = False

            if index == len(self.elements) - 1 and last_coma:
                body_to_str += ","

        return body_to_str


class Protocol(Basic):
    def __init__(
        self,
        identifier: str,
        source_interval: Tuple[int, int],
        element_type: ElementsTypes = ElementsTypes.NONE_ELEMENT,
        parametrs: ParametrArray | None = None,
    ):
        super().__init__(identifier, source_interval, element_type)
        self.body: BodyElementArray = BodyElementArray()
        self.parametrs: ParametrArray = ParametrArray()
        if parametrs is not None:
            self.parametrs = parametrs

    def copy(self):
        protocol = Protocol(self.identifier, self.source_interval, self.element_type)
        for element in self.body.getElements():
            protocol.body.addElement(element)
        protocol.parametrs = self.parametrs.copy()
        protocol.number = self.number
        return protocol

    def addBody(self, body: BodyElement):
        self.body.addElement(body)

    def getName(self):
        identifier = self.identifier
        if self.number:
            identifier = "{0}_{1}".format(identifier, self.number)
        if self.parametrs.getLen() > 0:
            identifier = "{0}({1})".format(identifier, str(self.parametrs))

        return identifier

    def updateLinks(self, module):
        for index, element in enumerate(self.body.getElements()):
            func_name = self.utils.extractFunctionName(element.identifier)
            if func_name:
                action = module.actions.findElement(func_name)
                if action:
                    self.body[index] = (
                        action,
                        element.element_type,
                        element.element_type,
                    )

    def __str__(self):
        return "{0} = {1}".format(
            self.getName(),
            str(self.body),
        )

    def __repr__(self):
        return f"\tProtocol({self.identifier!r}, {self.sequence!r})\n"


class ProtocolArray(BasicArray):
    def __init__(self):
        super().__init__(Protocol)

    def copy(self):
        new_aray: ProtocolArray = ProtocolArray()
        for element in self.getElements():
            new_aray.addElement(element.copy())
        return new_aray

    def getElementsIE(
        self,
        include: ElementsTypes | None = None,
        exclude: ElementsTypes | None = None,
        include_identifier: str | None = None,
        exclude_identifier: str | None = None,
    ):
        result: ProtocolArray = ProtocolArray()
        elements = self.elements

        if (
            include is None
            and exclude is None
            and include_identifier is None
            and exclude_identifier is None
        ):
            return self.copy()

        for element in elements:
            if include is not None and element.element_type is not include:
                continue
            if exclude is not None and element.element_type is exclude:
                continue
            if (
                include_identifier is not None
                and element.identifier is not include_identifier
            ):
                continue
            if (
                exclude_identifier is not None
                and element.identifier is exclude_identifier
            ):
                continue

            result.addElement(element)

        return result

    def updateLinks(self, module):
        for element in self.getElements():
            element.updateLinks(module)

    def getProtocolsInStrFormat(self):
        result = ""
        for element in self.elements:
            result += "\n"
            result += str(element)
        result = self.string_formater.removeTrailingComma(result)
        return result

    def __repr__(self):
        return f"ProtocolsArray(\n{self.elements!r}\n)"

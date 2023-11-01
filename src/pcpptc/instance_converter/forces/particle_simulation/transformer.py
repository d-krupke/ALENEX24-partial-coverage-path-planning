"""
The physics engine and visualization need specific value ranges to work well.
These transformer help to transform the coordinates back and forth.
"""

import typing
from abc import ABC, abstractmethod

from pymunk import Vec2d


class Transformer(ABC):
    """
    Base class
    """

    def __init__(self):
        pass

    @abstractmethod
    def transform(self, p: Vec2d) -> Vec2d:
        """
        Transforms a coordinate of the source coordinate system to the target coordinate
        system.
        """

    @abstractmethod
    def revert(self, p: Vec2d) -> Vec2d:
        """
        Transforms a coordinate of the target coordinate system back to the target
        coordinate system.
        """

    def __call__(self, *args, **kwargs):
        p = Vec2d(*args) if len(args) == 2 else args[0]
        return self.transform(p)


class ScaleTransformer(Transformer):
    """
    Scales the coordinates by some factor.
    """

    def __init__(self, scaling: float):
        super().__init__()
        self.scaling = scaling

    def transform(self, p: Vec2d) -> Vec2d:
        return p * self.scaling

    def revert(self, p: Vec2d) -> Vec2d:
        return p / self.scaling


class TranslateTransformer(Transformer):
    """
    Translates/shifts the coordinates by some factor
    """

    def __init__(self, translation: Vec2d):
        super().__init__()
        self.translation = translation
        print("translation", translation)

    def transform(self, p: Vec2d) -> Vec2d:
        return p + self.translation

    def revert(self, p: Vec2d) -> Vec2d:
        return p - self.translation


class TransformerChain(Transformer):
    """
    Allows the chaining of multiple transformer
    """

    def __init__(self, transformer: typing.List[Transformer]):
        super().__init__()
        self.transformer = transformer

    def transform(self, p: Vec2d) -> Vec2d:
        for transformer in self.transformer:
            p = transformer.transform(p)
        return p

    def revert(self, p: Vec2d) -> Vec2d:
        for transformer in self.transformer[::-1]:
            p = transformer.revert(p)
        return p


class BoundingBoxTransformer(TransformerChain):
    """
    Transforms coordinates from a source bounding box to a target bounding box.
    Especially used for physics engine to canvas.
    """

    def __init__(
        self,
        source_bb: typing.Tuple[Vec2d, Vec2d],
        target_bb: typing.Tuple[Vec2d, Vec2d],
    ):
        super().__init__([])
        self.source_bb = source_bb
        self.target_bb = target_bb
        print("source", source_bb)
        print("target", target_bb)
        scaler = self._calculate_scale_transformer()
        translater = TranslateTransformer(target_bb[0] - scaler.transform(source_bb[0]))
        self.transformer = [scaler, translater]
        print("lower", self.transform(self.source_bb[0]))
        print("upper", self.transform(self.source_bb[1]))

    def _calculate_scale_transformer(self):
        source_size = self.source_bb[1] - self.source_bb[0]
        print(source_size)
        target_size = self.target_bb[1] - self.target_bb[0]
        print(target_size)
        scale = min(target_size[i] / source_size[i] for i in [0, 1])
        return ScaleTransformer(scale)

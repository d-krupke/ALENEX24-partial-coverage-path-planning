class FixedEdges:
    class _EdgeRepr:
        def __init__(self, v, w):
            self.v = min(v, w)
            self.w = max(v, w)

        def __hash__(self):
            return hash(self.as_tuple())

        def as_tuple(self):
            return (self.v, self.w)

        def __eq__(self, other):
            return self.as_tuple() == other.as_tuple()

        def other(self, v):
            if self.v == v:
                return self.w
            elif self.w == v:
                return self.v
            msg = "v is not in edge"
            raise ValueError(msg)

    def __bool__(self):
        return len(self._fixed_edges) > 0

    def __init__(self, area, fractional_solution):
        self._fixed_edges = {}
        for v in area:
            for vp, value in fractional_solution.at_vertex(v).items():
                for n in vp.endpoints():
                    if n not in area:
                        e = self._EdgeRepr(v, n)
                        self._fixed_edges[e] = self._fixed_edges.get(e, 0) + value

    def __getitem__(self, item):
        e = self._EdgeRepr(item[0], item[1])
        return self._fixed_edges.get(e, 0)

    def at_vertex(self, v):
        for e, n in self._fixed_edges.items():
            if v in e.as_tuple():
                yield e.other(v), n

    def items(self):
        for e, _n in self._fixed_edges.items():
            yield e.as_tuple(),

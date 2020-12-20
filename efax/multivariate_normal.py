from __future__ import annotations

from typing import Iterable

import numpy as np
from jax import numpy as jnp
from tjax import RealArray, Shape, dataclass

from .exponential_family import ExpectationParametrization, NaturalParametrization

__all__ = ['MultivariateNormalNP', 'MultivariateNormalEP']


def _broadcasted_outer(x: RealArray) -> RealArray:
    return jnp.einsum("...i,...j->...ij", x, x)


@dataclass
class MultivariateNormalNP(NaturalParametrization['MultivariateNormalEP']):
    mean_times_precision: RealArray
    negative_half_precision: RealArray

    # Implemented methods --------------------------------------------------------------------------
    def shape(self) -> Shape:
        return self.mean_times_precision.shape[:-1]

    def log_normalizer(self) -> RealArray:
        eta = self.mean_times_precision
        k = eta.shape[-1]
        h_inv = jnp.linalg.inv(self.negative_half_precision)
        a = jnp.einsum("...i,...ij,...j", eta, h_inv, eta)
        s, ld = jnp.linalg.slogdet(-self.negative_half_precision)
        return -0.25 * a - 0.5 * ld + 0.5 * k * jnp.log(np.pi)

    def to_exp(self) -> MultivariateNormalEP:
        h_inv = jnp.linalg.inv(self.negative_half_precision)
        h_inv_times_eta = jnp.einsum("...ij,...j->...i", h_inv, self.mean_times_precision)
        mean = -0.5 * h_inv_times_eta
        second_moment = 0.25 * _broadcasted_outer(h_inv_times_eta) - 0.5 * h_inv
        return MultivariateNormalEP(mean, second_moment)

    def carrier_measure(self, x: RealArray) -> RealArray:
        return jnp.zeros(x.shape)

    def sufficient_statistics(self, x: RealArray) -> MultivariateNormalEP:
        return MultivariateNormalEP(x, jnp.square(x))

    @classmethod
    def field_axes(cls) -> Iterable[int]:
        yield 1
        yield 2


@dataclass
class MultivariateNormalEP(ExpectationParametrization[MultivariateNormalNP]):
    mean: RealArray
    second_moment: RealArray

    # Implemented methods --------------------------------------------------------------------------
    def shape(self) -> Shape:
        return self.mean.shape[:-1]

    def to_nat(self) -> MultivariateNormalNP:
        variance = self.second_moment - _broadcasted_outer(self.mean)
        inv_variance = jnp.linalg.inv(variance)
        return MultivariateNormalNP(self.mean * inv_variance, -0.5 * inv_variance)

    def expected_carrier_measure(self) -> RealArray:
        return jnp.zeros(self.shape())
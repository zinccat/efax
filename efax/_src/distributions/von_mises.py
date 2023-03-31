from __future__ import annotations

import math

import jax.numpy as jnp
from jax.nn import softplus
from tjax import JaxRealArray, Shape, inverse_softplus
from tjax.dataclasses import dataclass
from typing_extensions import override

from ..exp_to_nat import ExpToNat
from ..has_entropy import HasEntropyEP, HasEntropyNP
from ..multidimensional import Multidimensional
from ..natural_parametrization import NaturalParametrization
from ..parameter import VectorSupport, distribution_parameter
from ..tools import iv_ratio, log_ive

__all__ = ['VonMisesFisherNP', 'VonMisesFisherEP']


@dataclass
class VonMisesFisherNP(HasEntropyNP,
                       NaturalParametrization['VonMisesFisherEP', JaxRealArray],
                       Multidimensional):
    mean_times_concentration: JaxRealArray = distribution_parameter(VectorSupport())

    # Implemented methods --------------------------------------------------------------------------
    @property
    @override
    def shape(self) -> Shape:
        return self.mean_times_concentration.shape[:-1]

    @override
    def log_normalizer(self) -> JaxRealArray:
        half_k = self.dimensions() * 0.5
        kappa = jnp.linalg.norm(self.mean_times_concentration, 2, axis=-1)
        return (kappa
                - (half_k - 1.0) * jnp.log(kappa)
                + half_k * jnp.log(2.0 * math.pi)
                + log_ive(half_k - 1.0, kappa))

    @override
    def to_exp(self) -> VonMisesFisherEP:
        q = self.mean_times_concentration
        kappa: JaxRealArray = jnp.linalg.norm(q, 2, axis=-1, keepdims=True)
        return VonMisesFisherEP(
            jnp.where(kappa == 0.0,  # noqa: PLR2004
                      q,
                      q * (_a_k(self.dimensions(), kappa) / kappa)))

    @override
    def carrier_measure(self, x: JaxRealArray) -> JaxRealArray:
        return jnp.zeros(self.shape)

    @override
    def sufficient_statistics(self, x: JaxRealArray) -> VonMisesFisherEP:
        return VonMisesFisherEP(x)

    @override
    def dimensions(self) -> int:
        return self.mean_times_concentration.shape[-1]

    # New methods ----------------------------------------------------------------------------------
    def to_kappa_angle(self) -> tuple[JaxRealArray, JaxRealArray]:
        if self.dimensions() != 2:  # noqa: PLR2004
            raise ValueError
        kappa: JaxRealArray = jnp.linalg.norm(self.mean_times_concentration, axis=-1)
        angle = jnp.where(kappa == 0.0,  # noqa: PLR2004
                          0.0,
                          jnp.arctan2(self.mean_times_concentration[..., 1],
                                      self.mean_times_concentration[..., 0]))
        return kappa, angle


@dataclass
class VonMisesFisherEP(HasEntropyEP[VonMisesFisherNP],
                       ExpToNat[VonMisesFisherNP, JaxRealArray], Multidimensional):
    mean: JaxRealArray = distribution_parameter(VectorSupport())

    # Implemented methods --------------------------------------------------------------------------
    @property
    @override
    def shape(self) -> Shape:
        return self.mean.shape[:-1]

    @classmethod
    @override
    def natural_parametrization_cls(cls) -> type[VonMisesFisherNP]:
        return VonMisesFisherNP

    @override
    def expected_carrier_measure(self) -> JaxRealArray:
        return jnp.zeros(self.shape)

    @override
    def initial_search_parameters(self) -> JaxRealArray:
        mu: JaxRealArray = jnp.linalg.norm(self.mean, 2, axis=-1)
        # 0 <= mu <= 1.0
        initial_kappa = jnp.where(mu == 1.0,  # noqa: PLR2004
                                  jnp.inf,
                                  (mu * self.dimensions() - mu ** 3) / (1.0 - mu ** 2))
        return inverse_softplus(initial_kappa)

    @override
    def search_to_natural(self, search_parameters: JaxRealArray) -> VonMisesFisherNP:
        kappa = softplus(search_parameters)
        mu = jnp.linalg.norm(self.mean, 2, axis=-1)
        q = self.mean * (kappa / mu)[..., jnp.newaxis]
        return VonMisesFisherNP(q)

    @override
    def search_gradient(self, search_parameters: JaxRealArray) -> JaxRealArray:
        kappa = softplus(search_parameters)
        mu = jnp.linalg.norm(self.mean, 2, axis=-1)
        return _a_k(self.dimensions(), kappa) - mu

    @override
    def dimensions(self) -> int:
        return self.mean.shape[-1]


# Private functions --------------------------------------------------------------------------------
def _a_k(k: float | JaxRealArray, kappa: float | JaxRealArray) -> JaxRealArray:
    return iv_ratio(k * 0.5, kappa)

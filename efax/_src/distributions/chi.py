from __future__ import annotations

import jax.numpy as jnp
from jax.scipy import special as jss
from tjax import Array, JaxRealArray
from tjax.dataclasses import dataclass
from typing_extensions import override

from ..parameter import ScalarSupport, distribution_parameter
from ..transformed_parametrization import (TransformedExpectationParametrization,
                                           TransformedNaturalParametrization)
from .chi_square import ChiSquareEP, ChiSquareNP

__all__ = ['ChiNP', 'ChiEP']


@dataclass
class ChiNP(TransformedNaturalParametrization[ChiSquareNP, ChiSquareEP, 'ChiEP', JaxRealArray]):
    k_over_two_minus_one: JaxRealArray = distribution_parameter(ScalarSupport())

    # Implemented methods --------------------------------------------------------------------------
    @override
    def base_distribution(self) -> ChiSquareNP:
        return ChiSquareNP(self.k_over_two_minus_one)

    @override
    def create_expectation(self, expectation_parametrization: ChiSquareEP) -> ChiEP:
        return ChiEP(expectation_parametrization.mean_log)

    @override
    def sample_to_base_sample(self, x: Array) -> JaxRealArray:
        return jnp.square(x)

    @override
    def carrier_measure(self, x: JaxRealArray) -> JaxRealArray:
        return jnp.log(2.0 * x) - jnp.square(x) * 0.5


@dataclass
class ChiEP(TransformedExpectationParametrization[ChiSquareEP, ChiSquareNP, ChiNP]):
    mean_log: JaxRealArray = distribution_parameter(ScalarSupport())

    # Implemented methods --------------------------------------------------------------------------
    @classmethod
    @override
    def natural_parametrization_cls(cls) -> type[ChiNP]:
        return ChiNP

    @override
    def base_distribution(self) -> ChiSquareEP:
        return ChiSquareEP(self.mean_log)

    @override
    def create_natural(self, natural_parametrization: ChiSquareNP) -> ChiNP:
        return ChiNP(natural_parametrization.k_over_two_minus_one)

    @override
    def expected_carrier_measure(self) -> JaxRealArray:
        q = self.to_nat()
        k_over_two = q.k_over_two_minus_one + 1.0
        return -1.0 * k_over_two + 0.5 * jss.digamma(k_over_two) + 1.5 * jnp.log(2.0)

from __future__ import annotations

import operator
from typing import Any, Generic, TypeVar, final

from jax.tree_util import tree_map
from tjax import RealArray, jit

from .natural_parametrization import NaturalParametrization
from .parametrization import Parametrization
from .tools import parameters_dot_product

__all__ = ['ExpectationParametrization']


NP = TypeVar('NP', bound=NaturalParametrization[Any, Any])


class ExpectationParametrization(Parametrization, Generic[NP]):
    """The expectation parametrization of an exponential family distribution.

    This class also doubles as the sufficient statistics of an exponential family distribution.

    The motivation for the expectation parametrization is combining independent and identically
    distributed observations into the maximum likelihood distribution.  In the expectation
    parametrization, this is an expected value.
    """
    # Abstract methods -----------------------------------------------------------------------------
    @classmethod
    def natural_parametrization_cls(cls) -> type[NP]:
        raise NotImplementedError

    def to_nat(self) -> NP:
        """The corresponding natural parameters."""
        raise NotImplementedError

    def expected_carrier_measure(self) -> RealArray:
        """The expected carrier measure of the distribution.

        This is the missing term from the inner product between the observed distribution and the
        predicted distribution.  Often, it is just jnp.zeros(self.shape).
        """
        raise NotImplementedError

    # Final methods --------------------------------------------------------------------------------
    @jit
    @final
    def cross_entropy(self, q: NP) -> RealArray:
        """The cross entropy.

        Args:
            q: The natural parameters of the prediction.
        """
        return (-parameters_dot_product(q, self)
                + q.log_normalizer()
                - self.expected_carrier_measure())

    @jit
    @final
    def entropy(self) -> RealArray:
        """The Shannon entropy.

        This can be quite slow since it depends on a conversion to natural parameters.
        """
        return self.cross_entropy(self.to_nat())

    @jit
    @final
    def kl_divergence(self, q: NP) -> RealArray:
        """The Kullback-Leibler divergence.

        This can be quite slow since it depends on a conversion to natural parameters.

        Args:
            self: The expectation parameters of the first distribution.
            q: The natural parameters of second destribution.
        """
        self_nat = self.to_nat()
        difference = tree_map(operator.sub, self_nat, q)
        return (parameters_dot_product(difference, self)
                + q.log_normalizer()
                - self_nat.log_normalizer())

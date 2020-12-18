from typing import Any

from chex import Array
from jax import numpy as jnp
from jax.nn import softplus
from jax.scipy import special as jss
from tjax import RealArray, Shape

from .exp_to_nat import ExpToNat
from .exponential_family import ExponentialFamily

__all__ = ['Beta', 'Dirichlet']


class Dirichlet(ExpToNat, ExponentialFamily):

    def __init__(self, num_parameters: int, **kwargs: Any):
        if not isinstance(num_parameters, int):
            raise TypeError
        if num_parameters < 2:
            raise ValueError
        observation_shape: Shape
        if num_parameters == 2:
            observation_shape = ()
        else:
            observation_shape = (num_parameters - 1,)
        super().__init__(num_parameters=num_parameters,
                         observation_shape=observation_shape,
                         **kwargs)

    # Magic methods --------------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (f"{type(self).__name__}(shape={self.shape}, "
                f"num_parameters={self.num_parameters})")

    # Implemented methods --------------------------------------------------------------------------
    def log_normalizer(self, q: RealArray) -> RealArray:
        return (jnp.sum(jss.gammaln(q + 1.0), axis=-1)
                - jss.gammaln(jnp.sum(q, axis=-1) + q.shape[-1]))

    def nat_to_exp(self, q: RealArray) -> RealArray:
        return (jss.digamma(q + 1.0)
                - jss.digamma(jnp.sum(q, axis=-1, keepdims=True) + q.shape[-1]))

    def sufficient_statistics(self, x: RealArray) -> RealArray:
        if self.num_parameters == 2:
            return jnp.stack([jnp.log(x), jnp.log(1.0 - x)], axis=-1)
        one_minus_total_x = 1.0 - jnp.sum(x, axis=-1, keepdims=True)
        return jnp.append(jnp.log(x), jnp.log(one_minus_total_x), axis=-1)

    # Overridden methods ---------------------------------------------------------------------------
    def exp_to_nat_transform_q(self, transformed_q: Array) -> Array:
        # Run Newton's method on the whole real line.
        return softplus(transformed_q) - 1.0


class Beta(Dirichlet):
    """
    The Beta distribution.

    The best way to interpret the parameters of the beta distribution are that an observation x in
    [0, 1] represents the Bernoulli probability that outcome 0 (out of {0, 1}) is realized.  In this
    way, the Beta class coincides with a special case of the Dirichlet class.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(num_parameters=2, **kwargs)

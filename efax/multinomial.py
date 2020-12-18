from typing import Any, Optional

import numpy as np
from jax import numpy as jnp
from jax.scipy import special as jss
from tjax import RealArray, Shape

from .dirichlet import Dirichlet
from .exponential_family import ExponentialFamily

__all__ = ['Multinomial']


class Multinomial(ExponentialFamily):

    def __init__(self, *, num_parameters: int, **kwargs: Any) -> None:
        if num_parameters < 0:
            raise ValueError
        observation_shape: Shape
        if num_parameters == 1:
            observation_shape = ()
        else:
            observation_shape = (num_parameters,)
        super().__init__(num_parameters=num_parameters,
                         observation_shape=observation_shape,
                         **kwargs)

    # Magic methods --------------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (f"{type(self).__name__}(shape={self.shape}, "
                f"num_parameters={self.num_parameters})")

    # Implemented methods --------------------------------------------------------------------------
    def log_normalizer(self, q: RealArray) -> RealArray:
        max_q = jnp.maximum(0.0, jnp.amax(q, axis=-1))
        q_minus_max_q = q - max_q[..., np.newaxis]
        log_scaled_A = jnp.logaddexp(-max_q, jss.logsumexp(q_minus_max_q, axis=-1))
        return max_q + log_scaled_A

    def nat_to_exp(self, q: RealArray) -> RealArray:
        max_q = jnp.maximum(0.0, jnp.amax(q, axis=-1))
        q_minus_max_q = q - max_q[..., np.newaxis]
        log_scaled_A = jnp.logaddexp(-max_q, jss.logsumexp(q_minus_max_q, axis=-1))
        return jnp.exp(q_minus_max_q - log_scaled_A[..., np.newaxis])

    def exp_to_nat(self, p: RealArray) -> RealArray:
        p_k = 1.0 - jnp.sum(p, axis=-1, keepdims=True)
        return jnp.log(p / p_k)

    def sufficient_statistics(self, x: RealArray) -> RealArray:
        return x

    # New methods ----------------------------------------------------------------------------------
    @staticmethod
    def nat_to_probability(q: RealArray) -> RealArray:
        max_q = jnp.maximum(0.0, jnp.amax(q, axis=-1))
        q_minus_max_q = q - max_q[..., np.newaxis]
        log_scaled_A = jnp.logaddexp(-max_q, jss.logsumexp(q_minus_max_q, axis=-1))
        p = jnp.exp(q_minus_max_q - log_scaled_A[..., np.newaxis])
        final_p = 1.0 - jnp.sum(p, axis=-1, keepdims=True)
        return jnp.append(p, final_p, axis=-1)

    @staticmethod
    def nat_to_surprisal(q: RealArray) -> RealArray:
        total_p = Multinomial.nat_to_probability(q)
        return -jnp.log(total_p)

    # Overridden methods ---------------------------------------------------------------------------
    def conjugate_prior_family(self) -> Optional[ExponentialFamily]:
        return Dirichlet(self.num_parameters + 1)

    def conjugate_prior_distribution(self, p: RealArray, n: RealArray) -> RealArray:
        reshaped_n = n[..., np.newaxis]
        final_p = 1.0 - jnp.sum(p, axis=-1, keepdims=True)
        return reshaped_n * jnp.append(p, final_p, axis=-1)

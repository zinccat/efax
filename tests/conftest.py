from __future__ import annotations

import subprocess
from collections.abc import Generator
from typing import Any

import numpy as np
import pytest
from jax.experimental import enable_x64
from jax.random import KeyArray, PRNGKey
from numpy.random import Generator as NumpyGenerator

from efax import HasConjugatePrior, HasGeneralizedConjugatePrior, Samplable

from .create_info import create_infos
from .distribution_info import DistributionInfo


@pytest.fixture(autouse=True)
def _jax_enable64() -> Generator[None, None, None]:
    with enable_x64():
        yield


def pytest_addoption(parser: Any) -> None:
    parser.addoption('--distribution', action='store', default=None)


@pytest.fixture()
def generator() -> NumpyGenerator:
    return np.random.default_rng(123)


@pytest.fixture()
def key() -> KeyArray:
    return PRNGKey(123)


@pytest.fixture(scope='session')
def _configure_numpy() -> Generator[None, None, None]:
    line_width = [int(x)
                  for x in subprocess.check_output(['stty', 'size']).decode().split()][1]

    with np.errstate(all='raise'):
        with np.printoptions(precision=10, linewidth=line_width):
            yield


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "nondistribution: mark a test as not related to a particular distribution")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--distribution") is None:
        return
    skip_non_distribution = pytest.mark.skip(reason="Distribution selected")
    for item in items:
        if "nondistribution" in item.keywords:
            item.add_marker(skip_non_distribution)


_all_infos = create_infos()


@pytest.fixture()
def distribution_name(request: Any) -> None | str:
    return request.config.getoption("--distribution")


@pytest.fixture(scope='session', params=_all_infos)
def distribution_info(request: Any) -> DistributionInfo[Any, Any, Any]:
    distribution_name: str | None = request.config.getoption('--distribution')
    info = request.param
    assert isinstance(info, DistributionInfo)
    info.skip_if_deselected(distribution_name)
    return request.param


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if 'sampling_distribution_info' in metafunc.fixturenames and 'natural' in metafunc.fixturenames:
        p = [(info, natural)
             for info in _all_infos
             for natural in [False, True]
             if issubclass(info.nat_class() if natural else info.exp_class(), Samplable)]
        metafunc.parametrize("sampling_distribution_info, natural", p)
    if 'cp_distribution_info' in metafunc.fixturenames:
        q = [info
             for info in _all_infos
             if issubclass(info.exp_class(), HasConjugatePrior)]
        metafunc.parametrize("cp_distribution_info", q)
    if 'gcp_distribution_info' in metafunc.fixturenames:
        q = [info
             for info in _all_infos
             if issubclass(info.exp_class(), HasGeneralizedConjugatePrior)]
        metafunc.parametrize("gcp_distribution_info", q)

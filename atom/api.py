# -*- coding: utf-8 -*-

"""Automated Tool for Optimized Modelling (ATOM).

Author: tvdboom
Description: Module containing the API classes.

"""

# Standard packages
import pickle
import pandas as pd
from typeguard import typechecked
from typing import Optional, Union

# Own modules
from .atom import ATOM
from .basetransformer import BaseTransformer
from .utils import ARRAY_TYPES, merge


# Functions ================================================================= >>

@typechecked
def ATOMModel(
    estimator,
    acronym: str = None,
    fullname: str = None,
    needs_scaling: bool = False,
    type: str = "kernel",
):
    """Convert an estimator to a model that can be ingested by ATOM's pipeline.

    Add the relevant attributes to the estimator so that they can be used
    when initializing the CustomModel class.

    Parameters
    ----------
    estimator: class
        Model's estimator. Can be a class or an instance.

    acronym: str, optional (default=None)
        Model's acronym. Used to call the `model` from the training instance.
        If None, the estimator's name will be used (not recommended).

    fullname: str, optional (default=None)
        Full model's name. If None, the estimator's name will be used.

    needs_scaling: bool, optional (default=False)
        Whether the model needs scaled features. Can not be True for
        deep learning datasets.

    type: str, optional (default="kernel")
        Model's type. Used to select shap's explainer. Choose from:
            - "linear" for linear models.
            - "tree" for tree-based models.
            - "kernel" for the remaining models.

    """
    if acronym:
        estimator.acronym = acronym
    if fullname:
        estimator.fullname = fullname
    estimator.needs_scaling = needs_scaling
    if type not in ("linear", "tree", "kernel"):
        raise ValueError(
            "Invalid value for the type parameter."
            " Choose from: linear, tree or kernel."
        )
    else:
        estimator.type = type

    return estimator


@typechecked
def ATOMLoader(
    filename: str,
    data: Optional[Union[ARRAY_TYPES]] = None,
    transform_data: bool = True,
    verbose: Optional[int] = None,
):
    """Load a class instance from a pickle file.

    If the file is a `training` instance that was saved using `save_data=False`,
    you can load new data into it. If the file is an `atom` instance, you can also
    apply all data transformations in the pipeline to the provided data.

    Parameters
    ----------
    filename: str
        Name of the pickle file to load.

    data: tuple of indexables or None, optional (default=None)
        Tuple containing the features and target. Only use this parameter if the
        file is a `training` instance that was saved using `save_data=False`.
        Allowed formats are:
            - X, y
            - train, test
            - X_train, X_test, y_train, y_test
            - (X_train, y_train), (X_test, y_test)

        X, train, test: dict, list, tuple, np.array or pd.DataFrame
            Feature set with shape=(n_features, n_samples). If no
            y is provided, the last column is used as target.

        y: int, str or array-like
            - If int: Index of the target column in X.
            - If str: Name of the target column in X.
            - Else: Target column with shape=(n_samples,).

    transform_data: bool, optional (default=True)
        If False, the `data` is left as provided. If True, the `data` is transformed
        through all the steps in the instance's pipeline. This parameter is ignored
        if the loaded file is not an `atom` instance.

    verbose: int or None, optional (default=None)
        Verbosity level of the transformations applied on the new data. If None,
        use the verbosity from the loaded instance. This parameter is ignored if
        `transform_data=False`.

    """
    # Check verbose parameter
    if verbose and (verbose < 0 or verbose > 2):
        raise ValueError(
            "Invalid value for the verbose parameter."
            f"Value should be between 0 and 2, got {verbose}."
        )

    with open(filename, "rb") as f:
        cls = pickle.load(f)

    if data is not None:
        if not hasattr(cls, "_branches"):
            raise TypeError(
                "Data is provided but the class is not an atom nor "
                f"training instance, got {cls.__class__.__name__}."
            )

        elif cls.pipeline.data is not None:
            raise ValueError(
                f"The loaded {cls.__class__.__name__} instance already contains data!"
            )

        # Prepare the provided data
        data, idx = cls._get_data_and_idx(data, use_n_rows=transform_data)

        for key, pl in cls._branches.items():
            pl.data, pl.idx = data, idx

            if transform_data:
                # Transform the data through all transformers in the pipeline
                for est in [i for i in pl.estimators if hasattr(i, "transform")]:
                    if verbose is not None:
                        vb = est.get_params()["verbose"]  # Save original verbosity
                        est.set_params(verbose=verbose)

                    # Some transformations are only applied on the training set
                    if est.__class__.__name__ in ["Outliers", "Balancer"]:
                        X, y = est.transform(cls.X_train, cls.y_train)
                        cls.dataset = pd.concat([merge(X, y), cls.test])
                    else:
                        X = est.transform(cls.X, cls.y)

                        # Data changes depending if the estimator returned X or X, y
                        if isinstance(X, tuple):
                            cls.dataset = merge(*X)
                        else:
                            cls.dataset = merge(X, cls.y)

                    cls.dataset.reset_index(drop=True, inplace=True)
                    if verbose is not None:
                        est.verbose = vb  # Reset the original verbosity

    cls.log(f"{cls.__class__.__name__} loaded successfully!", 1)

    return cls


# Classes =================================================================== >>

class ATOMClassifier(BaseTransformer, ATOM):
    """ATOM class for classification tasks.

    Parameters
    ----------
    *arrays: sequence of indexables
        Dataset containing the features and target. Allowed formats are:
            - X, y
            - train, test
            - X_train, X_test, y_train, y_test
            - (X_train, y_train), (X_test, y_test)

        X, train, test: dict, list, tuple, np.array or pd.DataFrame
            Feature set with shape=(n_features, n_samples). If
            no y is provided, the last column is used as target.

        y: int, str or array-like
            - If int: Index of the target column in X.
            - If str: Name of the target column in X.
            - Else: Target column with shape=(n_samples,).

    n_rows: int or float, optional (default=1)
        - If <=1: Fraction of the dataset to use.
        - If >1: Number of rows to use (only if input is X, y).

    test_size: int, float, optional (default=0.2)
        - If <=1: Fraction of the dataset to include in the test set.
        - If >1: Number of rows to include in the test set.

        This parameter is ignored if the train and test set are provided.

    n_jobs: int, optional (default=1)
        Number of cores to use for parallel processing.
            - If >0: Number of cores to use.
            - If -1: Use all available cores.
            - If <-1: Use number of cores - 1 - n_jobs.

        Beware that using multiple processes on the same machine may
        cause memory issues for large datasets.

    verbose: int, optional (default=0)
        Verbosity level of the class. Possible values are:
            - 0 to not print anything.
            - 1 to print basic information.
            - 2 to print detailed information.

    warnings: bool or str, optional (default=True)
        - If True: Default warning action (equal to "default" when string).
        - If False: Suppress all warnings (equal to "ignore" when string).
        - If str: One of the possible actions in python's warnings environment.

        Note that changing this parameter will affect the `PYTHONWARNINGS`
        environment.

        Note that ATOM can't manage warnings that go directly from C/C++ code
        to the stdout/stderr.

    logger: bool, str, class or None, optional (default=None)
        - If None: Doesn't save a logging file.
        - If bool: True for logging file with default name. False for no logger.
        - If str: name of the logging file. "auto" for default name.
        - If class: python "Logger" object.

        Note that warnings will not be saved to the logger in any case.

    random_state: int or None, optional (default=None)
        Seed used by the random number generator. If None, the random
        number generator is the `RandomState` instance used by `numpy.random`.

    """

    @typechecked
    def __init__(
        self,
        *arrays,
        n_rows: Union[int, float] = 1,
        test_size: float = 0.2,
        logger: Optional[Union[str, callable]] = None,
        n_jobs: int = 1,
        warnings: Union[bool, str] = True,
        verbose: int = 0,
        random_state: Optional[int] = None,
    ):
        super().__init__(
            n_jobs=n_jobs,
            verbose=verbose,
            warnings=warnings,
            logger=logger,
            random_state=random_state,
        )

        self.goal = "classification"
        ATOM.__init__(self, arrays, n_rows=n_rows, test_size=test_size)


class ATOMRegressor(BaseTransformer, ATOM):
    """ATOM class for regression tasks.

    Parameters
    ----------
    *arrays: sequence of indexables
        Dataset containing the features and target. Allowed formats are:
            - X, y
            - train, test
            - X_train, X_test, y_train, y_test
            - (X_train, y_train), (X_test, y_test)

        X, train, test: dict, list, tuple, np.array or pd.DataFrame
            Feature set with shape=(n_features, n_samples). If no
            y is provided, the last column is used as target.

        y: int, str or array-like
            - If int: Index of the target column in X.
            - If str: Name of the target column in X.
            - Else: Target column with shape=(n_samples,).

    n_rows: int or float, optional (default=1)
        - If <=1: Fraction of the dataset to use.
        - If >1: Number of rows to use (only if input is X, y).

    test_size: int, float, optional (default=0.2)
        - If <=1: Fraction of the dataset to include in the test set.
        - If >1: Number of rows to include in the test set.

        This parameter is ignored if the train and test set are provided.

    n_jobs: int, optional (default=1)
        Number of cores to use for parallel processing.
            - If >0: Number of cores to use.
            - If -1: Use all available cores.
            - If <-1: Use number of cores - 1 - n_jobs.

        Beware that using multiple processes on the same machine may
        cause memory issues for large datasets.

    verbose: int, optional (default=0)
        Verbosity level of the class. Possible values are:
            - 0 to not print anything.
            - 1 to print basic information.
            - 2 to print detailed information.

    warnings: bool or str, optional (default=True)
        - If True: Default warning action (equal to "default" when string).
        - If False: Suppress all warnings (equal to "ignore" when string).
        - If str: One of the possible actions in python's warnings environment.

        Note that changing this parameter will affect the `PYTHONWARNINGS`
        environment.

        Note that ATOM can't manage warnings that go directly from C/C++ code
        to the stdout/stderr.

    logger: bool, str, class or None, optional (default=None)
        - If None: Doesn't save a logging file.
        - If bool: True for logging file with default name. False for no logger.
        - If str: name of the logging file. "auto" for default name.
        - If class: python "Logger" object.

        Note that warnings will not be saved to the logger in any case.

    random_state: int or None, optional (default=None)
        Seed used by the random number generator. If None, the random
        number generator is the `RandomState` instance used by `numpy.random`.

    """

    @typechecked
    def __init__(
        self,
        *arrays,
        n_rows: Union[int, float] = 1,
        test_size: float = 0.2,
        n_jobs: int = 1,
        warnings: Union[bool, str] = True,
        verbose: int = 0,
        logger: Optional[Union[str, callable]] = None,
        random_state: Optional[int] = None,
    ):
        super().__init__(
            n_jobs=n_jobs,
            verbose=verbose,
            warnings=warnings,
            logger=logger,
            random_state=random_state,
        )

        self.goal = "regression"
        ATOM.__init__(self, arrays, n_rows=n_rows, test_size=test_size)

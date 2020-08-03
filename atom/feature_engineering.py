# -*- coding: utf-8 -*-

"""Automated Tool for Optimized Modelling (ATOM).

Author: tvdboom
Description: Module containing the feature selection and generator estimators.

"""

# Standard packages
import numpy as np
import pandas as pd
from typeguard import typechecked
from typing import Optional, Union, Sequence

# Other packages
import featuretools as ft
from featuretools.primitives import make_trans_primitive
from featuretools.variable_types import Numeric
from gplearn.genetic import SymbolicTransformer
from sklearn.base import BaseEstimator
from sklearn.decomposition import PCA
from sklearn.feature_selection import (
    f_classif, f_regression, mutual_info_classif, mutual_info_regression,
    chi2, SelectKBest, SelectFromModel, RFE, RFECV
    )

# Own modules
from .models import MODEL_LIST
from .basetransformer import BaseTransformer
from .data_cleaning import BaseCleaner, Scaler
from .utils import (
    METRIC_ACRONYMS, X_TYPES, Y_TYPES, to_df, check_scaling, check_is_fitted,
    get_model_name, composed, crash, method_to_log
    )
from .plots import FeatureSelectorPlotter


# Functions and variables ================================================== >>

def sqrt(column):
    return np.sqrt(column)


def log(column):
    return np.log(column)


def sin(column):
    return np.sin(column)


def cos(column):
    return np.cos(column)


def tan(column):
    return np.tan(column)


sqrt = make_trans_primitive(sqrt, [Numeric], Numeric)
log = make_trans_primitive(log, [Numeric], Numeric)
sin = make_trans_primitive(sin, [Numeric], Numeric)
cos = make_trans_primitive(cos, [Numeric], Numeric)
tan = make_trans_primitive(tan, [Numeric], Numeric)


# Classes =================================================================== >>

class FeatureGenerator(BaseEstimator, BaseTransformer, BaseCleaner):
    """Apply automated feature engineering.

    Use Deep feature Synthesis or a genetic algorithm to create new combinations
    of existing features to capture the non-linear relations between the original
    features.

    Parameters
    ----------
    strategy: str, optional (default='DFS')
        Strategy to crate new features. Choose from:
            - 'DFS' to use Deep Feature Synthesis.
            - 'GFG' or 'genetic' to use Genetic Feature Generation.

    n_features: int, optional (default=None)
        Number of newly generated features to add to the dataset (if
        strategy='genetic', no more than 1% of the population). If None,
        select all created.

    generations: int, optional (default=20)
        Number of generations to evolve. Only if strategy='genetic'.

    population: int, optional (default=500)
        Number of programs in each generation. Only if strategy='genetic'.

    operators: str, sequence or None, optional (default=None)
        Mathematical operators to apply on the features. None for all. Choose from:
        'add', 'sub', 'mul', 'div', 'sqrt', 'log', 'inv', 'sin', 'cos', 'tan'.

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

    logger: bool, str, class or None, optional (default=None)
        - If None: Doesn't save a logging file.
        - If bool: True for logging file with default name, False for no logger.
        - If string: name of the logging file. 'auto' for default name.
        - If class: python Logger object.

    random_state: int or None, optional (default=None)
        Seed used by the random number generator. If None, the random
        number generator is the RandomState instance used by `np.random`.

    """

    def __init__(self,
                 strategy: str = 'DFS',
                 n_features: Optional[int] = None,
                 generations: int = 20,
                 population: int = 500,
                 operators: Optional[Union[str, Sequence[str]]] = None,
                 n_jobs: int = 1,
                 verbose: int = 0,
                 logger: Optional[Union[bool, str, callable]] = None,
                 random_state: Optional[int] = None):
        super().__init__(n_jobs=n_jobs,
                         verbose=verbose,
                         logger=logger,
                         random_state=random_state)

        # Check Parameters
        if n_features is not None and n_features <= 0:
            raise ValueError("Invalid value for the n_features parameter." +
                             f"Value should be >0, got {n_features}.")

        if strategy.lower() in ('gfg', 'genetic'):
            if population < 100:
                raise ValueError("Invalid value for the population parameter." +
                                 f"Value should be >100, got {population}.")
            if generations < 1:
                raise ValueError("Invalid value for the generations parameter." +
                                 f"Value should be >100, got {generations}.")
            if n_features and n_features > int(0.01 * population):
                raise ValueError("Invalid value for the n_features parameter." +
                                 "Value should be <1% of the population, " +
                                 f"got {n_features}.")
        elif strategy.lower() != 'dfs':
            raise ValueError("Invalid value for the strategy parameter." +
                             "Value should be either 'dfs' or 'genetic', " +
                             f"got {strategy}.")

        # Check operators
        default = ['add', 'sub', 'mul', 'div', 'sqrt', 'log', 'sin', 'cos', 'tan']
        if not operators:  # None or empty list
            operators = default
        else:
            if not isinstance(operators, (list, tuple)):
                operators = [operators]
            for operator in operators:
                if operator not in default:
                    raise ValueError(
                        "Invalid value in the operators parameter, got " +
                        f"{operator}. Choose from: {', '.join(default)}.")

        # Define attributes
        self.strategy = strategy
        self.n_features = n_features
        self.generations = generations
        self.population = population
        self.operators = operators

        self._is_fitted = False
        self.dfs_features = None
        self.symbolic_transformer = None
        self.genetic_features = pd.DataFrame(
            columns=['name', 'description', 'fitness'])

    @composed(crash, method_to_log, typechecked)
    def fit(self, X: X_TYPES, y: Y_TYPES):
        """Fit the data according to the selected strategy.

        Parameters
        ----------
        X: dict, sequence, np.array or pd.DataFrame
            Data containing the features, with shape=(n_samples, n_features).

        y: int, str, sequence, np.array or pd.Series
            - If int: Position of the target column in X.
            - If str: Name of the target column in X.
            - Else: Data target column with shape=(n_samples,).

        Returns
        -------
        self: FeatureGenerator

        """
        X, y = self._prepare_input(X, y)

        self.log("Fitting FeatureGenerator...", 1)

        if self.strategy.lower() == 'dfs':
            # Make an entity set and add the entity
            entity_set = ft.EntitySet(id='atom')
            entity_set.entity_from_dataframe(entity_id='data',
                                             dataframe=X,
                                             make_index=True,
                                             index='index')

            # Get list of transformation primitives
            trans_primitives = []
            for operator in self.operators:
                if operator == 'add':
                    trans_primitives.append('add_numeric')
                elif operator == 'sub':
                    trans_primitives.append('subtract_numeric')
                elif operator == 'mul':
                    trans_primitives.append('multiply_numeric')
                elif operator == 'div':
                    trans_primitives.append('divide_numeric')
                elif operator in ('sqrt', 'log', 'sin', 'cos', 'tan'):
                    trans_primitives.append(eval(operator))

            # Run deep feature synthesis with transformation primitives
            self.dfs_features = ft.dfs(entityset=entity_set,
                                       target_entity='data',
                                       max_depth=1,
                                       features_only=True,
                                       trans_primitives=trans_primitives)

            # Make sure there are enough features (-1 because X has an index column)
            max_features = len(self.dfs_features) - X.shape[1] - 1
            if not self.n_features or self.n_features > max_features:
                self.n_features = max_features

            # Get random indices from the feature list
            idx_old = list(range(X.shape[1]-1))
            idx_new = list(np.random.randint(
                X.shape[1], len(self.dfs_features), self.n_features))
            idx = idx_old + idx_new

            # Get random selection of features
            self.dfs_features = \
                [value for i, value in enumerate(self.dfs_features) if i in idx]

        else:
            self.symbolic_transformer = \
                SymbolicTransformer(generations=self.generations,
                                    population_size=self.population,
                                    hall_of_fame=int(0.1 * self.population),
                                    n_components=int(0.01 * self.population),
                                    init_depth=(1, 2),
                                    function_set=self.operators,
                                    feature_names=X.columns,
                                    verbose=0 if self.verbose < 2 else 1,
                                    n_jobs=self.n_jobs,
                                    random_state=self.random_state)
            self.symbolic_transformer.fit(X, y)

        self._is_fitted = True
        return self

    @composed(crash, method_to_log, typechecked)
    def transform(self, X: X_TYPES, y: Optional[Y_TYPES] = None):
        """Create the new features.

        Parameters
        ----------
        X: dict, sequence, np.array or pd.DataFrame
            Data containing the features, with shape=(n_samples, n_features).

        y: int, str, sequence, np.array or pd.Series, optional (default=None)
            Does nothing. Implemented for continuity of the API.

        Returns
        -------
        X: pd.DataFrame
            Dataframe containing the newly generated features.

        """
        check_is_fitted(self, '_is_fitted')
        X, y = self._prepare_input(X, y)

        self.log("Creating new features...", 1)

        if self.strategy.lower() == 'dfs':
            # Make an entity set and add the entity
            entity_set = ft.EntitySet(id='atom')
            entity_set.entity_from_dataframe(entity_id='data',
                                             dataframe=X,
                                             make_index=True,
                                             index='index')

            X = ft.calculate_feature_matrix(features=self.dfs_features,
                                            entityset=entity_set,
                                            n_jobs=self.n_jobs)

            X.index.name = ''  # DFS gives index a name automatically
            self.log(" --> {} new features were added to the dataset."
                     .format(self.n_features), 2)

        else:
            new_features = self.symbolic_transformer.transform(X)

            # ix = indices of all new features that are not in the original set
            # descript = list of the operators applied to create the new features
            # fitness = list of fitness scores of the new features
            ix, descript, fitness = [], [], []
            for i, program in enumerate(self.symbolic_transformer):
                if str(program) not in X.columns:
                    ix.append(i)
                descript.append(str(program))
                fitness.append(program.fitness_)

            # Remove all features that are identical to those in the dataset
            new_features = new_features[:, ix]
            descript = [descript[i] for i in range(len(descript)) if i in ix]
            fitness = [fitness[i] for i in range(len(fitness)) if i in ix]

            # Indices of all non duplicate elements in list
            ix = [ix for ix, v in enumerate(descript) if v not in descript[:ix]]

            # Remove all duplicate elements
            new_features = new_features[:, ix]
            descript = [descript[i] for i in range(len(descript)) if i in ix]
            fitness = [fitness[i] for i in range(len(fitness)) if i in ix]

            self.log("-" * 49, 2)

            # Check if any new features remain in the loop
            if len(descript) == 0:
                self.log("WARNING! The genetic algorithm couldn't find any " +
                         "improving non-linear features!", 1)
                return X

            # Get indices of the best features
            if self.n_features and len(descript) > self.n_features:
                index = np.argpartition(fitness, -self.n_features)[-self.n_features:]
            else:
                index = range(len(descript))

            # Select best features only
            new_features = new_features[:, index]
            for i, idx in enumerate(index):
                self.genetic_features = self.genetic_features.append(
                    {'name': 'Feature ' + str(1 + i + len(X.columns)),
                     'description': descript[idx],
                     'fitness': fitness[idx]},
                    ignore_index=True)

            self.log(" --> {} new features were added to the dataset."
                     .format(len(self.genetic_features)), 2)

            cols = list(X.columns) + list(self.genetic_features['name'])
            X = pd.DataFrame(np.hstack((X, new_features)), columns=cols)

        return X


class FeatureSelector(BaseEstimator,
                      BaseTransformer,
                      BaseCleaner,
                      FeatureSelectorPlotter):
    """Apply feature selection techniques.

    Remove features according to the selected strategy. Ties between
    features with equal scores will be broken in an unspecified way.
    Also removes features with too low variance and finds pairs of
    collinear features based on the Pearson correlation coefficient. For
    each pair above the specified limit (in terms of absolute value), it
    removes one of the two.

    Parameters
    ----------
    strategy: string or None, optional (default=None)
        Feature selection strategy to use. Choose from:
            - None: Do not perform any feature selection algorithm.
            - 'univariate': Perform a univariate F-test.
            - 'PCA': Perform principal component analysis.
            - 'SFM': Select best features from model.
            - 'RFE': Recursive feature eliminator.
            - 'RFECV': RFE with cross-validated selection.

        Note that the RFE and RFECV strategies don't work when the solver is a
        CatBoost model due to incompatibility of the APIs.

    solver: string, callable or None, optional (default=None)
        Solver or model to use for the feature selection strategy. See the
        sklearn documentation for an extended description of the choices.
        Select None for the default option per strategy (not applicable
        for SFM, RFE and RFECV).
            - for 'univariate', choose from:
                + 'f_classif'
                + 'f_regression'
                + 'mutual_info_classif'
                + 'mutual_info_regression'
                + 'chi2'
                + Any function taking two arrays (X, y), and returning
                  arrays (scores, p-values). See the sklearn documentation.
            - for 'PCA', choose from:
                + 'auto' (default)
                + 'full'
                + 'arpack'
                + 'randomized'
            - for 'SFM': choose a base estimator from which the
                         transformer is built. The estimator must have
                         either a feature_importances_ or coef_ attribute
                         after fitting. No default option. You can use a
                         model from the ATOM package. No default option.
            - for 'RFE': choose a supervised learning estimator. The
                         estimator must have either a feature_importances_
                         or coef_ attribute after fitting. You can use a
                         model from the ATOM package. No default option.
            - for 'RFECV': choose a supervised learning estimator. The
                           estimator must have either feature_importances_
                           or coef_ attribute after fitting. You can use a
                           model from the ATOM package. No default option.

    n_features: int, float or None, optional (default=None)
        Number of features to select. Choose from:
            - if None: Select all features.
            - if < 1: Fraction of the total features to select.
            - if >= 1: Number of features to select.

        If strategy='SFM' and the threshold parameter is not specified, the threshold
        will be set to -np.inf in order to make this parameter the number of features
        to select.
        If strategy='RFECV', it's the minimum number of features to select.

    max_frac_repeated: float or None, optional (default=1.)
        Remove features with the same value in at least this fraction of
        the total rows. The default is to keep all features with non-zero
        variance, i.e. remove the features that have the same value in all
        samples. None to skip this step.

    max_correlation: float or None, optional (default=1.)
        Minimum value of the Pearson correlation coefficient to identify
        correlated features. A value of 1 removes one of 2 equal columns.
        A dataframe of the removed features and their correlation values
        can be accessed through the collinear attribute. None to skip this step.

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

    logger: bool, str, class or None, optional (default=None)
        - If None: Doesn't save a logging file.
        - If bool: True for logging file with default name, False for no logger.
        - If string: name of the logging file. 'auto' for default name.
        - If class: python Logger object.

    random_state: int or None, optional (default=None)
        Seed used by the random number generator. If None, the random
        number generator is the RandomState instance used by `np.random`.

    **kwargs
        Any extra keyword argument for the PCA, SFM, RFE or RFECV estimators.
        See the corresponding sklearn documentation for the available options.

    """

    def __init__(self,
                 strategy: Optional[str] = None,
                 solver: Optional[Union[str, callable]] = None,
                 n_features: Optional[Union[int, float]] = None,
                 max_frac_repeated: Optional[Union[int, float]] = 1.,
                 max_correlation: Optional[float] = 1.,
                 n_jobs: int = 1,
                 verbose: int = 0,
                 logger: Optional[Union[bool, str, callable]] = None,
                 random_state: Optional[int] = None,
                 **kwargs):
        super().__init__(n_jobs=n_jobs,
                         verbose=verbose,
                         logger=logger,
                         random_state=random_state)

        # Check parameters
        if isinstance(strategy, str):
            strats = ['univariate', 'pca', 'sfm', 'rfe', 'rfecv']

            if strategy.lower() not in strats:
                raise ValueError("Invalid value for the strategy parameter. " +
                                 "Choose from: univariate, PCA, SFM, RFE or " +
                                 "RFECV.")

            elif strategy.lower() == 'univariate':
                solvers_dct = dict(f_classif=f_classif,
                                   f_regression=f_regression,
                                   mutual_info_classif=mutual_info_classif,
                                   mutual_info_regression=mutual_info_regression,
                                   chi2=chi2)

                if not solver:
                    raise ValueError("Choose a solver for the strategy!")
                elif solver in solvers_dct:
                    solver = solvers_dct[solver]
                elif isinstance(solver, str):
                    raise ValueError(
                        f"Unknown solver. Choose from: {', '.join(solvers_dct)}.")

            elif strategy.lower() == 'pca':
                solver = 'auto' if solver is None else solver

            elif strategy.lower() in ['sfm', 'rfe', 'rfecv']:
                if solver is None:
                    raise ValueError("Select a solver for the strategy!")
                elif isinstance(solver, str):
                    # Assign goal depending on solver's ending
                    if solver[-6:] == '_class':
                        self.goal = 'classification'
                        solver = solver[:-6]
                    elif solver[-4:] == '_reg':
                        self.goal = 'regression'
                        solver = solver[:-4]

                    if solver.lower() not in map(str.lower, MODEL_LIST):
                        raise ValueError(
                            "Unknown value for the solver parameter, got " +
                            f"{solver}. Try one of {list(MODEL_LIST)}.")
                    else:  # Set to right model name and call model's method
                        model_class = MODEL_LIST[get_model_name(solver)]
                        solver = model_class(self).get_model()

        if n_features is not None and n_features <= 0:
            raise ValueError("Invalid value for the n_features parameter. " +
                             f"Value should be >0, got {n_features}.")
        if max_frac_repeated is not None and not 0 <= max_frac_repeated <= 1:
            raise ValueError(
                "Invalid value for the max_frac_repeated parameter. Value should " +
                f"be between 0 and 1, got {max_frac_repeated}.")
        if max_correlation is not None and not 0 <= max_correlation <= 1:
            raise ValueError(
                "Invalid value for the max_correlation parameter. Value should " +
                f"be between 0 and 1, got {max_correlation}.")

        # Define attributes
        self.strategy = strategy
        self.solver = solver
        self.n_features = n_features
        self.max_frac_repeated = max_frac_repeated
        self.max_correlation = max_correlation
        self.kwargs = kwargs

        self.collinear = None
        self.univariate = None
        self.scaler = None
        self.pca = None
        self.sfm = None
        self.rfe = None
        self.rfecv = None
        self._is_fitted = False

    def _remove_low_variance(self, X, max_, _vb=2):
        """Remove features with too low variance.

        Parameters
        ----------
        X: pd.DataFrame
            Data containing the features, with shape=(n_samples, n_features).

        max_: float
            Maximum fraction of repeated values.

        _vb: int, optional (default=2)
            Internal parameter to silence the fit method. If default, prints.

        Returns
        -------
        X: pd.DataFrame
            Dataframe with no low variance columns.

        """
        for n, col in enumerate(X):
            unique, count = np.unique(X[col], return_counts=True)
            for u, c in zip(unique, count):
                # If count is larger than fraction of total...
                if c >= max_ * len(X):
                    self.log(f" --> Feature {col} was removed due to " +
                             f"low variance. Value {u} repeated in " +
                             f"{round(c/len(X)*100., 1)}% of rows.", _vb)
                    X.drop(col, axis=1, inplace=True)
                    break
        return X

    def _remove_collinear(self, X, max_, _vb=2):
        """Remove collinear features.

        Finds pairs of collinear features based on the Pearson correlation
        coefficient. For each pair above the specified limit (in terms of
        absolute value), it removes one of the two. Using code adapted from:
        https://chrisalbon.com/machine_learning/feature_selection/
        drop_highly_correlated_features

        Parameters
        ----------
        X: pd.DataFrame
            Data containing the features, with shape=(n_samples, n_features).

        max_: float
            Maximum correlation allowed before removing one of the columns.

        _vb: int, optional (default=2)
            Internal parameter to silence the fit method. If default, prints.

        Returns
        -------
        X: pd.DataFrame
            Dataframe with no highly correlated features.

        """
        mtx = X.corr()  # Pearson correlation coefficient matrix

        # Extract the upper triangle of the correlation matrix
        upper = mtx.where(np.triu(np.ones(mtx.shape).astype(np.bool), k=1))

        # Select the features with correlations above the threshold
        to_drop = [i for i in upper.columns if any(abs(upper[i] > max_))]

        # Dataframe to hold correlated pairs
        self.collinear = pd.DataFrame(columns=['drop_feature',
                                               'correlated_feature',
                                               'correlation_value'])

        # Iterate to record pairs of correlated features
        for col in to_drop:
            # Find the correlated features
            corr_features = list(upper.index[abs(upper[col]) > max_])

            # Find the correlated values
            corr_values = list(round(upper[col][abs(upper[col]) > max_], 5))
            drop_features = set([col for _ in corr_features])

            # Add to class attribute
            self.collinear = self.collinear.append(
                {'drop_feature': ', '.join(drop_features),
                 'correlated_feature': ', '.join(corr_features),
                 'correlation_value': ', '.join(map(str, corr_values))},
                ignore_index=True)

            self.log(f" --> Feature {col} was removed due to " +
                     "collinearity with another feature.", _vb)

        return X.drop(to_drop, axis=1)

    @composed(crash, method_to_log, typechecked)
    def fit(self, X: X_TYPES, y: Optional[Y_TYPES] = None):
        """Fit the data according to the selected strategy.

        Note that the univariate, sfm (when model is not fitted), rfe and rfecv
        strategies need a target column. Leaving it None will raise an exception.

        Parameters
        ----------
        X: dict, sequence, np.array or pd.DataFrame
            Data containing the features, with shape=(n_samples, n_features).

        y: int, str, sequence, np.array or pd.Series
            - If None: y is not used in the estimator.
            - If int: Position of the target column in X.
            - If str: Name of the target column in X.
            - Else: Data target column with shape=(n_samples,).

        Returns
        -------
        self: FeatureSelector

        """
        def check_y():
            """For some strategies, y needs to be provided."""
            if y is None:
                raise ValueError("Invalid value for the y parameter. Value cannot " +
                                 f"be None for strategy='{self.strategy}'.")

        X, y = self._prepare_input(X, y)

        self.log("Fitting FeatureSelector...", 1)

        # Remove features with too low variance
        if self.max_frac_repeated is not None:
            X = self._remove_low_variance(X, self.max_frac_repeated, _vb=42)

        # Remove features with too high correlation
        if self.max_correlation is not None:
            X = self._remove_collinear(X, self.max_correlation, _vb=42)

        # Set n_features as all or fraction of total
        if self.n_features is None:
            self.n_features = X.shape[1]
        elif self.n_features < 1:
            self.n_features = int(self.n_features * X.shape[1])

        # Perform selection based on strategy
        if self.strategy is None:
            self._is_fitted = True
            return self  # Exit feature_engineering

        elif self.strategy.lower() == 'univariate':
            check_y()
            self.univariate = SelectKBest(self.solver, k=self.n_features)
            self.univariate.fit(X, y)

        elif self.strategy.lower() == 'pca':
            # Always fit in case the data to transform is not scaled
            self.scaler = Scaler().fit(X)
            if not check_scaling(X):
                X = self.scaler.transform(X)

            # Define PCA
            self.pca = PCA(n_components=None,
                           svd_solver=self.solver,
                           **self.kwargs)
            self.pca.fit(X)
            self.pca.n_components_ = self.n_features  # Number of components

        elif self.strategy.lower() == 'sfm':
            # If any of these attr exists, model is already fitted
            condition1 = hasattr(self.solver, 'coef_')
            condition2 = hasattr(self.solver, 'feature_importances_')
            self.kwargs['prefit'] = True if condition1 or condition2 else False

            # If threshold is not specified, select only based on n_features
            if not self.kwargs.get('threshold'):
                self.kwargs['threshold'] = -np.inf

            self.sfm = SelectFromModel(estimator=self.solver,
                                       max_features=self.n_features,
                                       **self.kwargs)
            if not self.kwargs['prefit']:
                check_y()
                self.sfm.fit(X, y)

        elif self.strategy.lower() == 'rfe':
            check_y()
            self.rfe = RFE(estimator=self.solver,
                           n_features_to_select=self.n_features,
                           **self.kwargs)
            self.rfe.fit(X, y)

        elif self.strategy.lower() == 'rfecv':
            check_y()
            if self.n_features == X.shape[1]:
                self.n_features = 1

            if self.kwargs.get('scoring') in METRIC_ACRONYMS:
                self.kwargs['scoring'] = METRIC_ACRONYMS[self.kwargs['scoring']]

            self.rfecv = RFECV(estimator=self.solver,
                               min_features_to_select=self.n_features,
                               n_jobs=self.n_jobs,
                               **self.kwargs)
            self.rfecv.fit(X, y)

        self._is_fitted = True
        return self

    @composed(crash, method_to_log, typechecked)
    def transform(self, X: X_TYPES, y: Optional[Y_TYPES] = None):
        """Transform the data according to the selected strategy.

        Parameters
        ----------
        X: dict, sequence, np.array or pd.DataFrame
            Data containing the features, with shape=(n_samples, n_features).

        y: int, str, sequence, np.array or pd.Series, optional (default=None)
            Does nothing. Only for continuity of API.

        Returns
        -------
        X: pd.DataFrame
            Copy of the feature dataset.

        """
        check_is_fitted(self, '_is_fitted')
        X, y = self._prepare_input(X, y)

        self.log("Performing feature selection ...", 1)

        # Remove features with too low variance
        if self.max_frac_repeated is not None:
            X = self._remove_low_variance(X, self.max_frac_repeated)

        # Remove features with too high correlation
        if self.max_correlation is not None:
            X = self._remove_collinear(X, self.max_correlation)

        # Perform selection based on strategy
        if self.strategy is None:
            return X

        elif self.strategy.lower() == 'univariate':
            for n, col in enumerate(X):
                if not self.univariate.get_support()[n]:
                    self.log(f" --> Feature {col} was removed after the uni" +
                             "variate test (score: {:.2f}  p-value: {:.2f})."
                             .format(self.univariate.scores_[n],
                                     self.univariate.pvalues_[n]), 2)
                    X.drop(col, axis=1, inplace=True)

        elif self.strategy.lower() == 'pca':
            self.log(f" --> Applying Principal Component Analysis...", 2)

            if not check_scaling(X):
                self.log("   >>> Scaling features...", 2)
                X = self.scaler.transform(X)

            # Define PCA, keep in mind that it has all components still
            n = self.pca.n_components_
            var = np.array(self.pca.explained_variance_ratio_[:n])
            X = to_df(self.pca.transform(X)[:, :n], index=X.index, pca=True)
            self.log("   >>> Total explained variance: {}"
                     .format(round(var.sum(), 3)), 2)

        elif self.strategy.lower() == 'sfm':
            for n, column in enumerate(X):
                if not self.sfm.get_support()[n]:
                    self.log(f" --> Feature {column} was removed by the " +
                             f"{self.solver.__class__.__name__}.", 2)
                    X.drop(column, axis=1, inplace=True)

        elif self.strategy.lower() == 'rfe':
            for n, column in enumerate(X):
                if not self.rfe.support_[n]:
                    self.log(f" --> Feature {column} was removed by the RFE.", 2)
                    X.drop(column, axis=1, inplace=True)

        elif self.strategy.lower() == 'rfecv':
            for n, column in enumerate(X):
                if not self.rfecv.support_[n]:
                    self.log(f" --> Feature {column} was removed by the RFECV.", 2)
                    X.drop(column, axis=1, inplace=True)

        return X
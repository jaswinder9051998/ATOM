# -*- coding: utf-8 -*-

"""Automated Tool for Optimized Modelling (ATOM).

Author: tvdboom
Description: Module containing the parent class for all model subclasses.

"""

# Standard packages
import pickle
import numpy as np
import pandas as pd
from time import time
from tqdm import tqdm
from joblib import Parallel, delayed
from typeguard import typechecked
from typing import Optional, Union
from inspect import signature

# Sklearn
from sklearn.base import clone
from sklearn.utils import resample
from sklearn.metrics import SCORERS, confusion_matrix
from sklearn.model_selection import StratifiedShuffleSplit, ShuffleSplit
from sklearn.model_selection import KFold, StratifiedKFold
from sklearn.calibration import CalibratedClassifierCV

# Others
from skopt.utils import use_named_args
from skopt.callbacks import DeadlineStopper, DeltaXStopper, DeltaYStopper
from skopt.optimizer import base_minimize, gp_minimize, forest_minimize, gbrt_minimize

# Own modules
from .plots import SuccessiveHalvingPlotter, TrainSizingPlotter
from .utils import (
    ARRAY_TYPES, X_TYPES, Y_TYPES, CUSTOM_METRICS, METRIC_ACRONYMS, flt, lst,
    merge, arr, check_scaling, time_to_string, catch_return, transform,
    composed, get_best_score, crash, method_to_log, PlotCallback,
)


# Classes =================================================================== >>

class BaseModel(SuccessiveHalvingPlotter, TrainSizingPlotter):
    """Parent class of all model subclasses.

    Parameters
     ----------
     data: dict
         Dictionary of the data used for this model (train and test).

     T: class
         Class from which the model is called. To avoid having to pass
         attributes through params.

    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

        # BO attributes
        self._iter = 0
        self._init_bo = None
        self._pbar = None
        self._cv = 5  # Default value
        self._early_stopping = None
        self._stopped = None
        self.bo = pd.DataFrame(
            columns=["params", "model", "score", "time_iteration", "time"]
        )
        self.bo.index.name = "call"

        # Parameter attributes
        self._est_params = {}
        self._est_params_fit = {}

        # BaseModel attributes
        self.best_params = None
        self.estimator = None
        self.time_fit = None
        self.metric_bo = None
        self.time_bo = None
        self.metric_train = None
        self.metric_test = None
        self.metric_bagging = []
        self.mean_bagging = None
        self.std_bagging = None
        self.time_bagging = None
        self.reset_prediction_attributes()

        # Results
        self._results = pd.DataFrame(
            columns=[
                "metric_bo",
                "time_bo",
                "metric_train",
                "metric_test",
                "time_fit",
                "mean_bagging",
                "std_bagging",
                "time_bagging",
                "time",
            ]
        )
        self._results.index.name = "model"

    def __repr__(self):
        repr_ = f"{self.fullname}\n --> Estimator: {self.estimator.__class__.__name__}"
        for i, metric in enumerate(self.T.metric_):
            repr_ += f"\n --> {metric.name}: {get_best_score(self, i)}"

        return repr_

    def _get_default(self, x, params):
        """Return the standard parameter from params or the training instance.

        Parameters
        ----------
        x: list
            Standard parameter name(s). Can be n_jobs and/or random_state.

        params: dict
            Parameters for the estimator provided by the BO and est_params.

        """
        args = []
        for i in x:
            args.append(params.pop(i) if params.get(i) else getattr(self.T, i))

        if len(args) == 1:
            return args[0]
        else:
            return args[0], args[1]

    def get_params(self, x):
        """Return a dictionary of the model´s hyperparameters.

        Parameters
        ----------
        x: list
            Hyperparameters returned by the BO, in order of self.params.

        """
        params = {}
        for i, (key, value) in enumerate(self.params.items()):
            if value[1]:  # If it has decimals...
                params[key] = round(x[i], value[1])
            else:
                params[key] = x[i]

        return params

    def get_init_values(self):
        """Return the default values of the model's hyperparameters."""
        return [value[0] for value in self.params.values()]

    @composed(crash, method_to_log, typechecked)
    def bayesian_optimization(
        self,
        n_calls: int = 15,
        n_initial_points: int = 5,
        bo_params: dict = {},
    ):
        """Run the bayesian optimization algorithm.

        Search for the best combination of hyperparameters. The function to
        optimize is evaluated either with a K-fold cross-validation on the
        training set or using a different validation set every iteration.

        Parameters
        ----------
        n_calls: int, list or tuple, optional (default=15)
            Maximum number of iterations of the BO (including `n_initial_points`).
            If 0, skip the BO and fit the model on its default Parameters.
            If iterable, the n-th value will apply to the n-th model in the
            pipeline.

        n_initial_points: int, list or tuple, optional (default=5)
            Initial number of random tests of the BO before fitting the
            surrogate function. If equal to `n_calls`, the optimizer will
            technically be performing a random search. If iterable, the n-th
            value will apply to the n-th model in the pipeline.

        bo_params: dict, optional (default={})
            Additional parameters to for the BO. These can include:
                - base_estimator: str, optional (default="GP")
                    Surrogate model to use. Choose from:
                        - "GP" for Gaussian Process
                        - "RF" for Random Forest
                        - "ET" for Extra-Trees
                        - "GBRT" for Gradient Boosted Regression Trees
                - max_time: int, optional (default=np.inf)
                    Stop the optimization after `max_time` seconds.
                - delta_x: int or float, optional (default=0)
                    Stop the optimization when `|x1 - x2| < delta_x`.
                - delta_y: int or float, optional (default=0)
                    Stop the optimization if the 5 minima are within `delta_y`.
                - early stopping: int, float or None, optional (default=None)
                    Training will stop if the model didn't improve in last
                    `early_stopping` rounds. If <1, fraction of rounds from the
                    total. If None, no early stopping is performed. Only available
                    for models that allow in-training evaluation.
                - cv: int, optional (default=5)
                    Number of folds for the cross-validation. If 1, the
                    training set will be randomly split in a subtrain and
                    validation set.
                - callbacks: callable or list of callables, optional (default=None)
                    Callbacks for the BO.
                - dimensions: dict, array or None, optional (default=None)
                    Custom hyperparameter space for the bayesian optimization.
                    Can be an array to share the same dimensions across models
                    or a dictionary with the model names as key. If None, ATOM's
                    predefined dimensions are used.
                - plot_bo: bool, optional (default=False)
                    Whether to plot the BO's progress as it runs. Creates a canvas
                    with two plots: the first plot shows the score of every trial
                    and the second shows the distance between the last consecutive
                    steps. Don't forget to call `%matplotlib` at the start of the
                    cell if you are using an interactive notebook!
                - Any other parameter for skopt's optimizer.

        """

        def optimize(**params):
            """Optimization function for the bayesian optimization algorithm.

            Parameters
            ----------
            params: dict
               Model's hyperparameters to be used for this iteration of the BO.

            Returns
            -------
            score: float
                Score achieved by the model.

            """

            def fit_model(train_idx, val_idx):
                """Fit the model. Function for parallelization.

                Divide the training set in a (sub)train and validation set for this
                fit. Fit the model on custom_fit if exists, else normally. Return
                the score on the validation set.

                Parameters
                ----------
                train_idx: list
                    Indices for the subtrain set.

                val_idx: list
                    Indices for the validation set.

                Returns
                -------
                score: float
                    Score of the fitted model on the validation set.

                """
                X_subtrain = self.X_train.loc[train_idx]
                y_subtrain = self.y_train.loc[train_idx]
                X_val = self.X_train.loc[val_idx]
                y_val = self.y_train.loc[val_idx]

                # Match the sample_weights with the length of the subtrain set
                # Make copy of est_params to not alter the mutable variable
                est_copy = self._est_params_fit.copy()
                if "sample_weight" in est_copy:
                    est_copy["sample_weight"] = [
                        self._est_params_fit["sample_weight"][i] for i in train_idx
                    ]

                if hasattr(self, "custom_fit"):
                    self.custom_fit(
                        estimator=est,
                        train=(X_subtrain, y_subtrain),
                        validation=(X_val, y_val),
                        params=est_copy
                    )

                    # Alert if early stopping was applied (only for cv=1)
                    if self._cv == 1 and self._stopped:
                        self.T.log(
                            f"Early stop at iteration {self._stopped[0]} "
                            f"of {self._stopped[1]}.", 2
                        )
                else:
                    est.fit(arr(X_subtrain), y_subtrain, **est_copy)

                # Calculate metrics on the validation set
                return [metric(est, arr(X_val), y_val) for metric in self.T.metric_]

            t_iter = time()  # Get current time for start of the iteration

            # Print iteration and time
            self._iter += 1
            if self._iter > n_initial_points:
                call = f"Iteration {self._iter}"
            else:
                call = f"Initial point {self._iter}"

            if self._pbar:
                self._pbar.set_description(call)
            len_ = "-" * (48 - len(call))
            self.T.log(f"{call} {len_}", 2)
            self.T.log(f"Parameters --> {params}", 2)

            est = self.get_estimator({**self._est_params, **params})

            # Same splits per model, but different for every iteration of the BO
            rs = self.T.random_state + self._iter if self.T.random_state else None

            if self._cv == 1:
                # Select test_size from ATOM or use default of 0.2
                t_size = self.T._test_size if hasattr(self.T, "_test_size") else 0.2
                kwargs = dict(test_size=t_size, random_state=rs)
                if self.T.goal.startswith("class"):
                    # Folds are made preserving the % of samples for each class
                    split = StratifiedShuffleSplit(1, **kwargs)
                else:
                    split = ShuffleSplit(1, **kwargs)

                scores = fit_model(*next(split.split(self.X_train, self.y_train)))

            else:  # Use cross validation to get the score
                kwargs = dict(n_splits=self._cv, shuffle=True, random_state=rs)
                if self.T.goal.startswith("class"):
                    # Folds are made preserving the % of samples for each class
                    k_fold = StratifiedKFold(**kwargs)
                else:
                    k_fold = KFold(**kwargs)

                # Parallel loop over fit_model
                jobs = Parallel(self.T.n_jobs)(
                    delayed(fit_model)(i, j)
                    for i, j in k_fold.split(self.X_train, self.y_train)
                )
                scores = list(np.mean(jobs, axis=0))

            # Append row to the bo attribute
            t = time_to_string(t_iter)
            t_tot = time_to_string(self._init_bo)
            self.bo.loc[call] = {
                "params": params,
                "estimator": est,
                "score": flt(scores),
                "time_iteration": t,
                "time": t_tot,
            }

            # Update the progress bar
            if self._pbar:
                self._pbar.update(1)

            # Print output of the BO
            out = [
                f"{m.name}: {scores[i]:.4f}  Best {m.name}: "
                f"{max([lst(s)[i] for s in self.bo.score]):.4f}"
                for i, m in enumerate(self.T.metric_)
            ]
            self.T.log(f"Evaluation --> {'   '.join(out)}", 2)
            self.T.log(f"Time iteration: {t}   Total time: {t_tot}", 2)

            return -scores[0]  # Negative since skopt tries to minimize

        # Running optimization ============================================== >>

        # Check parameters
        if n_initial_points < 1:
            raise ValueError(
                "Invalid value for the n_initial_points parameter. "
                f"Value should be >0, got {n_initial_points}."
            )
        if n_calls < n_initial_points:
            raise ValueError(
                "Invalid value for the n_calls parameter. Value "
                f"should be >n_initial_points, got {n_calls}."
            )

        self.T.log(f"\n\nRunning BO for {self.fullname}...", 1)

        self._init_bo = time()
        if self.T.verbose == 1:
            self._pbar = tqdm(total=n_calls, desc="Random start 1")

        # Prepare callbacks
        callbacks = []
        if bo_params.get("callbacks"):
            if not isinstance(bo_params["callbacks"], (list, tuple)):
                callbacks = [bo_params["callbacks"]]
            else:
                callbacks = bo_params["callbacks"]
            bo_params.pop("callbacks")

        if bo_params.get("max_time"):
            if bo_params["max_time"] <= 0:
                raise ValueError(
                    "Invalid value for the max_time parameter. "
                    f"Value should be >0, got {bo_params['max_time']}."
                )
            callbacks.append(DeadlineStopper(bo_params["max_time"]))
            bo_params.pop("max_time")

        if bo_params.get("delta_x"):
            if bo_params["delta_x"] < 0:
                raise ValueError(
                    "Invalid value for the delta_x parameter. "
                    f"Value should be >=0, got {bo_params['delta_x']}."
                )
            callbacks.append(DeltaXStopper(bo_params["delta_x"]))
            bo_params.pop("delta_x")

        if bo_params.get("delta_y"):
            if bo_params["delta_y"] < 0:
                raise ValueError(
                    "Invalid value for the delta_y parameter. "
                    f"Value should be >=0, got {bo_params['delta_y']}."
                )
            callbacks.append(DeltaYStopper(bo_params["delta_y"], n_best=5))
            bo_params.pop("delta_y")

        if "plot_bo" in bo_params:
            if bo_params["plot_bo"]:
                callbacks.append(PlotCallback(self))
            bo_params.pop("plot_bo")

        # Prepare additional arguments
        if bo_params.get("cv"):
            if bo_params["cv"] <= 0:
                raise ValueError(
                    "Invalid value for the max_time parameter. "
                    f"Value should be >=0, got {bo_params['cv']}."
                )
            self._cv = bo_params["cv"]
            bo_params.pop("cv")

        if bo_params.get("early_stopping"):
            if bo_params["early_stopping"] <= 0:
                raise ValueError(
                    "Invalid value for the early_stopping parameter. "
                    f"Value should be >=0, got {bo_params['early_stopping']}."
                )
            self._early_stopping = bo_params["early_stopping"]
            bo_params.pop("early_stopping")

        # Drop dimensions from BO if already in est_params
        for param in self._est_params:
            if param not in signature(self.get_estimator().__init__).parameters:
                raise ValueError(
                    f"Invalid value for the est_params parameter. Got {param} "
                    f"for estimator {self.get_estimator().__class__.__name__}."
                )
            elif param in self.params:
                self.params.pop(param)

        # Specify model dimensions
        def pre_defined_hyperparameters(x):
            return optimize(**self.get_params(x))

        # Get custom dimensions (if provided)
        dimensions = None
        if bo_params.get("dimensions"):
            if bo_params["dimensions"].get(self.name):
                dimensions = bo_params.get("dimensions")[self.name]

                @use_named_args(dimensions)
                def custom_hyperparameters(**x):
                    return optimize(**x)

                func = custom_hyperparameters  # Use custom hyperparameters
            bo_params.pop("dimensions")

        # If there were no custom dimensions, use the default
        if not dimensions:
            dimensions = self.get_dimensions()
            func = pre_defined_hyperparameters  # Default optimization func

        # If only 1 initial point, use the model's default parameters
        if n_initial_points == 1 and hasattr(self, "get_init_values"):
            bo_params["x0"] = self.get_init_values()

        # Choose base estimator (GP is chosen as default)
        base = bo_params.pop("base_estimator", "GP")

        # Prepare keyword arguments for the optimizer
        kwargs = dict(
            func=func,
            dimensions=dimensions,
            n_calls=n_calls,
            n_initial_points=n_initial_points,
            callback=callbacks,
            n_jobs=self.T.n_jobs,
            random_state=self.T.random_state,
        )
        kwargs.update(**bo_params)

        if isinstance(base, str):
            if base.lower() == "gp":
                optimizer = gp_minimize(**kwargs)
            elif base.lower() == "et":
                optimizer = forest_minimize(base_estimator="ET", **kwargs)
            elif base.lower() == "rf":
                optimizer = forest_minimize(base_estimator="RF", **kwargs)
            elif base.lower() == "gbrt":
                optimizer = gbrt_minimize(**kwargs)
            else:
                raise ValueError(
                    f"Invalid value for the base_estimator parameter, got {base}."
                    " Value should be one of: 'GP', 'ET', 'RF', 'GBRT'."
                )
        else:
            optimizer = base_minimize(base_estimator=base, **kwargs)

        if self._pbar:
            self._pbar.close()

        # Optimal parameters found by the BO
        # Return from skopt wrapper to get dict of custom hyperparameter space
        if func is pre_defined_hyperparameters:
            self.best_params = self.get_params(optimizer.x)
        else:

            @use_named_args(dimensions)
            def get_custom_params(**x):
                return x

            self.best_params = get_custom_params(optimizer.x)

        # Optimal score found by the BO
        self.metric_bo = self.bo.score.max(axis=0)

        # Save best model (not yet fitted)
        self.estimator = self.get_estimator({**self._est_params, **self.best_params})

        # Get the BO duration
        self.time_bo = time_to_string(self._init_bo)

        # Print results
        self.T.log(f"\nResults for {self.fullname}:{' ':9s}", 1)
        self.T.log("Bayesian Optimization ---------------------------", 1)
        self.T.log(f"Best parameters --> {self.best_params}", 1)
        out = [
            f"{m.name}: {lst(self.metric_bo)[i]:.4f}"
            for i, m in enumerate(self.T.metric_)
        ]
        self.T.log(f"Best evaluation --> {'   '.join(out)}", 1)
        self.T.log(f"Time elapsed: {self.time_bo}", 1)

    @composed(crash, method_to_log)
    def fit(self):
        """Fit to the complete training set and get the score on the test set."""
        t_init = time()

        # In case the bayesian_optimization method wasn't called
        if self.estimator is None:
            self.estimator = self.get_estimator(self._est_params)

        # Fit the selected model on the complete training set
        if hasattr(self, "custom_fit"):
            self.custom_fit(
                estimator=self.estimator,
                train=(self.X_train, self.y_train),
                validation=(self.X_test, self.y_test),
                params=self._est_params_fit
            )
        else:
            self.estimator.fit(arr(self.X_train), self.y_train, **self._est_params_fit)

        # Save metric scores on complete training and test set
        self.metric_train = flt([
            metric(self.estimator, arr(self.X_train), self.y_train)
            for metric in self.T.metric_
        ])
        self.metric_test = flt([
            metric(self.estimator, arr(self.X_test), self.y_test)
            for metric in self.T.metric_
        ])

        # Print stats ======================================================= >>

        if self.bo.empty:
            self.T.log("\n", 1)  # Print 2 extra lines
            self.T.log(f"Results for {self.fullname}:{' ':9s}", 1)
        self.T.log("Fit ---------------------------------------------", 1)
        if self._stopped:
            out = f"Early stop at iteration {self._stopped[0]} of {self._stopped[1]}."
            self.T.log(out, 1)
        out_train = [
            f"{m.name}: {lst(self.metric_train)[i]:.4f}"
            for i, m in enumerate(self.T.metric_)
        ]
        self.T.log(f"Train evaluation --> {'   '.join(out_train)}", 1)
        out_test = [
            f"{m.name}: {lst(self.metric_test)[i]:.4f}"
            for i, m in enumerate(self.T.metric_)
        ]
        self.T.log(f"Test evaluation --> {'   '.join(out_test)}", 1)

        # Get duration and print to log
        self.time_fit = time_to_string(t_init)
        self.T.log(f"Time elapsed: {self.time_fit}", 1)

    @composed(crash, method_to_log, typechecked)
    def bagging(self, bagging: Optional[int] = 5):
        """Apply a bagging algorithm on the model.

        Take bootstrap samples from the training set and test them on the test
        set to get a distribution of the model's results.

        Parameters
        ----------
        bagging: int or None, optional (default=5)
            Number of data sets (bootstrapped from the training set) to use in
            the bagging algorithm. If None or 0, no bagging is performed.

        """
        t_init = time()

        if bagging < 0:
            raise ValueError(
                "Invalid value for the bagging parameter."
                f"Value should be >=0, got {bagging}."
            )

        self.metric_bagging = []
        for _ in range(bagging):
            # Create samples with replacement
            sample_x, sample_y = resample(self.X_train, self.y_train)

            # Make a clone to not overwrite when fitting
            estimator = clone(self.estimator)

            # Fit on bootstrapped set and predict on the independent test set
            if hasattr(self, "custom_fit"):
                self.custom_fit(
                    estimator=estimator,
                    train=(sample_x, sample_y),
                    validation=None,
                    params=self._est_params_fit
                )
            else:
                estimator.fit(arr(sample_x), sample_y, **self._est_params_fit)

            scores = flt([
                metric(estimator, arr(self.X_test), self.y_test)
                for metric in self.T.metric_
            ])

            # Append metric result to list
            self.metric_bagging.append(scores)

        # Numpy array for mean and std
        # Separate for multi-metric to transform numpy types in python types
        if len(self.T.metric_) == 1:
            self.mean_bagging = np.mean(self.metric_bagging, axis=0).item()
            self.std_bagging = np.std(self.metric_bagging, axis=0).item()
        else:
            self.mean_bagging = np.mean(self.metric_bagging, axis=0).tolist()
            self.std_bagging = np.std(self.metric_bagging, axis=0).tolist()

        self.T.log("Bagging -----------------------------------------", 1)
        out = [
            f"{m.name}: {lst(self.mean_bagging)[i]:.4f}"
            " \u00B1 "
            f"{lst(self.std_bagging)[i]:.4f}"
            for i, m in enumerate(self.T.metric_)
        ]
        self.T.log(f"Evaluation --> {'   '.join(out)}", 1)

        # Get duration and print to log
        self.time_bagging = time_to_string(t_init)
        self.T.log(f"Time elapsed: {self.time_bagging}", 1)

    # Prediction methods ==================================================== >>

    def _prediction(self, X, y=None, sample_weight=None, method="predict", **kwargs):
        """Apply prediction methods on new data.

        First transform the new data and apply the attribute on the best model.
        The model has to have the provided attribute.

        Parameters
        ----------
        X: dict, list, tuple, np.array or pd.DataFrame
            Data containing the features, with shape=(n_samples, n_features).

        y: int, str, list, tuple, np.array, pd.Series, optional (default=None)
            - If None, the target column is not used in the attribute
            - If int: index of the column of X which is selected as target
            - If str: name of the target column in X
            - Else: data target column with shape=(n_samples,)

        sample_weight: array-like or None, optional (default=None)
            Sample weights for the score method.

        method: str, optional (default="predict")
            Method of the model to be applied.

        **kwargs
            Keyword arguments for the transform method.

        Returns
        -------
        np.array
            Return of the attribute.

        """
        if not hasattr(self.estimator, method):
            raise AttributeError(
                f"The {self.estimator.__class__.__name__} "
                f"estimator doesn't have a {method} method!"
            )

        # When there is a pipeline, apply all data transformations first
        if hasattr(self, "_est_pipeline"):
            if kwargs.get("verbose") is None:
                kwargs["verbose"] = self.T.verbose
            X, y = catch_return(transform(self._est_pipeline, X, y, **kwargs))

        # Scale the data if needed
        if self.needs_scaling and not check_scaling(X):
            X = self.T.scaler.transform(X)

        if y is None:
            return getattr(self.estimator, method)(X)
        else:
            return getattr(self.estimator, method)(X, y, sample_weight)

    @composed(crash, method_to_log, typechecked)
    def predict(self, X: X_TYPES, **kwargs):
        """Get predictions on new data."""
        return self._prediction(X, method="predict", **kwargs)

    @composed(crash, method_to_log, typechecked)
    def predict_proba(self, X: X_TYPES, **kwargs):
        """Get probability predictions on new data."""
        return self._prediction(X, method="predict_proba", **kwargs)

    @composed(crash, method_to_log, typechecked)
    def predict_log_proba(self, X: X_TYPES, **kwargs):
        """Get log probability predictions on new data."""
        return self._prediction(X, method="predict_log_proba", **kwargs)

    @composed(crash, method_to_log, typechecked)
    def decision_function(self, X: X_TYPES, **kwargs):
        """Get the decision function on new data."""
        return self._prediction(X, method="decision_function", **kwargs)

    @composed(crash, method_to_log, typechecked)
    def score(
        self,
        X: X_TYPES,
        y: Y_TYPES,
        sample_weight: Optional[Union[ARRAY_TYPES]] = None,
        **kwargs,
    ):
        """Get the score function on new data."""
        return self._prediction(X, y, sample_weight, method="score", **kwargs)

    # Prediction properties ================================================= >>

    def reset_prediction_attributes(self):
        """Clear all the prediction attributes."""
        self._predict_train, self._predict_test = None, None
        self._predict_proba_train, self._predict_proba_test = None, None
        self._log_proba_train, self._log_proba_test = None, None
        self._dec_func_train, self._dec_func_test = None, None
        self._score_train, self._score_test = None, None

    @property
    def predict_train(self):
        if self._predict_train is None:
            self._predict_train = self.estimator.predict(arr(self.X_train))
        return self._predict_train

    @property
    def predict_test(self):
        if self._predict_test is None:
            self._predict_test = self.estimator.predict(arr(self.X_test))
        return self._predict_test

    @property
    def predict_proba_train(self):
        if self._predict_proba_train is None:
            self._predict_proba_train = self.estimator.predict_proba(arr(self.X_train))
        return self._predict_proba_train

    @property
    def predict_proba_test(self):
        if self._predict_proba_test is None:
            self._predict_proba_test = self.estimator.predict_proba(arr(self.X_test))
        return self._predict_proba_test

    @property
    def predict_log_proba_train(self):
        if self._log_proba_train is None:
            self._log_proba_train = self.estimator.predict_log_proba(arr(self.X_train))
        return self._log_proba_train

    @property
    def predict_log_proba_test(self):
        if self._log_proba_test is None:
            self._log_proba_test = self.estimator.predict_log_proba(arr(self.X_test))
        return self._log_proba_test

    @property
    def decision_function_train(self):
        if self._dec_func_train is None:
            self._dec_func_train = self.estimator.decision_function(arr(self.X_train))
        return self._dec_func_train

    @property
    def decision_function_test(self):
        if self._dec_func_test is None:
            self._dec_func_test = self.estimator.decision_function(arr(self.X_test))
        return self._dec_func_test

    @property
    def score_train(self):
        if self._score_train is None:
            self._score_train = self.estimator.score(arr(self.X_train), self.y_train)
        return self._score_train

    @property
    def score_test(self):
        if self._score_test is None:
            self._score_test = self.estimator.score(arr(self.X_test), self.y_test)
        return self._score_test

    # Properties ==================================================== >>

    @property
    def results(self):
        """Return results without empty columns."""
        return self._results.dropna(axis=1, how="all")

    @property
    def dataset(self):
        if self.needs_scaling and not check_scaling(self.T.X):
            return merge(self.T.scaler.transform(self.T.X), self.y)
        else:
            return self.T.dataset

    @property
    def train(self):
        if self.needs_scaling and not check_scaling(self.T.X):
            return merge(self.T.scaler.transform(self.T.X_train), self.y_train)
        else:
            return self.T.train

    @property
    def test(self):
        if self.needs_scaling and not check_scaling(self.T.X):
            return merge(self.T.scaler.transform(self.T.X_test), self.y_test)
        else:
            return self.T.test

    @property
    def X(self):
        if self.needs_scaling and not check_scaling(self.T.X):
            return self.T.scaler.transform(self.T.X)
        else:
            return self.T.X

    @property
    def y(self):
        return self.T.y

    @property
    def X_train(self):
        if self.needs_scaling and not check_scaling(self.T.X):
            return self.T.scaler.transform(self.T.X_train)
        else:
            return self.T.X_train

    @property
    def X_test(self):
        if self.needs_scaling and not check_scaling(self.T.X):
            return self.T.scaler.transform(self.T.X_test)
        else:
            return self.T.X_test

    @property
    def y_train(self):
        return self.T.y_train

    @property
    def y_test(self):
        return self.T.y_test

    @property
    def shape(self):
        return self.T.shape

    @property
    def columns(self):
        return self.T.columns

    @property
    def target(self):
        return self.T.target

    @property
    def classes(self):
        return self.T.classes

    @property
    def n_classes(self):
        return self.T.n_classes

    # Utility methods ======================================================= >>

    def _final_output(self):
        """Returns the model's final output as a string."""
        # If bagging was used, we use a different format
        if self.mean_bagging is None:
            out = "   ".join([
                f"{m.name}: {lst(self.metric_test)[i]:.3f}"
                for i, m, in enumerate(self.T.metric_)
            ])
        else:
            out = "   ".join([
                f"{m.name}: {lst(self.mean_bagging)[i]:.3f}"
                " \u00B1 "
                f"{lst(self.std_bagging)[i]:.3f}"
                for i, m in enumerate(self.T.metric_)
            ])

        # Annotate if model overfitted when train 20% > test
        metric_train = lst(self.metric_train)
        metric_test = lst(self.metric_test)
        if metric_train[0] - 0.2 * metric_train[0] > metric_test[0]:
            out += " ~"

        return out

    @composed(crash)
    def calibrate(self, **kwargs):
        """Calibrate the model.

        Applies probability calibration on the winning model. The calibration is
        done with the CalibratedClassifierCV class from sklearn. The estimator will
        be trained via cross-validation on a subset of the training data, using the
        rest to fit the calibrator. The new classifier will replace the `estimator`
        attribute. All prediction attributes will reset.

        Parameters
        ----------
        **kwargs
            Additional keyword arguments for the CalibratedClassifierCV instance.
            Using cv="prefit" will use the trained model and fit the calibrator on
            the test set. Note that doing this will result in data leakage in the
            test set. Use this only if you have another, independent set for testing.

        """
        if self.T.goal.startswith("reg"):
            raise PermissionError(
                "The calibrate method is only available for classification tasks!"
            )

        calibrator = CalibratedClassifierCV(self.estimator, **kwargs)
        if kwargs.get("cv") != "prefit":
            self.estimator = calibrator.fit(self.X_train, self.y_train)
        else:
            self.estimator = calibrator.fit(self.X_test, self.y_test)

        # Reset all prediction properties since we changed the model attribute
        self.reset_prediction_attributes()

    @composed(crash, typechecked)
    def scoring(self, metric: Optional[str] = None, dataset: str = "test", **kwargs):
        """Get the scoring of a specific metric on the test set.

        Parameters
        ----------
        metric: str, optional (default=None)
            Name of the metric to calculate. Choose from any of sklearn's SCORERS or
            one of the CUSTOM_METRICS. If None, returns ATOM's final results for the
            model (ignores `dataset`).

        dataset: str, optional (default="test")
            Data set on which to calculate the metric. Options are "train" or "test".

        **kwargs
            Additional keyword arguments for the metric function.

        """
        metric_opts = CUSTOM_METRICS + list(SCORERS)

        # Check metric parameter
        if metric is None:
            return self._final_output()
        elif metric.lower() in METRIC_ACRONYMS:
            metric = METRIC_ACRONYMS[metric.lower()]
        elif metric.lower() not in metric_opts:
            raise ValueError(
                "Unknown value for the metric parameter, "
                f"got {metric}. Try one of {', '.join(metric_opts)}."
            )

        # Check set parameter
        dataset = dataset.lower()
        if dataset not in ("train", "test"):
            raise ValueError(
                "Unknown value for the dataset parameter. "
                "Choose between 'train' or 'test'."
            )

        try:
            if metric.lower() == "cm":
                return confusion_matrix(
                    getattr(self, f"y_{dataset}"), getattr(self, f"predict_{dataset}")
                )
            elif metric.lower() == "tn":
                return int(self.scoring("cm").ravel()[0])
            elif metric.lower() == "fp":
                return int(self.scoring("cm").ravel()[1])
            elif metric.lower() == "fn":
                return int(self.scoring("cm").ravel()[2])
            elif metric.lower() == "tp":
                return int(self.scoring("cm").ravel()[3])
            elif metric.lower() == "lift":
                tn, fp, fn, tp = self.scoring("cm").ravel()
                return float((tp / (tp + fp)) / ((tp + fn) / (tp + tn + fp + fn)))
            elif metric.lower() == "fpr":
                tn, fp, _, _ = self.scoring("cm").ravel()
                return float(fp / (fp + tn))
            elif metric.lower() == "tpr":
                _, _, fn, tp = self.scoring("cm").ravel()
                return float(tp / (tp + fn))
            elif metric.lower() == "sup":
                tn, fp, fn, tp = self.scoring("cm").ravel()
                return float((tp + fp) / (tp + fp + fn + tn))

            # Calculate the scorer via _score_func to use the prediction properties
            scorer = SCORERS[metric]
            if type(scorer).__name__ == "_ThresholdScorer":
                if self.T.task.startswith("reg"):
                    y_pred = getattr(self, f"predict_{dataset}")
                elif hasattr(self.estimator, "decision_function"):
                    y_pred = getattr(self, f"decision_function_{dataset}")
                else:
                    y_pred = getattr(self, f"predict_proba_{dataset}")
                    if self.T.task.startswith("bin"):
                        y_pred = y_pred[:, 1]
            elif type(scorer).__name__ == "_ProbaScorer":
                if hasattr(self.estimator, "predict_proba"):
                    y_pred = getattr(self, f"predict_proba_{dataset}")
                    if self.T.task.startswith("bin"):
                        y_pred = y_pred[:, 1]
                else:
                    y_pred = getattr(self, f"decision_function_{dataset}")
            else:
                y_pred = getattr(self, f"predict_{dataset}")

            return scorer._sign * float(scorer._score_func(
                getattr(self, f"y_{dataset}"), y_pred, **scorer._kwargs, **kwargs
            ))

        except (ValueError, TypeError):
            return f"Invalid metric for a {self.acronym} model with {self.T.task} task!"

    @composed(crash, method_to_log, typechecked)
    def save_estimator(self, filename: Optional[str] = None):
        """Save the estimator to a pickle file.

        Parameters
        ----------
        filename: str, optional (default=None)
            Name of the file to save. If None or "auto", the default name is used.

        """
        if not filename:
            filename = self.estimator.__class__.__name__
        elif filename == "auto" or filename.endswith("/auto"):
            filename = filename.replace("auto", self.estimator.__class__.__name__)

        with open(filename, "wb") as file:
            pickle.dump(self.estimator, file)
        self.T.log(f"{self.fullname} estimator saved successfully!", 1)

# Stochastic Gradient Descent (SGD)
-----------------------------------

Stochastic Gradient Descent is a simple yet very efficient approach to fitting linear
 classifiers and regressors under convex loss functions. Even though SGD has been
 around in the machine learning community for a long time, it has received a
 considerable amount of attention just recently in the context of large-scale learning.

Corresponding estimators are:

* [SGDClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html)
  for classification tasks.
* [SGDRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDRegressor.html)
  for regression tasks.

Read more in sklearn's [documentation](https://scikit-learn.org/stable/modules/sgd.html).


<br><br>
## Hyperparameters
------------------

* By default, the estimator adopts the default parameters provided by it's package.
  See the [user guide](../../../user_guide/#parameter-customization) on how to
  customize them.
* The `l1_ratio` parameter is only used when penalty = 'elasticnet'.
* The `eta0` parameter is only used when learning_rate != 'optimal'.
* The `n_jobs` and `random_state` parameters are set equal to those of the
 `training` instance.

<a name="atom"></a>
<table>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Dimensions:</strong></td>
<td width="75%" style="background:white;">
<strong>loss: str</strong>
<blockquote>
<ul>
<li>classifier: default='hinge'<br>
 Categorical(['hinge', 'log', 'modified_huber', 'squared_hinge', 'perceptron'], name='loss')</li>
<li>regressor: default='squared_loss'<br>
 Categorical(['squared_loss', 'huber', 'epsilon_insensitive', 'squared_epsilon_insensitive'], name='loss')</li>
</ul>
</blockquote>
<strong>penalty: str, default='l2'</strong>
<blockquote>
Categorical(['none', 'l1', 'l2', 'elasticnet'], name='penalty')
</blockquote>
<strong>alpha: float, default=1e-4</strong>
<blockquote>
Real(1e-4, 1.0, 'log-uniform', name='alpha')
</blockquote>
<strong>l1_ratio: float, default=0.15</strong>
<blockquote>
Categorical(np.linspace(0.1, 0.9, 9), name='l1_ratio').
</blockquote>
<strong>epsilon: float, default=0.1</strong>
<blockquote>
Real(1e-4, 1.0, 'log-uniform', name='epsilon')
</blockquote>
<strong>learning_rate: str, default='optimal'</strong>
<blockquote>
Categorical(['constant', 'invscaling', 'optimal', 'adaptive'], name = 'learning_rate')
</blockquote>
<strong>eta0: float, default=1e-4</strong>
<blockquote>
Real(1e-4, 1.0, 'log-uniform', name='eta0').
</blockquote>
<strong>power_t: float, default=0.5</strong>
<blockquote>
Categorical(np.linspace(0.1, 0.9, 9), name='power_t')
</blockquote>
<strong>average: bool, default=False</strong>
<blockquote>
Categorical([True, False], name='average')
</blockquote>
</td></tr>
</table>



<br><br><br>
## Attributes
-------------

### Data attributes

You can use the same [data attributes](../../ATOM/atomclassifier#data-attributes)
 as the `training` instances to check the dataset that was used to fit a particular
 model. These can differ from each other if the model needs scaled features and the
 data wasn't already scaled. Note that, unlike with the `training` instances, these
 attributes not be updated (i.e. they have no `@setter`).
<br><br>


### Utility attributes

<a name="atom"></a>
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Attributes:</strong></td>
<td width="75%" style="background:white;">
<strong>bo: pd.DataFrame</strong>
<blockquote>
Dataframe containing the information of every step taken by the BO. Columns include:
<ul>
<li>'params': Parameters used in the model.</li>
<li>'estimator': Estimator used for this iteration (fitted on last cross-validation).</li>
<li>'score': Score of the chosen metric. List of scores for multi-metric.</li>
<li>'time_iteration': Time spent on this iteration.</li>
<li>'time': Total time spent since the start of the BO.</li>
</ul>
</blockquote>
<strong>best_params: dict</strong>
<blockquote>
Dictionary of the best combination of hyperparameters found by the BO.
</blockquote>
<strong>estimator: class</strong>
<blockquote>
Estimator instance with the best combination of hyperparameters fitted on the complete training set.
</blockquote>
<strong>time_bo: str</strong>
<blockquote>
Time it took to run the bayesian optimization algorithm.
</blockquote>
<strong>metric_bo: float or list</strong>
<blockquote>
Best metric score(s) on the BO.
</blockquote>
<strong>time_fit: str</strong>
<blockquote>
Time it took to train the model on the complete training set and calculate the
 metric(s) on the test set.
</blockquote>
<strong>metric_train: float or list</strong>
<blockquote>
Metric score(s) on the training set.
</blockquote>
<strong>metric_test: float or list</strong>
<blockquote>
Metric score(s) on the test set.
</blockquote>
<strong>metric_bagging: list</strong>
<blockquote>
Array of the bagging's results.
</blockquote>
<strong>mean_bagging: float</strong>
<blockquote>
Mean of the bagging's results.
</blockquote>
<strong>std_bagging: float</strong>
<blockquote>
Standard deviation of the bagging's results.
</blockquote>
<strong>results: pd.DataFrame</strong>
<blockquote>
Dataframe of the training results with the model acronym as index. Columns can include:
<ul>
<li><b>metric_bo:</b> Best score achieved during the BO.</li>
<li><b>time_bo:</b> Time spent on the BO.</li>
<li><b>metric_train:</b> Metric score on the training set.</li>
<li><b>metric_test:</b> Metric score on the test set.</li>
<li><b>time_fit:</b> Time spent fitting and evaluating.</li>
<li><b>mean_bagging:</b> Mean score of the bagging's results.</li>
<li><b>std_bagging:</b> Standard deviation score of the bagging's results.</li>
<li><b>time_bagging:</b> Time spent on the bagging algorithm.</li>
<li><b>time:</b> Total time spent on the whole run.</li>
</ul>
</blockquote>
</td>
</tr>
</table>
<br>


### Prediction attributes

The prediction attributes are not calculated until the attribute is called for the
 first time. This mechanism avoids having to calculate attributes that are never
 used, saving time and memory.

<a name="atom"></a>
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Prediction attributes:</strong></td>
<td width="75%" style="background:white;">
<strong>predict_train: np.ndarray</strong>
<blockquote>
Predictions of the model on the training set.
</blockquote>
<strong> predict_test: np.ndarray</strong>
<blockquote>
Predictions of the model on the test set.
</blockquote>
<strong>decision_function_train: np.ndarray</strong>
<blockquote>
Decision function scores on the training set (only if classifier).
</blockquote>
<strong>decision_function_test: np.ndarray</strong>
<blockquote>
Decision function scores on the test set (only if classifier).
</blockquote>
<strong>score_train: np.float64</strong>
<blockquote>
Model's score on the training set.
</blockquote>
<strong>score_test: np.float64</strong>
<blockquote>
Model's score on the test set.
</blockquote>
</tr>
</table>
<br><br><br>


## Methods
----------

The majority of the [plots](../../../user_guide/#plots) and [prediction methods](../../../user_guide/#predicting)
 can be called directly from the `models`, e.g. `atom.sgd.plot_permutation_importance()` or `atom.sgd.predict(X)`.
 The remaining utility methods can be found hereunder:
<br><br>

<table>
<tr>
<td width="15%"><a href="#models-calibrate">calibrate</a></td>
<td>Calibrate the model.</td>
</tr>

<tr>
<td width="15%"><a href="#models-reset-prediction-attributes">reset_prediction_attributes</a></td>
<td>Clear all the prediction attributes.</td>
</tr>

<tr>
<td width="15%"><a href="#models-scoring">scoring</a></td>
<td>Get the scoring of a specific metric on the test set.</td>
</tr>

<tr>
<td><a href="#models-save-estimator">save_estimator</a></td>
<td>Save the estimator to a pickle file.</td>
</tr>
</table>
<br>


<a name="models-calibrate"></a>
<pre><em>method</em> <strong style="color:#008AB8">calibrate</strong>(\*\*kwargs)
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/basemodel.py#L827">[source]</a></div></pre>
<div style="padding-left:3%">
Applies probability calibration on the estimator. The calibration is done using the
 [CalibratedClassifierCV](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html)
 class from sklearn. The calibrator will be trained via cross-validation on a subset
 of the training data, using the rest to fit the calibrator. The new classifier will
 replace the `estimator` attribute. After calibrating, all prediction attributes will
 reset. Only if classifier.
<br /><br />
<table>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>**kwargs</strong>
<blockquote>
Additional keyword arguments for the CalibratedClassifierCV instance.
Using cv='prefit' will use the trained model and fit the calibrator on
the test set. Note that doing this will result in data leakage in the
test set. Use this only if you have another, independent set for testing.
</blockquote>
</tr>
</table>
</div>
<br />


<a name="models-reset-prediction-attributes"></a>
<pre><em>method</em> <strong style="color:#008AB8">reset_prediction_attributes</strong>()
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/basemodel.py#L655">[source]</a></div></pre>
<div style="padding-left:3%">
Clear all the prediction attributes. Use this method to free some memory before saving
 the class.
</div>
<br />


<a name="models-scoring"></a>
<pre><em>method</em> <strong style="color:#008AB8">scoring</strong>(metric=None, dataset='test')
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/basemodel.py#L859">[source]</a></div></pre>
<div style="padding-left:3%">
Returns the model's score for a specific metric.
<br /><br />
<table>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>metric: str or None, optional (default=None)</strong>
<blockquote>
Name of the metric to calculate. Choose from any of sklearn's [SCORERS](https://scikit-learn.org/stable/modules/model_evaluation.html#the-scoring-parameter-defining-model-evaluation-rules)
 or one of the following custom metrics (only if classifier):
<ul>
<li>'cm' or 'confusion_matrix' for an array of the confusion matrix.</li>
<li>'tn' for true negatives.</li>
<li>'fp' for false positives.</li>
<li>'fn' for false negatives.</li>
<li>'lift' for the lift metric.</li>
<li>'fpr' for the false positive rate.</li>
<li>'tpr' for true positive rate.</li>
<li>'sup' for the support metric.</li>
</ul>
If None, returns the final results for this model (ignores the `dataset` parameter).
</blockquote>
<strong>dataset: str, optional (default='test')</strong>
<blockquote>
Data set on which to calculate the metric. Options are 'train' or 'test'.
</blockquote>
</tr>
</table>
</div>
<br />


<a name="models-save-estimator"></a>
<pre><em>method</em> <strong style="color:#008AB8">save_estimator</strong>(filename=None)
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/basemodel.py#L945">[source]</a></div></pre>
<div style="padding-left:3%">
Save the estimator to a pickle file.
<br /><br />
<table>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>filename: str or None, optional (default=None)</strong>
<blockquote>
Name of the file to save. If None or 'auto', the estimator's name is used.
</blockquote>
</tr>
</table>
</div>
<br />


## Example
----------

```python
from atom import ATOMClassifier

atom = ATOMClassifier(X, y)
atom.run(models='SGD', metric='recall', bo_params={'cv': 3})
```
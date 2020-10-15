# Gaussian Naive bayes (GNB)
----------------------------

Gaussian Naive Bayes implements the Naive Bayes algorithm for classification. The
 likelihood of the features is assumed to be Gaussian.

Corresponding estimators are:

* [GaussianNB](https://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.GaussianNB.html)
  for classification tasks.

Read more in sklearn's [documentation](https://scikit-learn.org/stable/modules/naive_bayes.html#gaussian-naive-bayes).


<br><br>
## Hyperparameters
------------------

* By default, the estimator adopts the default parameters provided by it's package.
  See the [user guide](../../../user_guide/#parameter-customization) on how to
  customize them.
* GNB has no parameters to tune with the BO.



<br><br>
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
<strong>estimator: class</strong>
<blockquote>
Estimator instance fitted on the complete training set.
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
<li><b>name:</b> Name of the model.</li>
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
<strong>predict_proba_train: np.ndarray</strong>
<blockquote>
Predicted probabilities of the model on the training set.
</blockquote>
<strong>predict_proba_test: np.ndarray</strong>
<blockquote>
Predicted probabilities of the model on the test set.
</blockquote>
<strong>predict_log_proba_train: np.ndarray</strong>
<blockquote>
Predicted log probabilities of the model on the training set.
</blockquote>
<strong>predict_log_proba_test: np.ndarray</strong>
<blockquote>
Predicted log probabilities of the model on the test set.
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
 can be called directly from the `model`, e.g. `atom.gnb.plot_permutation_importance()` or `atom.gnb.predict(X)`.
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
 reset.
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
 or one of the following custom metrics:
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
atom.run(models='GNB')
```
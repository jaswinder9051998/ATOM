# Introduction
--------------

There is no magic formula in data science that can tell us which type of machine
 learning algorithm will perform best for a specific use-case. Best practices tell
 us to start with a simple model (e.g. linear regression) and build up to more
 complicated models (e.g. logistic regression -> random forest -> multilayer perceptron)
 if you are not satisfied with the results. Unfortunately, different models require
 different data cleaning steps, tuning a new set of hyperparameters, etc. Refactoring
 the code for all these steps can be very time consuming. This result in many data
 scientists just using the model best known to them and fine-tuning this particular
 model without ever trying other ones. This can result in poor performance (because
 the model is just not the right one for the task) or in poor time management (because you
 could have achieved a similar performance with a simpler/faster model).  
 
ATOM is here to help us solve these issues. With just a few lines of code, you can
 perform basic data cleaning steps, select relevant features and compare the
 performance of multiple models on a given dataset. ATOM should be able to provide
 quick insights on which algorithms perform best for the task at hand and provide an
 indication of the feasibility of the ML solution.
   
It is important to realize that ATOM is not here to replace all the work a data
 scientist has to do before getting his model into production. ATOM doesn't spit out
 production-ready models just by tuning some parameters in its API. After helping you
 to determine the right model, you will most probably need to fine-tune it using
 use-case specific features and data cleaning steps in order to achieve maximum
 performance.

So, this sounds a bit like AutoML, how is ATOM different than 
 [auto-sklearn](https://automl.github.io/auto-sklearn/master/) or
 [TPOT](http://epistasislab.github.io/tpot/)? Well, ATOM does AutoML in the sense
 that it helps you find the best model for a specific task, but contrary to the
 aforementioned packages, it does not actively search for the best model. It just
 runs all of them and let you pick the one that you think suites the best.
 AutoML packages are often black boxes to which you provide data, and magically,
 a good model comes out. Although it works great, they often produce complicated
 pipelines with low explainability, hard to sell to the business. In this, ATOM excels.
 Every step of the pipeline is accounted for, and using the provided plotting methods,
 its easy to demonstrate why a model is better/worse than the other.



<br><br>
# First steps
-------------

You can quickly install atom via `pip` or `conda`, see the [intallation guide](../getting_started/#installation).
 The easiest way to use ATOM is through [ATOMClassifier](../API/ATOM/atomclassifier)
 or [ATOMRegressor](../API/ATOM/atomregressor). These classes are wrappers for all
 other data cleaning, training and plotting methods. Contrary to sklearn's API,
 the ATOM instance contains the data you want to manipulate. Calling a method will
 apply all transformations on the data it contains.
 
First, create an ATOM instance and provide the data you want to use.

    atom = ATOMClassifier(X, y)

Apply data cleaning methods through the class. For example, calling the
[impute](../API/ATOM/atomclassifier/#atomclassifier-impute) will impute all missing
 values in the dataset.

    atom.impute(strat_num='median', strat_cat='most_frequent', min_frac_rows=0.1)

Fit the models you want to compare to the data.

    atom.run(['GNB', 'ET', 'MLP], metric='average_precision', n_calls=25, n_random_starts=10)

Analyze the results:

    atom.ET.feature_importances(show=10, filename='feature_importance_plot')
    atom.plot_prc(title='Precision-recall curve comparison plot')


<br><br>
# Data cleaning
---------------

ATOM provides four classes that can help you perform standard data cleaning steps:

<br>

### Standard data cleaning steps

<br>

### Scaling the features

<br>

### Handling missing values

<br>

### Encoding categorical features

<br>

### Handling outliers in the training set

<br>

### Balancing the data






<br><br>
# Feature engineering
---------------------

<cite>
<center>
"Applied machine learning" is basically feature engineering. ~ Andrew Ng.
</center>
</cite>


<br>
Feature engineering is the process of creating new features from the existing ones,
 in order to capture relationships with the target column that the first set of
 features didn't had on their own. This process is very important to improve the
 performance of machine learning algorithms. Although feature engineering works best
 when the data scientist applies use-case specific transformations, there are ways to
 do this in an automated manner, without prior domain knowledge. One of the problems
 of creating new features without human expert intervention, is that many of the newly
 created features can be useless, i.e. they do not help the algorithm to make better
 predictions. Even worse, having useless features can drop your performance. To avoid
 this, we perform feature selection, a process in which we select the relevant features 
 in the dataset. Click [here](examples/feature_engineering/feature_engineering.md) for an example.


<br>

### Generating new features

The [FeatureGenerator](API/feature_engineering/feature_generator.md) class creates
 new non-linear features based on the original feature set. It can be accessed from
 an ATOM instance through the [feature_generation](../API/ATOM/atomclassifier/#atomclassifier-feature-generation)
 method. You can choose between two strategies: Deep Feature Synthesis and Genetic
 Feature Generation.
 
**Deep Feature Synthesis**

Deep feature synthesis (DFS) applies the selected operators on the features in
 the dataset. For example, if the operator is 'log', it will create the new feature
 `LOG(old_feature)` and if the operator is 'mul', it will create the new feature
 `old_feature_1 x old_feature_2`. DFS can create many new features. The operators
 can be chosen through the `operators` parameter. Available options are:
<ul>
<li><b>add: </b>Sum two features together.</li>
<li><b>sub: </b>Subtract two features from each other.</li>
<li><b>mul: </b>Multiply two features with each other.</li>
<li><b>div: </b>Divide two features with each other.</li>
<li><b>srqt: </b>Take the square root of a feature.</li>
<li><b>log: </b>Take the logarithm of a feature.</li>
<li><b>sin: </b>Calculate the sine of a feature.</li>
<li><b>cos: </b>Calculate the cosine of a feature.</li>
<li><b>tan: </b>Calculate the tangent of a feature.</li>
</ul>

ATOM's implementation of DFS uses the [featuretools](https://www.featuretools.com/) package.

!!! tip
    DFS can create many new features and not all of them will be useful. Use the
    [FeatureSelector](./API/feature_engineering/feature_selector.md) class
    to reduce the number of features!

!!! warning
    When using DFS with n_jobs>1, make sure to protect your code with a if
    \__name__ == "\__main__". Featuretools uses dask, which uses python multiprocessing
    for parallelization. The spawn method on multiprocessing starts a new python
    process, which requires it to import the \__main__ module before it can do
    its task.

<br>
**Genetic Feature Generation**

Genetic feature generation (GFG) uses [genetic programming](https://en.wikipedia.org/wiki/Genetic_programming),
 a branch of evolutionary programming, to determine which features are successful and
 create new ones based on those. Where DFS' method can be seen as some kind of "brute force"
 for feature engineering, GFG tries to improve its features with every generation of
 the algorithm. GFG uses the same operators as DFS, but instead of only applying the
 transformations once, it evolves them further, creating complicated non-linear
 combinations of features with many transformations. The new features are given the
 name `Feature N` for the N-th feature. You can access the genetic feature's fitness
 and description (how they are calculated) through the `genetic_features` attribute.

ATOM uses the
 [SymbolicTransformer](https://gplearn.readthedocs.io/en/stable/reference.html#symbolic-transformer)
 class from the [gplearn](https://gplearn.readthedocs.io/en/stable/index.html) package
 for the genetic algorithm. Read more about this implementation
 [here](https://gplearn.readthedocs.io/en/stable/intro.html#transformer).

<br>

### Selecting useful features

The [FeatureSelector](API/feature_engineering/feature_selector.md) class provides
 tooling to select the relevant features from a dataset. It can be accessed from an
 ATOM instance through the [feature_selection](../API/ATOM/atomclassifier/#atomclassifier-feature-selection)
 method. The following strategies are implemented: univariate, PCA, SFM, RFE and RFECV.

!!! tip

    Use the [plot_feature_importance](API/plots/plot_feature_importance.md) method to
    examine how much a specific feature contributes to the fianl predictions. If the
    model doesn't have a `feature_importances_` attribute, use 
    [plot_permutation_importance](API/plots/plot_permutation_importance.md) instead.

**Univariate**

Univariate feature selection works by selecting the best features based on univariate statistical F-test.
 The test is provided via the `solver` parameter. It takes any function taking two arrays (X, y),
 and returning arrays (scores, p-values).
 Read more in the sklearn [documentation](https://scikit-learn.org/stable/modules/feature_selection.html#univariate-feature-selection).

**Principal Components Analysis**

Applying PCA will reduce the dimensionality of the dataset by maximizing the variance of each dimension.
 The new features will be called Component 0, Component 1, etc... The dataset will be
 scaled before applying the transformation (if it wasn't already).

**Selection from model**

SFM uses a supervised machine learning model with `feature_importances_` or `coef_`
 attributes to select the best features in a dataset based on importance weights.
 The model is provided through the `solver` parameter and can be already fitted.
 ATOM allows you to input one of the pre-defined models, e.g. `solver='RF'`. If you
 called the FeatureSelector class without using the ATOM wrapper, don't forget to
 indicate the task adding `_class` or `_reg` after the name, e.g. `RF_class` to use a
 random forest classifier.


**Recursive feature elimination**

Select features by recursively considering smaller and smaller sets of features.
 First, the estimator is trained on the initial set of features and the importance
 of each feature is obtained either through a `coef_` attribute or through a
 `feature_importances_` attribute. Then, the least important features are pruned from
 current set of features. That procedure is recursively repeated on the pruned set
 until the desired number of features to select is eventually reached. Note that, since
 RFE needs to fit the model again every iteration, this method can be fairly slow.
  
RFECV applies the same algorithm as RFE but uses a cross-validated metric (under the
 scoring parameter, see [RFECV](https://scikit-learn.org/stable/modules/generated/sklearn.feature_selection.RFECV.html#sklearn.feature_selection.RFECV))
 to assess every step's performance. Also, where RFE returns the number of features selected
 by `n_features`, RFECV returns the number of features that achieved the optimal score
 on the specified metric. Note that this is not always equal to the amount specified
 by `n_features`.

**Removing features with low variance**

Variance is the expectation of the squared deviation of a random variable from its mean.
 Features with low variance have many values repeated, which means the model will not
 learn a lot from them. [FeatureSelector](API/feature_engineering/feature_selector.md)
 removes all features where the same value is repeated in at least `max_frac_repeated`
 fraction of the rows. The default option is to remove a feature if all values in it
 are the same. 


**Removing features with multi-collinearity**

Two features that are highly correlated are redundant. Two will not contribute more
 than only one of them. [FeatureSelector](API/feature_engineering/feature_selector.md)
 will remove one of two features that have a Pearson correlation coefficient larger 
 than `max_correlation`. The default option is to remove one of 2 equal columns.
 A dataframe of the removed features and their correlation values can be accessed
 through the `collinear` attribute.


<br><br>
# Model fitting and evaluation
------------------------------

<br>

### Multi-metric runs


<br>

### Hyperparameter tuning


<br>

### Bagging


<br>

### Early stopping



<br><br>
# Model subclasses
------------------



<br><br>
# Handle new data streams
-------------------------

It is possible, that after running the whole ATOM pipeline, you would like to apply
 the same data transformations and maybe make predictions on a new dataset. This is
 possible using ATOM's [prediction methods]().



<br><br>
# Plotting
----------

After fitting the models to the data, it's time to analyze the results. ATOM provides
 many plotting methods to compare the model performances. Click [here](../API/ATOM/atomclassifier/#plots)
 for a list of the available plots. The plot descriptions and examples can be find in
 the API section. ATOM uses the [matplotlib](https://matplotlib.org/) and 
 [seaborn](https://seaborn.pydata.org/) packages for plotting.

The plot methods can be called from the ATOM instance directly, e.g. `atom.plot_roc()`,
 or from one of the model subclasses, `e.g. atom.LGB.plot_roc()`. If called from ATOM,
 it will make the plot for all models in the pipeline. This can be useful to compare 
 the results of multiple models. If called from the model subclass, it will only make
 the plot for that model. Use this option if you want information just for a specific
 model or to make the plot a bit less crowded.

Apart from the plot-specific parameters they may have, all plots have four parameters in common:
<ul>
<li>The `title` parameter allows you to add a custom title to the plot.
<li>The `figsize` parameter allows you to adjust the plot's size.
<li>The `filename` parameter is used to save the plot as a .png file.
<li>The `display` parameter determines whether the plot is rendered.</li>
 </ul>
 

You can customize the following plot aesthetics using the [plotting properties](../API/ATOM/atomclassifier/#plotting-properties):
<ul>
<li>Seaborn style</li>
<li>Color palette</li>
<li>Title fontsize</li>
<li>Label and legend fontsize</li>
<li>Tick fontsize</li>
</ul>
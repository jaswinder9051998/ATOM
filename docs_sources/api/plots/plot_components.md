# plot_components
------------------

<a name="plot-components"></a>
<pre><em>function</em> atom.plots.<strong style="color:#008AB8">plot_components</strong>(show=None, title=None, figsize=None, filename=None, display=True)
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/plots.py#L146">[source]</a></div></pre>
<div style="padding-left:3%">
Plot the explained variance ratio per components. Can only be called from
 an [ATOMClassifier](../ATOM/atomclassifier.md)/[ATOMRegressor](../ATOM/atomregressor.md)
 or [FeatureSelector](../feature_engineering/feature_selector.md) instance that
 applied PCA on the dataset. Can't be called from the model subclasses.
<br /><br />
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>show: int or None, optional (default=None)</strong>
<blockquote>
Number of components to show. If None, the number of components in the data are plotted.
</blockquote>
<strong>title: str or None, optional (default=None)</strong>
<blockquote>
Plot's title. If None, the default option is used.
</blockquote>
<strong>figsize: tuple, optional (default=None)</strong>
<blockquote>
Figure's size, format as (x, y). If None, adapts size to `show` parameter.
</blockquote>
<strong>filename: str or None, optional (default=None)</strong>
<blockquote>
Name of the file (to save). If None, the figure is not saved.
</blockquote>
<strong>display: bool, optional (default=True)</strong>
<blockquote>
Whether to render the plot.
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
atom.feature_selection(strategy='PCA', n_features=11)
atom.plot_components()
```
![plot_correlation](./img/plot_components.png)
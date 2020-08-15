# plot_residuals
----------------

<pre><em>function</em> atom.plots.<strong style="color:#008AB8">plot_residuals</strong>(models=None, title=None, figsize=(10, 6), filename=None, display=True)
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/plots.py#L336">[source]</a></div></pre>
<div style="padding-left:3%">
The plot shows the residuals (difference between the predicted and the
 true value) on the vertical axis and the independent variable on the
 horizontal axis. The gray, intersected line shows the identity line. This
 plot can be useful to analyze the variance of the error of the regressor.
 If the points are randomly dispersed around the horizontal axis, a linear
 regression model is appropriate for the data; otherwise, a non-linear model
 is more appropriate. Only for regression tasks.
<br /><br />
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>models: str, sequence or None, optional (default=None)</strong>
<blockquote>
Name of the models to plot. If None, all models in the pipeline are selected.
</blockquote>
<strong>title: str or None, optional (default=None)</strong>
<blockquote>
Plot's title. If None, the default option is used.
</blockquote>
<strong>figsize: tuple, optional (default=(10, 6))</strong>
<blockquote>
Figure's size, format as (x, y).
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
from atom import ATOMRegressor

atom = ATOMRegressor(X, y)
atom.run(['OLS', 'LGB'], metric='MAE')
atom.plot_residuals()
```
![plot_errors](./img/plot_residuals.png)
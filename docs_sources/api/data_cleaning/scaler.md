# Scaler
--------

<pre><em>class</em> atom.data_cleaning.<strong style="color:#008AB8">Scaler</strong>(verbose=0, logger=None)
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/atom.py#L114">[source]</a></div></pre>
Scales data to mean=0 and std=1. Standardization of a dataset is a common requirement
 for many machine learning estimators: they might behave badly if the individual
 features do not more or less look like standard normally distributed data (e.g.
 Gaussian with 0 mean and unit variance).

<table>
<tr>
<td width="20%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="80%" style="background:white;">
<strong>verbose: int, optional (default=0)</strong>
<blockquote>
Verbosity level of the class. Possible values are:
<ul>
<li>0 to not print anything.</li>
<li>1 to print basic information.</li>
<li>2 to print detailed information.</li>
</ul>
</blockquote>

<strong>logger: bool, str, class or None, optional (default=None)</strong>
<blockquote>
<ul>
<li>If None: Doesn't save a logging file.</li>
<li>If bool: True for logging file with default name, False for no logger.</li>
<li>If str: Name of the logging file. 'auto' to create an automatic name.</li>
<li>If class: python Logger object.</li>
</ul>
</blockquote>
</td>
</tr>
</table>
<br>

## Methods
---------

<table width="100%">
<tr>
<td><a href="#scaler-fit">fit</a></td>
<td>Fit the class.</td>
</tr>

<tr>
<td><a href="#scaler-fit-transform">fit_transform</a></td>
<td>Fit the class and return the transformed data.</td>
</tr>

<tr>
<td><a href="#scaler-get-params">get_params</a></td>
<td>Get parameters for this estimator.</td>
</tr>

<tr>
<td><a href="#scaler-save">save</a></td>
<td>Save the instance to a pickle file.</td>
</tr>


<tr>
<td><a href="#scaler-set-params">set_params</a></td>
<td>Set the parameters of this estimator.</td>
</tr>

<tr>
<td><a href="#scaler-transform">transform</a></td>
<td>Transform the data.</td>
</tr>
</table>
<br>



<a name="scaler-fit"></a>
<pre><em>function</em> Scaler.<strong style="color:#008AB8">fit</strong>(X, y=None) 
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/atom.py#L2155">[source]</a></div></pre>
<div style="padding-left:3%">
Fit the class.
<br><br>
</div>
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>X: dict, sequence, np.array or pd.DataFrame</strong>
<blockquote>
Data containing the features, with shape=(n_samples, n_features).
</blockquote>
<strong>y: int, str, sequence, np.array or pd.Series, optional (default=None)</strong>
<blockquote>
Does nothing. Implemented for continuity of the API.
</blockquote>
</tr>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Returns:</strong></td>
<td width="75%" style="background:white;">
<strong>self: Scaler</strong>
<blockquote>
Fitted instance of self.
</blockquote>
</tr>
</table>
<br />


<a name="scaler-fit-transform"></a>
<pre><em>function</em> Scaler.<strong style="color:#008AB8">fit_transform</strong>(X, y=None) 
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/atom.py#L2155">[source]</a></div></pre>
<div style="padding-left:3%">
Fit the Scaler and return the scaled data.
<br><br>
</div>
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>X: dict, sequence, np.array or pd.DataFrame</strong>
<blockquote>
Data containing the features, with shape=(n_samples, n_features).
</blockquote>
<strong>y: int, str, sequence, np.array or pd.Series, optional (default=None)</strong>
<blockquote>
Does nothing. Implemented for continuity of the API.
</blockquote>
</tr>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Returns:</strong></td>
<td width="75%" style="background:white;">
<strong>X: pd.DataFrame</strong>
<blockquote>
Scaled feature set.
</blockquote>
</tr>
</table>
<br />

<a name="scaler-get-params"></a>
<pre><em>function</em> Scaler.<strong style="color:#008AB8">get_params</strong>(deep=True) 
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/atom.py#L2155">[source]</a></div></pre>
<div style="padding-left:3%">
Get parameters for this estimator.
<br><br>
</div>
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>deep: bool, default=True</strong>
<blockquote>
If True, will return the parameters for this estimator and contained subobjects that are estimators.
</blockquote>
</tr>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Returns:</strong></td>
<td width="75%" style="background:white;">
<strong>params: dict</strong>
<blockquote>
Dictionary of the parameter names mapped to their values.
</blockquote>
</tr>
</table>
<br />


<a name="scaler-save"></a>
<pre><em>function</em> Scaler.<strong style="color:#008AB8">save</strong>(filename=None)
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/atom.py#L696">[source]</a></div></pre>
<div style="padding-left:3%">
Save the instance to a pickle file.
<br><br>
<table>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>filename: str or None, optional (default=None)</strong>
<blockquote>
Name to save the file with. None to save with default name.
</blockquote>
</tr>
</table>
</div>
<br>

<a name="scaler-set-params"></a>
<pre><em>function</em> Scaler.<strong style="color:#008AB8">set_params</strong>(**params) 
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/atom.py#L2155">[source]</a></div></pre>
<div style="padding-left:3%">
Set the parameters of this estimator.
<br><br>
</div>
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>\*\*params: dict</strong>
<blockquote>
Estimator parameters.
</blockquote>
</tr>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Returns:</strong></td>
<td width="75%" style="background:white;">
<strong>self: Scaler</strong>
<blockquote>
Estimator instance.
</blockquote>
</tr>
</table>
<br />


<a name="scaler-transform"></a>
<pre><em>function</em> Scaler.<strong style="color:#008AB8">transform</strong>(X, y=None) 
<div align="right"><a href="https://github.com/tvdboom/ATOM/blob/master/atom/atom.py#L2155">[source]</a></div></pre>
<div style="padding-left:3%">
Scale the data.
<br><br>
</div>
<table width="100%">
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Parameters:</strong></td>
<td width="75%" style="background:white;">
<strong>X: dict, sequence, np.array or pd.DataFrame</strong>
<blockquote>
Data containing the features, with shape=(n_samples, n_features).
</blockquote>
<strong>y: int, str, sequence, np.array or pd.Series, optional (default=None)</strong>
<blockquote>
Does nothing. Implemented for continuity of the API.
</blockquote>
</tr>
<tr>
<td width="15%" style="vertical-align:top; background:#F5F5F5;"><strong>Returns:</strong></td>
<td width="75%" style="background:white;">
<strong>X: pd.DataFrame</strong>
<blockquote>
Scaled feature set.
</blockquote>
</tr>
</table>
<br />


## Example
---------
```python
from atom.data_cleaning import Scaler

X_scaled = Scaler().fit_transform(X)
```
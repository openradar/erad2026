---
jupyter:
  jupytext:
    text_representation:
      extension: .md
      format_name: markdown
      format_version: '1.3'
      jupytext_version: 1.19.1
  kernelspec:
    display_name: Python 3 (ipykernel)
    language: python
    name: python3
---

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
# An Introduction to Open Radar Science
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
## What is Open Science?

<div align="center">
<img src="https://www.earthdata.nasa.gov/s3fs-public/2021-11/Circle_Diagram_UPDATE_2.jpg?VersionId=pFRniRpjtgc_MEXUJKi9_sXLoMsSX.pB" width="500"/>
</div>

Image based on [Ramachandran et al. 2021](https://doi.org/10.1029/2020EA001562)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### What Does this look like in the Weather Radar Community?
- Since the late 2000s (and even before) there has been a number of major open source projects released (see e.g. https://openradarscience.org).
- Some of them are in a mature stage and are widely used in an academic (mostly) but also operational environment
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
- Most make use of modern tools (e.g. github, conda, docker) and practices (e.g. Continuous Integration, automatic tests) that make them easy to evolve and deploy
- Most are backed by major weather services or academic institutions
Projects are not competing among them but collaborating : Best practices and inter-operability are discussed regularly and joint open source courses have been organized for years at major radar conferences (AMS, ERAD)  
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
## The Conceptual Idea of the Open Radar Stack
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
### Common weather radar processing workflows

![radar workflows](images/open-radar-workflow-tasks.png)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
### The Open Radar Tools

![open radar tools](images/open-radar-tools.png)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Additional Tools that Can be used with/for Weather Radar Data

- [MetPy](https://unidata.github.io/MetPy/latest/index.html)
    - a collection of tools in Python for reading, visualizing, and performing calculations with weather data
- [tobac](https://tobac.readthedocs.io/en/latest/)
    - a Python package for rapidly identify, track and analyze clouds in different types of gridded datasets, such as 3D model output from cloud-resolving model simulations or 2D data from satellite retrievals.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
## Introductions of the Core Open Radar Stack
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### Wradlib *(Keep the magic to the minimum (let the user decide))*
- https://wradlib.org
- One of the oldest packages (2011)
- Open platform for collaborative development of algorithms
- Python-based
- Linux/Windows/Mac
- Flat data model that allows maximum flexibility to interact with the data.
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
- xarray readers available (now in xradar as of 2.0)
- Comprehensively addresses the full radar processing chain
- Mainly geared to interactive use in research but used in operations too
- Easy to install (PyPI, conda, Docker Hub)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Functionality
<div>
<img src="images/wradlib-functionality.svg"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Sample Image
<div>
<img src="images/wradlib-images.png" width="600"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### Py-ART *(It's all about the data model)*
- https://arm-doe.github.io/pyart/
- Created in the context of the ARM program (2013)
- Open platform for collaborative development of algorithms
- Mostly Python-based (some modules in C, Cython and FORTRAN)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
- Linux/Windows/Mac
- Core : Radar object that structures the radar data and metadata mirroring the C/F Radial standard
- Limited scope. Base block to built upon
- Rich ecosystem of packages: ART-VIEW, PyTDA, PyDDA, TINT, Pyrad...
- Easy to install (PyPI, conda)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Functionality
<div>
<img src="images/pyart-functionality.svg"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Sample Image
<div>
<img src="images/pyart-images.png" width="800"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### Pyrad *(Flexible and replicable data processing chains with no programming)*
- https://github.com/MeteoSwiss/pyrad
- Initially developed at MeteoSwiss. Now shared development between MeteoSwiss and Météo-France
- Python-based weather radar data processing framework capable of operating in real time or off-line
- Core based on ARM-DOE Py-ART (Pyrad major contributor)
- Easy to install (PyPI, conda)
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Functionality
<div>
<img src="images/pyrad-functionality.svg"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Sample Image
<div>
<img src="images/pyrad-images.jpg"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### LROSE *(High quality building blocks forcomplex workflows)*
- http://lrose.net/ 
- Based on legacy of NCAR and CSU tools
- Fast native cross-platform applications
- Mostly C++
- Linux/Mac/partially Windows
- Many stand-alone tools
- Stores data in CF/Radial
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Functionality
<div>
<img src="images/lrose-functionality.svg"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Sample Image
<div>
<img src="images/lrose-images.png"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### BALTRAD *(Advanced Weather Radar Network)*
- Heritage from the Nordic Network NORDRAD. Partly funded by the EU. BALTRAD and BALTRAD+ projects (2009-2014). 13 partners in 10 countries
- Real-time data exchange and data processing
- Sub-packages written in different languages
    - Data exchange: JAVA
    - Data processing: C and Python
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
- Linux/Mac
- Distributed networking, partners exchange polar data and process them using a common toolbox
- Uses ODIM-H5
- Documentation: https://baltrad.github.io/  
- Code: https://github.com/baltrad
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Functionality
<div>
<img src="images/baltrad-functionality.svg"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Sample Image
<div>
<img src="images/baltrad-images.png"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### Conclusions on the Open Radar Stack
- Acknowledge software when you use it – treat it like a paper
    - Most projects have Digital Object Identifiers (DOIs)
- Contribute back to projects
    - Report bugs, suggest enhancements, share feedback!
- Do not be afraid to contribute
    - We all started somewhere – your code will be reviewed + tests ensure things do not break
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
- Open Source does not end at making things open
    - Support, documentation, consistency, etc. are required
- Take a look at existing projects to see if you can collaborate/coordinate!
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
## The Open Radar Community
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### More on Open Science: Beyond the Tools
<div>
<img src="images/secret-sauce.png"/>
</div>

- Open Science = Open Data + Open Algorithms + Open Software + Open Peer Review + Open Access Publication
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
- Thereby, science process and outputs can be:
    - ✅ Transparent
    - ✅ Reproducible
    - ✅ Transferrable
    - ✅ Collaborative
    - ✅ Credible!
    - ✅ Durable, sustainable
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
<div class="admonition alert alert-info">
    <p class="admonition-title" style="font-weight:bold">Important</p>
    No conflict between Intellectual Property Rights (IPR) and licensing.
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
#### Recommendations for Open Scientists
- Use Git for collaborative change/version code management
    - GitHub: github.com 
    - GitLab: gitlab.com
- Linux virtual machine on your local computer
    - Cost-effective near-replication of official environments
    - Good for development, even while traveling
    - VM is the starting point, a vehicle, for creating transferrable computational environments
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "subslide"} -->
- Today’s cloud instance is an “elaborated” VM (Jupyterhub/Binderhub)
- If you have a choice, use an open programming language
- Avoid proprietary algorithms like Numerical Recipes
- Publish code
- Publish data
- Publish code & data associated with a study/paper
- Publish in Open Access journals
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
### The Open Radar Forum - Establishing a Community of Practice
https://openradar.discourse.group/

<div>
<img src="images/open-radar-forum.png"/>
</div>
<!-- #endregion -->

<!-- #region editable=true slideshow={"slide_type": "slide"} -->
## Conclusions
https://openradarscience.org

<div>
<img src="images/openradar-landing-page.png"/>
</div>

- There is no “silver bullet” for open science
- Try to use open languages where possible
- Share your work!
- Join the conversation on the forum
- You can find more posts relevant to the Open Radar Community on our website (at the top) and on the forum
- We have monthly meetings! Join!
<!-- #endregion -->

```python editable=true slideshow={"slide_type": ""}

```

---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.19.1
  main_language: python
kernelspec:
  display_name: Python 3
  name: python3
---

::::{grid} 5

:::{grid-item}
```{image} ../../images/logos/radar_datatree_logo.png
:width: 150px
:alt: radar datatree Logo
```
:::

:::{grid-item}
```{image} ../../images/logos/xradar_logo.svg
:width: 150px
:alt: xradar Logo
```
:::

:::{grid-item}
```{image} ../../images/logos/Xarray_Icon_Final.svg
:width: 150px
:alt: xarray Logo
```
:::

:::{grid-item}
```{image} ../../images/logos/pyproj_logo.svg
:width: 150px
:alt: pyproj Logo
```
:::

:::{grid-item}
```{image} ../../images/logos/wradlib_logo.svg.png
:width: 125px
:alt: wradlib Logo
```
:::

::::

(workflow-overview)=
# Overview

This collection of notebooks demonstrates a complete radar processing workflow, from raw weather radar observations to quantitative precipitation estimation (QPE). Individual notebooks are largely self-contained and may be used independently, but they are organized according to the typical radar processing workflow.

The material is divided into three sections:

- [](#pre-course-material) - introduction to datasets, tools, and core functionality
- [](#main-course) - hands-on radar processing exercises using representative case studies
- [](#post-course-material) - resources for further exploration after the course

The notebooks assume basic familiarity with Python and scientific Python libraries such as NumPy, Xarray, and Matplotlib.

(pre-course-material)=
## Pre-Course Material

The pre-course material introduces datasets, tools, and core processing concepts used throughout the course. These notebooks are intended to familiarize participants with the radar observations, data structures, visualization methods, and supporting geospatial information before moving on to the main processing exercises.

The notebooks may also be explored independently and provide the necessary background for understanding the subsequent correction, gridding, and quantitative precipitation estimation workflows.

The pre-course notebooks are grouped into the following thematic areas:

### Radar Data Exploration

These notebooks provide an overview of the available radar datasets and their characteristics. They include examples of stratiform and convective precipitation cases, inspection of scan strategies, radar coverage, and basic visualization of the observations. The notebooks [](#inspect-single-pol) and [](#inspect-dual-pol) present data from two different radar sites and illustrate both stratiform and convective precipitation observations.

### Terrain and Beam Blockage

Digital elevation models (DEMs) are used to assess terrain-induced beam blockage. The [](#terrain-beamblockage) notebook demonstrates the generation of a DEM for the radar domain and the derivation of beam blockage fractions from radar beam geometry and terrain elevation.

### Quality Assurance and Quality Control *(under development)*

These notebooks will cover procedures to improve data quality prior to quantitative applications.

The [](#system_phidp), [](#delta-phidp) and [](#differential-phase) notebooks demonstrate the differential phase processing workflow, from estimating system differential phase and total differential phase shift to correcting biases, filtering and smoothing differential phase, and deriving specific differential phase..

### Radar Corrections *(under development)*

Processing steps that compensate for known measurement and observation effects. The [](#attenuation-correction-single-pol) notebook shows how to apply single-polarization attenuation correction using the Hitschfeld–Bordan and Krämer method's. The [](#attenuation-correction-dual-pol) notebook facilitates the ZPHI method to derive specific attenuation and correct reflectivity.

### Quantitative Precipitation Estimation (QPE) *(under development)*

Generation and evaluation of quantitative precipitation products derived from radar observations.

### Polar-to-Cartesian Gridding

Interpolation of polar radar observations onto a common Cartesian analysis grid. This step facilitates the combination of multiple radars and provides input for subsequent products such as precipitation estimation and nowcasting.

Common analysis grid generation and Polar-to-Cartesian interpolation is highlighted in [](#gridding-polar-data), Multi-radar compositing is shown in [](#composite-to-grid).

(main-course)=
## Main Course

The main course introduces the weather radar processing workflow using two representative precipitation events: [](#stratiform-case) and [](#convective-case). These datasets highlight the different characteristics and challenges associated with widespread layered precipitation and localized intense convection.

Throughout the exercises, participants will apply and evaluate the correction and processing techniques introduced in the pre-course material. In addition, [](#clear-air-case) is provided specifically for assessing the impact and quality of selected correction methods under non-precipitating conditions.

By working through these complementary cases, participants will gain practical experience with typical radar data issues and develop an understanding of how processing strategies may differ depending on meteorological conditions.

(post-course-material)=
## Post-Course Material

The [](#workflow-post-course) section provides additional resources, references, and suggestions for further exploration beyond the main course exercises. Rather than introducing new mandatory material, it serves as a collection of pointers and comments intended to support continued learning and experimentation.

Participants are encouraged to revisit the course datasets, explore alternative processing approaches, and consult the referenced documentation and literature for further study of radar data processing and evaluation techniques.
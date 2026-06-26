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
```{image} ../../images/logos/radar_datatree.png
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
:alt: xarray Logo
```
:::

:::{grid-item}
```{image} ../../images/logos/wradlib_logo.svg.png
:width: 125px
:alt: wradlib Logo
```
:::

::::


# Workflow Overview

This collection of notebooks demonstrates the complete processing chain from raw weather radar observations to quantitative precipitation estimation (QPE). Individual notebooks are largely self-contained and can be used independently, but they are organized according to the typical radar processing workflow.

## Radar Data Exploration

These notebooks provide an overview of the available radar datasets and their characteristics. They include examples of stratiform and convective precipitation cases, inspection of scan strategies, radar coverage, and basic visualization of the observations.

## Terrain and Beam Blockage

Digital elevation models (DEMs) are used to assess terrain-induced beam blockage. The notebooks demonstrate the generation of a DEM for the radar domain and the derivation of beam blockage fractions from radar beam geometry and terrain elevation.

## Quality Assurance and Quality Control (planned)

These notebooks will cover procedures to improve data quality prior to quantitative applications.

## Radar Corrections (planned)

Processing steps that compensate for known measurement effects.

## Quantitative Precipitation Estimation (QPE) (planned)

Generation and evaluation of precipitation products derived from radar observations.

## Polar-to-Cartesian Gridding

Interpolation of polar radar observations onto a common Cartesian analysis grid. This step facilitates the combination of multiple radars and provides input for subsequent products such as precipitation estimation and nowcasting.

- Polar-to-Cartesian interpolation
- Common analysis grid generation
- Multi-radar compositing
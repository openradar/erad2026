
# Short Course Outline

_Open Radar – Open Source Software Tools for Radar Data Processing 
From Raw Data to Analysis-Ready Fields_

```{attention}
This course outline and the accompanying course materials are still under development and will continue to evolve. Please check back regularly for updates.
```

## Summary

This short course provides a hands-on introduction to open-source weather radar processing, guiding participants through the complete workflow from raw radar data to analysis-ready precipitation products. Building on recent developments in the open radar science ecosystem, the course emphasises interoperable and reproducible workflows based on tools such as xradar, Py-ART, and wradlib. Participants will work with real-world datasets to perform quality control, apply essential corrections, and generate gridded radar products within a modern, xarray-based framework. In addition, the course highlights how established systems such as BALTRAD and LROSE can be integrated into these workflows, bridging research and operational environments. Particular emphasis is placed on transparency and adaptability of processing methods, enabling participants not only to apply existing tools but also to understand and modify key algorithmic components. The course forms the first part of a two-day training sequence and provides the processed datasets required for subsequent precipitation nowcasting applications.

## Course Type
Short Course (Full Day)

## Proposed Schedule
Saturday (full day, approximately 7–8 hours including coffee and lunch breaks)

## Conveners / Instructors
See [README](README.md#list-of-instructors).

## Motivation and Background

Weather radar observations play a central role in contemporary meteorology, underpinning applications such as severe weather monitoring, hydrology, and aviation. Despite their widespread use, the transformation of raw radar measurements into reliable and analysis-ready products remains a complex task that involves multiple processing steps, including quality control, correction procedures, and spatial transformations. In recent years, the open radar science ecosystem has evolved into a coherent and increasingly interoperable software stack. Tools such as Py-ART and wradlib are complemented by developments such as xradar, which provides a unified interface aligned with emerging standards such as CfRadial2/FM301. This evolution reflects a broader shift towards scalable, standards-compliant, and cloud-ready workflows. At the same time, recent training activities, have highlighted the importance of reproducible, notebook-based workflows and a more transparent treatment of processing algorithms. Building on both the ERAD Open Radar Science courses, the proposed course integrates these perspectives
by combining interoperable software usage with a stronger emphasis on workflow design and methodological understanding. The course is conceived as the first part of a two-day sequence, with a subsequent course focusing on precipitation nowcasting.

## Objectives

The course is designed to provide participants with a clear understanding of the radar data processing chain and to develop practical skills in applying open-source tools to real-world datasets. Particular emphasis is placed on interoperable workflows, including the role of xradar as a unifying interface for radar data access and representation, and on the integration of complementary processing systems. In addition, participants will be introduced to the conceptual design of processing workflows and to selected algorithmic components, enabling them to understand and adapt processing steps rather than relying solely on predefined routines. 

## Target Audience

The course is primarily intended for early-career researchers, including doctoral candidates and postdoctoral scientists, as well as operational meteorologists, hydrologists, and other practitioners working with precipitation data. Participants are expected to have a basic familiarity with Python, although extensive prior experience with radar data is not required.

## Course Format

The course follows a strongly practice-oriented format in which short introductory lectures are combined with guided hands-on sessions. All exercises are carried out in an interactive computing environment such as Jupyter Notebook. The full-day programme is structured to balance instruction and practical work, with regular breaks to maintain engagement. The schedule has a morning block focused on data access, quality control, corrections, and gridding followed by an afternoon block covering product
generation.  The schedule is interspersed with coffee breaks and a longer lunch break.

## Course Content

The course begins with an overview of the Open Radar Science framework, introducing the guiding principles of openness, reproducibility, and interoperability in radar meteorology. This session situates participants within the evolving open-source radar ecosystem and highlights the roles of key tools such as xradar, Py-ART, BALTRAD, LROSE and wradlib. Particular attention is given to the concept of a modular and interoperable software stack, in which different tools address complementary aspects of the radar processing chain while sharing common data structures. This overview provides a conceptual framework that guides all subsequent practical exercises.

Following the overview, participants receive a concise introduction to weather radar measurements and the full processing chain, including common sources of uncertainty and error. Morning sessions focus on data ingestion and exploration, emphasizing modern access patterns using xradar to handle multiple radar formats consistently within an xarray-based workflow. Practical exercises are conducted in Jupyter notebooks,
allowing participants to explore and adapt processing steps in real time.

A central component of the morning is dedicated to the full processing chain of quality control, essential corrections, and transformations. 
Participants will identify and mitigate non-meteorological signals, including ground clutter and noise, and apply standard filtering and masking techniques.  Participants apply attenuation correction, consider calibration issues, and examine reflectivity–rainfall relationships. The course then guides participants through transforming polar radar data into Cartesian grids and generating key gridded products, such as constant-altitude plan position indicators and composite fields, illustrating the interactions between xradar, Py-ART, and wradlib.  In the final practical session, participants derive precipitation products, including instantaneous rain rates and accumulated fields, and export these in standard formats such as NetCDF, Zarr or others.


After a lunch break, afternoon sessions offer individual projects:
* In depth exploration of selected steps from the morning session, to provide insight into the underlying algorithms and enable participants to modify or extend them as needed.
* A dedicated session focuses on the integration of established radar processing frameworks into modern workflows. Systems such as BALTRAD and LROSE (TITAN / SAMURAI)  are introduced, demonstrating how their capabilities can complement Python-based tools and be incorporated into xarray-based pipelines. This session bridges research-oriented workflows with operational processing environments, providing participants with a broader perspective on the radar ecosystem.
* A special session on Echo Top Height Analysis to identify storm structure, vertical extents, and derived products.

Exercises emphasize transparency and reproducibility, enabling participants to not only generate analysis-ready datasets but also to understand and adapt the processing workflows. The course concludes with a discussion of how these outputs can be used in precipitation nowcasting, providing a direct link to the second day of the training sequence.

By the end of the day, participants will have completed a full radar processing workflow, gained hands-on experience with interoperable open-source tools, and acquired the skills needed to design, modify, and apply radar processing pipelines for both research and operational purposes.

## Software and Tools

All exercises will be based on open-source software within the Python ecosystem, in particular xradar, Py-ART, wradlib, xarray, and dask. The course will explicitly demonstrate how these tools can be combined into coherent and reproducible workflows, while also interfacing with external systems such as BALTRAD and LROSE.

## Data and Case Studies

The course is based on one to two carefully selected radar cases representing different precipitation regimes, for example convective and stratiform events. These datasets are used consistently throughout the course and serve as input for the subsequent nowcasting course.

## Expected Outcomes

At the end of the course, participants will have a practical understanding of the main steps involved in radar data processing and will be able to apply standard methods for quality control, correction, and gridding. They will have produced analysis-ready precipitation datasets and will be familiar with modern, interoperable workflows based on the open radar science ecosystem.

## Course Materials

All teaching materials are made openly available. This includes interactive notebooks, example datasets, instructions for data access, and supporting documentation. Where appropriate, additional material for further exploration is provided. Background material and pre-course reading material and exercises include:
1. [Background Material](presentations/intro-to-open-radar-science.md)
2. [Getting Started](getting_started.md)
3. [Data Access](notebooks/xradar/xradar-basics.md)
4. [Specific Data Access](notebooks/data-access/intro-data-access.md)

## Requirements

Participants are expected to bring a laptop with a modern web browser. 
Instructions for installing the required software environment can be found in [getting started](getting_started.md). For the course we will work via a cloud-based solution. Information will be provided soon.

## Relation to Other ERAD Activities

The course forms the first part of a coordinated two-day training activity. The second course will focus on open-source approaches to precipitation nowcasting and will directly build on the datasets and workflows developed during this session.

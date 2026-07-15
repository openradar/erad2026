# BinderHub entry point (binder.projectpythia.org): pulls the prebuilt course
# image instead of building the environment (BALTRAD/LROSE cannot be compiled
# on the fly there — binder/appendix.txt is a repo2docker CLI-only feature).
#
# Bump the pinned tag after every environment change, once the Build Image
# workflow has pushed the new image. The workflow itself ignores this file
# (it removes it before running repo2docker), so images are always rebuilt
# from environment.yml + appendix.txt.
FROM ghcr.io/openradar/erad2026:d3da0545aef0

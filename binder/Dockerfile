# BinderHub entry point (binder.projectpythia.org): pulls the prebuilt course
# image instead of building the environment.
#
# The PR author must update the pinned tag after changing the environment.
# The Build Image workflow reads this tag and publishes the corresponding image.
#
# Note the image also bakes in the repository contents, so it goes stale when
# notebooks change even though the environment has not. Build Image only fires on
# binder/**, install/** and its own workflow file, so a notebook-only PR never
# refreshes it -- bump this pin and re-run Build Image to pick those up.
#
FROM ghcr.io/openradar/erad2026:pr-62

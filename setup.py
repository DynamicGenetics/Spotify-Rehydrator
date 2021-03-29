import setuptools

with open("README.rst", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="spotifyrehydrator",
    version="0.1.0",
    author="Nina Di Cara",
    author_email="ninadicara@gmail.com",
    description="A convenience package for creating datasets of track features from self-requested Spotify data.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://github.com/DynamicGenetics/Spotify-Rehydrator",
    project_urls={
        "Bug Tracker": "https://github.com/DynamicGenetics/Spotify-Rehydrator/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        "spotipy >= 2.16",  # https://github.com/plamere/spotipy
        "alive_progress>=1.6",  # https://github.com/rsalmei/alive-progress
        "pandas>=1.2",  # https://github.com/pandas-dev/pandas
        "simplejson>=3.17",  # https://github.com/simplejson/simplejson
    ],
)

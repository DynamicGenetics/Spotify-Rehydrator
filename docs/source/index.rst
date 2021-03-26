Welcome to the Spotify Rehydrator!
==============================================

.. toctree::
    :maxdepth: 2

The *Spotify Rehydrator* was created to provide a simple way to generate full datasets of track features from user-owned Spotify data.
It relies on the excellent `Spotipy <https://github.com/plamere/spotipy/>`_ library and brings together a series of API calls in a convenient way that can manage data from
multiple different people, as would be common in a research study. It can also be used by individuals who are curious to learn more about
their own data! The idea of a rehydrator was inspired by similar work being done to enable sharing of Twitter datasets for research purposes. 

Before you use the rehyrdator, please make sure to read the Disclaimers to get an understanding of the limitations of the search strategy used. 

Getting Started
================
To use the rehydrator you will need two things:
1. Some data to rehydrate. 
2. Spotify Developer credentials

Requesting data
---------------
This package is designed to work with the files named `StreamingHistory.json` that are
sent to users as part of their data package if they `request their own Spotify data <https://support.spotify.com/us/article/data-rights-and-privacy-settings/>`_. 

This data should be in one or more files with a list of JSON objects that look like this::

    {
    "endTime" : "2019-01-19 17:01",
    "artistName" : "An Artist",
    "trackName" : "A Track Name",
    "msPlayed" : 19807
    }


Developer credentials
---------------------
To request developer credentials go to `Spotify's developer portal <https://developer.spotify.com/dashboard/>`_. You will need to 'create an app', which you can
then request credentials against. This will give you a ``Client ID`` and a ``Client Secret``. 

Using the rehydrator
=====================
The *Spotify Rehydrator* primarily operates through the ``Rehydrator`` class. The required inputs for this class are an input folder, an output folder and a `ClientCredentials <>`_ 
object, which is used by `Spotipy` for authenticating the API calls. You can then call the ``run()`` method.

Assuming you have saved your Client ID and Client Secret as environment variables then this is an example of how you could run the Rehydrator::
    
    from spotify-rehydrator import Rehydrator
    from spotipy.oauth2 import SpotifyClientCredentials

    auth = SpotifyClientCredentials(
        client_id=CLIENT_ID, 
        client_secret=CLIENT_SECRET
        )

    Rehydrator(
        input_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "input"),
        output_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "output"),
        sp_creds=auth,
    ).run()


Disclaimers
================


Code Documentation
===================

.. automodule:: rehydrate
    :members:


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

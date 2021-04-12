Welcome to the Spotify Rehydrator!
==============================================

.. toctree::
    :maxdepth: 2

The *Spotify Rehydrator* was created to provide a simple way to generate full datasets of track features from user-owned Spotify data.
It relies on the excellent `Spotipy <https://github.com/plamere/spotipy/>`_ library and brings together a series of API calls in a convenient way that can manage data from
multiple different people, as would be common in a research study. It can also be used by individuals who are curious to learn more about
their own data! The idea of a rehydrator was inspired by similar work being done to enable sharing of Twitter datasets for research purposes. 

Before you use the rehyrdator, please make sure to read the Disclaimers to get an understanding of the limitations of the search strategy used. 

User Guide
=====================
The *Spotify Rehydrator* primarily operates through the ``Rehydrator`` class. The required inputs for this class are an input folder,
an output folder and a Client ID and Client Secret from the Spotify Developer Portal. These are used for authenticating the API calls. You can then call the ``run()`` method.

.. note::  To request developer credentials go to `Spotify's developer portal <https://developer.spotify.com/dashboard/>`_.
            You will need to 'create an app' which have credentials associated with it.
            Your app dashboard will give you access to your ``Client ID`` and a ``Client Secret``. 

Assuming you have set your Client ID and Client Secret as environment variables then this is an example of how you could run the Rehydrator::
    
    import os
    from spotifyrehydrator import Rehydrator

    Rehydrator(
        input_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "input"),
        output_path=os.path.join(pathlib.Path(__file__).parent.absolute(), "output"),
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    ).run(return_all=True)


The ``.run()`` argument will by default return the following information as columns: spotify track ID of the returned track, the name of the artist of the returned track,
the name of the returned track. This will be joined with the searched artist and track, the person ID where relevant, and the time metadata in the original ``.json`` file.
There are then three optional arguments:  
* ``artist_info = True`` will return the popularity of the artist returned and a list of genres attributed to that artist, provided by `the Artists API endpoint <https://developer.spotify.com/documentation/web-api/reference/#category-artists>`_
* ``audio_features = True`` will return a column for each of the audio features provided by the `Tracks API. <https://developer.spotify.com/documentation/web-api/reference/#category-tracks>`_
* ``return_all = True`` will return both the above. 

Be aware that extra arguments involve more API calls and so may take longer. 


Expected formats
------------------

Streaming History JSON
^^^^^^^^^^^^^^^^^^^^^^
This package is designed to work with the files named `StreamingHistory.json` that are
sent to users as part of their data package if they
`request their own Spotify data <https://support.spotify.com/us/article/data-rights-and-privacy-settings/>`_. 
The file will contain up to the past year of the user's listening data.

This data should be in one or more files with a list of JSON objects that look like this::

    {
    "endTime" : "2019-01-19 17:01",
    "artistName" : "An Artist",
    "trackName" : "A Track Name",
    "msPlayed" : 19807
    }


Input folder
^^^^^^^^^^^^^
The input folder should contain a series of Streaming History JSON files. 
If you have files belonging to multiple individuals then the package expects the
unique identifier for each person to be the prefix, followed by an underscore. For example::

    # input folder
    person001_StreamingHistory0.json
    person001_StreamingHistory1.json
    person002_StreamingHistory0.json

This would result in two rehydrated files being saved to the output folder::

    # output folder
    person001-rehydrated.tsv
    person002-rehydrated.tsv

You could also input several files without any underscores to represent individuals. These
would all be combined and saved in one output file. 

Useful information
--------------------
* If the output directory does not exist then it will be created. 
* Rehydration for one individual can take 15 minutes or more depending on how many songs there are.
* If a file for the next individual's data to be rehydrated already exists in the output directory then that person will be skipped. You will need to delete or remove their file from the output folder for the rehydrator to process their data. 

Disclaimers
================
* Not all tracks can be retreived from the API. In our experience about 5% of tracks cannot be found on the API. These will have a value of NONE in the output files. 
* There is not a guaranteed match between the first returned item in a search and the track you want. Comparing msPlayed with the track length is a good way to test this since msPlayed should not exceed the track length. 

Code Documentation
===================

.. automodule:: utils
    :members:


Contributing
=============
Contributions to the package are very welcome! 

If you would like to add a new feature then 

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

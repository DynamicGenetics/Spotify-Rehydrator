.. image:: https://github.com/DynamicGenetics/Spotify-Rehydrator/blob/main/docs/image.png?raw=true
  :width: 400
  :alt: Spotify Rehydrator


.. |GPLv3 license| image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: http://perso.crans.org/besson/LICENSE.html


Recreate a full dataset of audio features of songs downloaded through Spotify's
`download my data <https://support.spotify.com/us/article/data-rights-and-privacy-settings/>`_ facility.  

This requires the files named ``StreamingHistory{n}.json`` where ``{n}`` represents the file number that starts at 0, and goes up to however many files were retrieved.  


Quick start
==============
Extended documentation is `available on ReadTheDocs <https://spotify-rehydrator.readthedocs.io>`_. An example of using the package to rehydrate a folder of json files is::
  
  # main.py
  from spotifyrehydrator import Rehydrator
  import os
  import pathlib

  if __name__ == "__main__":
      Rehydrator(
          os.path.join(pathlib.Path(__file__).parent.absolute(), "input"),
          os.path.join(pathlib.Path(__file__).parent.absolute(), "output"),
          client_id=os.getenv("SPOTIFY_CLIENT_ID"),
          client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
      ).run(return_all=True)


Run takes boolean arguments for ``audio_features`` and ``artist info``, or for ``return_all`` which then returns both. These will determine how much information is retrieved to make up
the full dataset that is saved into the output folder. 

How it works
=============
#. The files for each person are read from the specified input folder.  
#. The name and artist provided are searched with the Spotify API. The first result is taken to be the track, and the track ID is recorded.   
#. Additional information is searched on other endpoints if ``audio_features``, ``artist info`` or ``return_all`` were set to ``True``.
#. The matched track ID and audio features are saved as one **tab delimited** ``.tsv`` file per person into the specified output folder. 

Good to know
===============
* Not all tracks can be retreived from the API. In our experience about 5% of tracks cannot be found on the API. These will have a value of NONE in the output files. 
* There is not a guaranteed match between the first returned item in a search and the track you want. Comparing msPlayed with the track length is a good way to test this since msPlayed should not exceed the track length. 


P.S. Thanks to `Pixel perfect <https://www.flaticon.com/authors/pixel-perfect>`_ for the title `icon <https://www.flaticon.com/>`_. 🙂 

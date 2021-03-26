.. image:: https://github.com/DynamicGenetics/Spotify-Rehydrator/blob/main/docs/image.png?raw=true
  :width: 450
  :alt: Spotify Rehydrator


.. |GPLv3 license| image:: https://img.shields.io/badge/License-GPLv3-blue.svg
   :target: http://perso.crans.org/besson/LICENSE.html


Recreate a full dataset of audio features of songs downloaded through Spotify's 'download my data' facility.  
This requires the files named `StreamingHistory{n}.json` where {n} represents the file number that starts at 0, and goes up to however many files were retrieved.   

How it works
=============
#. The files for each person are read to a single dataframe from the `/input` folder.  
#. The name and artist provided are searched with the Spotify API. The first result is taken to be the track, and the track ID is recorded.   
#. The trackIDs are then searched on the `get_audio_features` `API endpoint <https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-audio-features-for-several-tracks>`_. 
#. The matched track ID and audio features are saved as one **tab delimited** `.csv` file per person into the `/output` folder. 

Good to know
===============
* Not all tracks can be retreived from the API. In our experience about 5% of tracks cannot be found on the API. These will have a value of NONE in the output files. 
* There is not a guaranteed match between the first returned item in a search and the track you want. Comparing msPlayed with the track length is a good way to test this since msPlayed should not exceed the track length. 
* This programme is optimised for British users. If you are running it elsewhere you may want to try changing the 'market' argument in the function `get_URIs` in `functions.py`. More information about this is `available in Spotify's documentation <https://developer.spotify.com/documentation/web-api/reference/#endpoint-search>`_. 


P.S. Thanks to `Pixel perfect <https://www.flaticon.com/authors/pixel-perfect>`_ for the title `icon <https://www.flaticon.com/>`_. 🙂 

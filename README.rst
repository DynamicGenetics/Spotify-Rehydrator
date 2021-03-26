<img src="https://github.com/DynamicGenetics/Spotify-Rehydrator/blob/main/docs/image.png?raw=true" width="500px" alt="Spotify Rehydrator">

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


Recreate a full dataset of audio features of songs downloaded through Spotify's 'download my data' facility.  
This requires the files named `StreamingHistory{n}.json` where {n} represents the file number that starts at 0, and goes up to however many files were retrieved.   

The code can be used as it is, or can be altered to suit your requirements with some minor changes. For instance, making a different query on the trackIDs.  

## How to use it
1. Download this repository to your computer.  
2. Put all of your `StreamingHistory.json` files in the sub-folder `input`. If these files are from multiple people and you want each of their files labelled then make sure each file has a unique ID for each person as the prefix, separated by an underscore. E.G. `person001_StreamingHistory0.json`, `person001_StreamingHistory1.json` etc.   
3. Put your Spotify Developer credentials in a file called `secrets.py` file, in the top level of the repository.  A template is provided in [`secrets-example.py`](https://github.com/DynamicGenetics/Spotify-Rehydrator/blob/main/docs/secrets-example.py)
4. Run the `rehydrate.py` file.  

## How it works
1. The files for each person are read to a single dataframe from the `/input` folder.  
2. The name and artist provided are searched with the Spotify API. The first result is taken to be the track, and the track ID is recorded.   
3. The trackIDs are then searched on the [`get_audio_features` API endpoint](https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-audio-features-for-several-tracks). 
4. The matched track ID and audio features are saved as one **tab delimited** `.csv` file per person into the `/output` folder. 

Intermediate files are saved along the way in the `/temp/` folder. This means that if you have a lot of files to process and the programme shuts down for any reason (laptop goes to sleep etc) then
you can start the script again and it will pick up where it left off. You can delete the temp folder when you're finished.  

## Good to know
- Not all tracks can be retreived from the API. In our experience about 5% of tracks cannot be found on the API. These will have a value of NONE in the output files. 
- There is not a guaranteed match between the first returned item in a search and the track you want. Comparing msPlayed with the track length is a good way to test this since msPlayed should not exceed the track length. 
- This programme is optimised for British users. If you are running it elsewhere you may want to try changing the 'market' argument in the function `get_URIs` in `functions.py`. More information about this is [available in Spotify's documentation](https://developer.spotify.com/documentation/web-api/reference/#endpoint-search). 


P.S. Thanks to [Pixel perfect](https://www.flaticon.com/authors/pixel-perfect) for the title [icon](https://www.flaticon.com/). 🙂 
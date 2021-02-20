![Spotify Rehydrator Logo](https://github.com/DynamicGenetics/Spotify-Rehydrator/blob/main/docs/image.png?raw=true)

This application allows you to get audio features of songs downloaded through Spotify's 'download my data' facility.  
It requires the files named `StreamingHistory{n}.json` where {n} represents the file number that starts at 0, and goes up to however many files were retrieved.   

This repository can be used as it is, or can be altered to suit your personal requirements with some minor changes. For instance, making a different query on the trackIDs.  

## How to use it
1. Download this repository to your computer.  
2. Put all of your `StreamingHistory.json` files in the sub-folder `input`. If these files are from multiple people and you want each of their files labelled then make sure each file has the participants' unique ID as the prefix, separated by an underscore. E.G. `participantID_StreamHistory.json`.   
3. Put your Spotify Developer credentials in the `secrets.py` file.  
4. Run the `rehydrate.py` file.  

## How it works
1. The files for each person are read to a single dataframe from the `/input` folder.  
2. The name and artist provided are searched with the Spotify API. The first result is taken to be the track, and the track ID is recorded.   
3. The trackIDs are then searched on the [`get_audio_features` API endpoint](https://developer.spotify.com/documentation/web-api/reference/#endpoint-get-audio-features-for-several-tracks). 
4. The matched track ID and audio features are saved as one **tab delimited** `.csv` file per person into the `/output` folder. 

Intermediate files are saved along the way in the `/temp/` folder. This means that if you have a lot of files to process and the programme shuts down for any reason (laptop goes to sleep etc) then
you can start the script again and it will pick up where it left off. You can delete the temp folder when you're finished.  

## Good to know
- Not all trackIDs can be retreived. In our experience about 5% of tracks cannot be found on the API. These will have a value of NONE in the output files.  
- This programme is optimised for British listeners. If you are running it elsewhere you may want to try changing the 'market' argument in the function `get_URIs` in `functions.py`. More information about this is [available in Spotify's documentation](https://developer.spotify.com/documentation/web-api/reference/#endpoint-search). 

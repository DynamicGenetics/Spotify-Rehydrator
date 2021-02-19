# Spotify Rehydrator

This application allows you to get audio features of songs downloaded through Spotify's 'download my data' facility. 
It requires the files named `StreamingHistory{n}.json` where {n} represents the file number that starts at 0, and goes up to however many files were retrieved.   

This repository can be used as it is, or can be altered to suit your personal requirements with some minor changes. For instance, making a different query on the trackIDs. 

## How to use it

1. Download this repository to your computer. 
2. Put all of your `StreamingHistory.json` files in the sub-folder `input`. If these files are from multiple people and you want each of their files labelled then make sure each file has the participants' unique ID as the prefix, separated by an underscore. E.G. `participantID_StreamHistory.json`. 
3. Put your Spotify Developer credentials in the `secrets.py` file.
4. Run `rehydrate.py`.

## How it works
1. The files for each person are read to a single dataframe from the `/input` folder.  
2. The name and artist provided are searched with the Spotify API. The first result is taken to be the track, and the track ID is recorded.  
3. The matched track ID and information about each listening event are saved as one file per person into the `/matched` folder.  

Depending on the number of unique tracks, a single person's data could take 10-30 minutes to process.  

The final output is a file called `track_features.csv` which is a **tab delimited** file, saved to the `output` folder. 

## Guide to the output
The files will be 



## Trouble Shooting
It takes a while to run. 

Market location. 

Not all track IDs are found. 
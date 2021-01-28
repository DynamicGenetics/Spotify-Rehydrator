# Spotify Rehydrator

This application allows you to get audio features of songs downloaded through Spotify's 'download my data' facility. 
It requires the files named `StreamingHistory{n}.json` where {n} represents the file number that starts at 0, and goes up to however many files were retrieved.   

If there are multiple peoples' data then each set of files needs to be prefixed by a unique code or name, and then an underscore. For instance:  
```
participant001_StreamingHistory0.json
```
This ensures that data from the same person is labelled and grouped appropriately.  

## How does it work? 
1. The files for each person are read to a single dataframe from the `/input` folder.  
2. The name and artist provided are searched with the Spotify API. The first result is taken to be the track, and the track ID is recorded.  
3. The matched track ID and information about each listening event are saved as one file per person into the `/matched` folder.  

Depending on the number of unique tracks, a single person's data could take 10-30 minutes to process.  

The final output is a file called `track_features.csv` which is a **tab delimited** file, saved to the `output` folder. 
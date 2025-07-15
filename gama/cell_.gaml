/**
* Name: grid
* Based on the internal empty template. 
* Author: ashfa
* Tags: 
*/



model cell_



grid cell width:50 height:50 neighbors: 8 {
	int robot_vision_range <- 3;
    int robot_speech_range <- 3;
    
    list<cell> neighbors_at_robot_vision update: (self neighbors_at (robot_vision_range));
    list<cell> neighbors_at_robot_speech update: (self neighbors_at (robot_speech_range));
       
    aspect default {
        draw string(string(index)) color: #black anchor: #center font: font(3); 
    }
}